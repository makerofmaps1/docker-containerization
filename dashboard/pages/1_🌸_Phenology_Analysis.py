# basic flowing phenology analysis dashboard
# shows map of observations and bar chart of counts by month/year

import os
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
from sqlalchemy import create_engine
import streamlit as st

st.set_page_config(page_title="Phenology Analysis", layout="wide")
st.title("🌸 Flowering Phenology Data")

# cache the database connection
# so we can create it once and reuse it
@st.cache_resource
def get_db():
    db_host = os.getenv('DB_HOST', 'database')
    connection_string = f'postgresql://postgres:postgres@{db_host}:5432/environmental_data'
    return create_engine(connection_string)

# similarly, cache the data so we load once and reuse
# again, small data set so caching is fine
@st.cache_data(ttl=600)
def load_data(_engine):
    query = """
            SELECT photo_id, year, observation_date, latitude, longitude,
                   genus_species, family
            FROM flower_observations
            ORDER BY observation_date;
            """
    return pd.read_sql(query, _engine)

# load data and do basic pandas data type conversions
engine = get_db()
df = load_data(engine)
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
