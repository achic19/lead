import geopandas as gpd
import osmnx as ox

# code to show how the osm become graph with and without simplifcation
area_path = r'inputs\test.shp'
area = gpd.read_file(area_path)
area = area['geometry'][0]

graph = ox.graph_from_polygon(area, network_type='all', simplify=False)
gdf_format = ox.graph_to_gdfs(graph)

pnt_shp = gdf_format[0].loc[:, ['geometry']]
edges_shp = gdf_format[1].loc[:, ['geometry']]

pnt_shp.to_file('for_figures/all_pnt.shp')
edges_shp.to_file('for_figures/all.shp')

graph = ox.graph_from_polygon(area, network_type='walk', simplify=False)
gdf_format = ox.graph_to_gdfs(graph)

pnt_shp = gdf_format[0].loc[:, ['geometry']]
edges_shp = gdf_format[1].loc[:, ['geometry']]

pnt_shp.to_file('for_figures/no_simpl_pnt.shp')
edges_shp.to_file('for_figures/no_simpl.shp')

graph = ox.graph_from_polygon(area, network_type='walk')
gdf_format = ox.graph_to_gdfs(graph)

pnt_shp = gdf_format[0].loc[:, ['geometry']]
edges_shp = gdf_format[1].loc[:, ['geometry']]

pnt_shp.to_file('for_figures/final_pnt.shp')
edges_shp.to_file('for_figures/final.shp')

# graph = ox.graph_from_place(area, network_type='walk',simplify=False)
# gdf_format = ox.graph_to_gdfs(graph)
# nx.write_shp(graph ,'/for_figures')
# graph = ox.graph_from_place(area,simplify=False)
# gdf_format = ox.graph_to_gdfs(graph)
# nx.write_shp(graph ,'/for_figures')
