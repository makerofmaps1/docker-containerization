# basic flowing phenology analysis dashboard
# shows map of observations and bar chart of counts by month/year

import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
from sqlalchemy import select, text, func
import streamlit as st

from models import FlowerObservation, Base
from db import get_engine
from load_data import resolve_data_file, load_phenology_data

st.set_page_config(page_title="Phenology Analysis", layout="wide")
st.title("🌸 Flowering Phenology Data")

# cache the database connection
# so we can create it once and reuse it
@st.cache_resource
def get_db():
    return get_engine()

# check if data exists in database
@st.cache_data(ttl=10)
def check_data_exists(_engine):
    try:
        with _engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM flower_observations")).scalar()
            return result > 0, result
    except Exception:
        return False, 0

# similarly, cache the data so we load once and reuse
# again, small data set so caching is fine
@st.cache_data(ttl=600)
def load_data(_engine):
    query = (
        select(
            FlowerObservation.photo_id,
            FlowerObservation.year,
            FlowerObservation.observation_date,
            FlowerObservation.latitude,
            FlowerObservation.longitude,
            FlowerObservation.genus_species,
            FlowerObservation.family,
        )
        .order_by(FlowerObservation.observation_date)
    )
    return pd.read_sql(query, _engine)

# load data and do basic pandas data type conversions
engine = get_db()

# Initialize session state for auto-reset
if 'auto_reset' not in st.session_state:
    st.session_state.auto_reset = False

# Check if auto-reset is enabled and data exists
if st.session_state.get('auto_reset', False):
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM flower_observations")).scalar()
            if result > 0:
                with engine.connect() as conn:
                    conn.execute(text("DROP TABLE IF EXISTS flower_observations CASCADE"))
                    conn.commit()
                st.cache_data.clear()
    except Exception:
        pass  # Table doesn't exist yet

data_exists, record_count = check_data_exists(engine)

# Show data loading section if no data exists
if not data_exists:
    st.info("📦 **Demo: Data Pipeline Architecture**")
    
    st.markdown("""
    This application demonstrates a cloud data pipeline:
    
    1. **Source (S3)**: Raw Excel file stored in AWS S3 bucket
    2. **Database (RDS)**: PostgreSQL with PostGIS extensions (accessed via SSH tunnel through EC2)
    3. **Application (Streamlit)**: Interactive visualization dashboard
    
    Click the button below to trigger the data loading process. This will:
    - Download the phenology data from S3
    - Create the database schema (if needed)
    - Load observations into the RDS database through the SSH tunnel
    - Display the interactive dashboard
    """)
    
    if st.button("🚀 Load Data from S3 to Database", type="primary"):
        with st.spinner("Loading data from S3 to database..."):
            progress_text = st.empty()
            
            try:
                progress_text.info("📡 Connecting to database...")
                
                # Create extensions and schema
                with engine.begin() as conn:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis_topology"))
                
                Base.metadata.create_all(engine)
                progress_text.info("✅ Database schema created")
                
                progress_text.info("📥 Downloading data from S3...")
                load_phenology_data(engine)
                
                progress_text.success("✅ Data successfully loaded! Refreshing app...")
                
                # Clear caches and rerun
                st.cache_data.clear()
                st.rerun()
                
            except Exception as e:
                progress_text.error(f"❌ Error loading data: {str(e)}")
                st.exception(e)
    
    st.stop()

# Display record count and reset button
st.sidebar.success(f"📊 Database: {record_count:,} observations")

# Add reset button for demo purposes
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔄 Demo Controls")

# Auto-reset toggle
st.session_state.auto_reset = st.sidebar.checkbox(
    "🔁 Auto-reset on page refresh",
    value=st.session_state.get('auto_reset', False),
    help="Automatically clear the database each time you refresh the page"
)

if st.sidebar.button("🗑️ Reset Demo (Clear Database)", type="secondary"):
    with st.spinner("Clearing database..."):
        try:
            with engine.connect() as conn:
                conn.execute(text("DROP TABLE IF EXISTS flower_observations CASCADE"))
                conn.commit()
            st.sidebar.success("✅ Database cleared!")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Error clearing database: {str(e)}")

df = load_data(engine)

if df.empty:
    st.warning("No data found in database. Please load data using the button above.")
    st.stop()

df['observation_date'] = pd.to_datetime(df['observation_date'])
df['month'] = df['observation_date'].dt.month

