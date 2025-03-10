#Visualising Mpox Cases: 

import pandas as pd 
import geopandas as gpd
import folium

#load Data 
df = pd.read_csv("Mpox_cases.csv")

#selecting only the columns we need: 
df = df[['iso3', 'total_confirmed_cases']] 

#Loading worldmap shapefile 
 #world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
world = gpd.read_file("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson")

# Merge with Mpox data on ISO3 country codes
merged = world.merge(df, left_on="iso_a3", right_on="iso3", how="left")

# Create a Folium map
m = folium.Map(location=[0, 20], zoom_start=2)

#Add Choropleth layer
folium.Choropleth(
    geo_data=merged,
    name="choropleth",
    data=merged,
    columns=["iso3", "total_confirmed_cases"],
    key_on="feature.properties.iso_a3",
    fill_color="YlOrRd",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Mpox Cases"
).add_to(m)

# Save and display
m.save("mpox_map.html")
print("Map saved as 'mpox_map.html'. Open in a browser to view.")