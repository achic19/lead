import os

import geopandas as gpd

london_shp = gpd.GeoDataFrame(crs='epsg:3857')

for folder in os.listdir('output'):
    print(folder)
    if folder == 'general_output':
        continue
    temp_path = os.path.join('output', folder, folder + '.shp')
    temp_pd = gpd.read_file(temp_path)
    london_shp = london_shp.append(temp_pd)
    print(london_shp.shape[0])

london_shp.to_file('output\general_output\london.shp')
