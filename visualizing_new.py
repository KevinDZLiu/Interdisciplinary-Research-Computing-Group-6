import pandas as pd

# Load the CSV file
data = pd.read_csv("Mpox_cases_Julia.csv")
data['week_end_date'] = pd.to_datetime(data['week_end_date'])
latest_data = data.loc[data.groupby('country')['week_end_date'].idxmax()]
heatmap_data = latest_data[['country', 'total_confirmed_cases']]
print(data.head())

# Group by country and sum the total confirmed cases
#heatmap_data = data.groupby('country')['total_confirmed_cases'].sum().reset_index()
print(heatmap_data)

#plotting the heatmap
import geopandas as gpd
import matplotlib.pyplot as plt

# Load a world shapefile (included with Geopandas)
#world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
world = gpd.read_file(r"ne_110m_admin_0_countries")
print(world.head())  # Verify the data loaded correctly

# Create a list of African countries
african_countries = [
    'Algeria', 'Angola', 'Benin', 'Botswana', 'Burkina Faso', 'Burundi', 'Cabo Verde', 'Cameroon', 'Central African Republic', 'Chad', 'Comoros', 'Republic of the Congo','Democratic Republic of the Congo', 'Djibouti', 'Egypt', 'Equatorial Guinea', 'Eritrea', 'Eswatini', 'Ethiopia', 'Gabon', 'Gambia', 'Ghana', 'Guinea', 'Guinea-Bissau', 'Ivory Coast', 'Kenya', 'Lesotho', 'Liberia', 'Libya', 'Madagascar', 'Malawi', 'Mali', 'Mauritania', 'Mauritius', 'Morocco', 'Mozambique', 'Namibia', 'Niger', 'Nigeria', 'Sao Tome and Principe', 'Senegal', 'Seychelles', 'Sierra Leone', 'Somalia', 'South Africa', 'South Sudan', 'Sudan', 'Rwanda', 'Togo', 'Tunisia','United Republic of Tanzania','Uganda', 'Zambia', 'Zimbabwe', 'Western Sahara']

africa = world[world['ADMIN'].isin(african_countries)]
print(africa.head())


#filter for African countries 
#africa = world[world['continent'] == 'Africa']

#verify column names
print(world.columns)
print(heatmap_data.columns)

# Merge with heatmap data
africa = africa.rename(columns={'ADMIN': 'country'})
africa = africa.merge(heatmap_data, on='country', how='left')

# Plot the heatmap
fig, ax = plt.subplots(1, 1, figsize=(15, 10))
africa.boundary.plot(ax=ax, linewidth=1)
africa.plot(column='total_confirmed_cases', ax=ax, legend=True, cmap='YlOrRd', legend_kwds={'label': "Confirmed Cases"})
ax.set_xticks([])
ax.set_yticks([])
plt.title("Mpox Cases Heatmap in Africa")
plt.show()