# Cascading filters: Family -> Species
st.sidebar.header("Filters")

# make list of available families
families = ['All'] + sorted(df['family'].dropna().unique().tolist())
selected_family = st.sidebar.selectbox("Family", families)

# Filter for family to get available species
temp_df = df.copy()
if selected_family != 'All':
    temp_df = temp_df[temp_df['family'] == selected_family]

species_list = ['All'] + sorted(temp_df['genus_species'].unique().tolist())
selected_species = st.sidebar.selectbox("Species", species_list)

# make filtered dataframe based on selections
filtered = df.copy()
if selected_family != 'All':
    filtered = filtered[filtered['family'] == selected_family]
if selected_species != 'All':
    filtered = filtered[filtered['genus_species'] == selected_species]

st.sidebar.write(f"**Showing {len(filtered)} observations**")

# Color map for years (shared between map and chart)
years = sorted(filtered['year'].unique())
colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#c0392b', '#e67e22', '#f1c40f', '#1abc9c', '#34495e']
year_colors = {year: colors[i % len(colors)] for i, year in enumerate(years)}

# will put our visuals in columns
col1, col2 = st.columns(2)

# left column: map
with col1:
    st.subheader("📍 Locations")

    if not filtered.empty:

        # Create map with zoomed initial extent
        # specifying manually here because we want a fixed initial/default extent
        center_lat = (34.73279680287924 + 34.748334732195495) / 2
        center_lon = (-82.87792143985396 + -82.84638166909697) / 2

        # declare map
        m = folium.Map(location=[center_lat, center_lon], zoom_start=15)

        # populate the map with points data
        for _, row in filtered.iterrows():
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=2,
                popup=f"{row['genus_species']}<br>{row['observation_date']}<br>Year: {row['year']}",
                color=year_colors[row['year']],
                fill=True,
                fillOpacity=0.6
            ).add_to(m)

        # Add legend
        legend_html = '<div style="position: fixed; bottom: 50px; left: 50px; z-index:9999; background-color:white; padding:10px; border:2px solid grey; border-radius:5px">'
        legend_html += '<p style="margin:0; font-weight:bold;">Year</p>'
        for year in years:
            legend_html += f'<p style="margin:0;"><span style="color:{year_colors[year]};">●</span> {year}</p>'
        legend_html += '</div>'

        # display map
        st_folium(m, width=450, height=500, returned_objects=[])
        st.markdown(legend_html, unsafe_allow_html=True)

# right column: chart
with col2:
    st.subheader("📊 Counts by Year and Month")

    # Count by month and year
    monthly_counts = filtered.groupby(['month', 'year']).size().reset_index(name='count')

    # Convert year to string for categorical treatment
    monthly_counts['year'] = monthly_counts['year'].astype(str)

    # Create complete month range for all years
    all_years = sorted(filtered['year'].unique())
    all_months = pd.DataFrame({
        'month': range(1, 13),
        'month_name': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    })

    # Create df with complete combination of months and years
    complete_data = []
    for year in all_years:
        for month in range(1, 13):
            complete_data.append({'month': month, 'year': str(year)})
    complete_df = pd.DataFrame(complete_data)

    # left join actual counts to complete_df made above
    monthly_counts = complete_df.merge(monthly_counts, on=['month', 'year'], how='left')
    monthly_counts['count'] = monthly_counts['count'].fillna(0).astype(int)

    # Add month names
    monthly_counts = monthly_counts.merge(all_months, on='month', how='left')

    # Create bar chart with year as color using same colors as map
    fig = px.bar(
        monthly_counts,
        x='month_name',
        y='count',
        color='year',
        barmode='group',
        labels={'month_name': 'Month', 'count': 'Number of Observations', 'year': 'Year'},
        title=f'Total Observations: {len(filtered)}',
        color_discrete_map={str(year): year_colors[year] for year in years}
    )

    # display
    st.plotly_chart(fig, use_container_width=True)

# Citation
st.markdown("---")
st.markdown("### Data Citation")
st.markdown("""
M. Cope, E. Mikhailova, C. Post, M. Schlautman, P. McMillan,  
Developing an integrated cloud-based spatial-temporal system for monitoring phenology,  
*Ecological Informatics*, Volume 39, 2017, Pages 123-129, ISSN 1574-9541,  
[https://doi.org/10.1016/j.ecoinf.2017.04.007](https://doi.org/10.1016/j.ecoinf.2017.04.007)
""")
