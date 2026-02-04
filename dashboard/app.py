# app landing page

import streamlit as st

# page configuration
# relates to files in pages/
# on this project: pages/1_🌸_Phenology_Analysis.py
st.set_page_config(page_title="Phenology Data Dashboard",
                   page_icon="🌸",
                   layout="wide")

# if we had more pages, we could add a sidebar navigation here
# e.g., if we had pages/2_📊_Another_Page.py
#st.set_page_config(page_title="Another Dashboard",
#                   page_icon="📊",
#                   layout="wide")


st.title("🌸 Dashboard Project Collection")
st.write("Use the navigation in the sidebar.")

st.markdown("""
### Available Pages:

- 🌸 Flowering Phenology - Interactive map and chart with flowering observation data
""")
