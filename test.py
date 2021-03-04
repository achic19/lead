import time
from multiprocessing import Pool

import geopandas as gpd
import networkx as nx
import numpy as np
from shapely.geometry import Point


# 01.10.2020
class CalcRoutes:
    def __init__(self, path, path_pnt):
        # Dataframe to save all the necessary information
        self.from_to_route_cost = gpd.GeoDataFrame(
            columns=['from', 'to', 'length optimal', 'weight optimal', 'length shortest', 'weight shortest',
                     'ratio length',
                     'ratio weight'], crs="EPSG:3857")

        # on which field to take the cost
        print(self.from_to_route_cost.crs)
        self.optimal_field = 'r_pdflw_pk'
        self.i_point = 0
        self.from_point = ''
        # read point network into geodataframe
        self.points_network = gpd.read_file(path_pnt)
        # Build graph based on the network
        G = nx.readwrite.nx_shp.read_shp(path)
        self.G = G.to_undirected()
        self.len_list = len(G.nodes)
        self.dic = {}

    def parallelize_dataframe(self, buffers):
        buffers.apply(lambda x: self.cal_routs_one_pnt(x['geometry_pnt'], x['geometry']), axis=1)

    def cal_routs_one_pnt(self, geometry, buffer):
        """

        :param geometry: geometry of the source point
        :param buffer: buffer around the source point to get all destination points within the buffer
        :return:
        """
        print("Local time:", time.ctime(time.time()))
        print("Progress {:2.4%}".format(self.i_point / self.len_list))
        self.i_point += 1

        # for each point get only the near area ( obtained by the buffer )
        point_list = gpd.clip(gdf=self.points_network, mask=buffer)
        # pool.map(func, df_split)
        point_list.apply(lambda x: self.cal_routs_source_dest(geometry, x), axis=1)

    def cal_routs_source_dest(self, node_from_init, node_to_init):
        try:
            # For each node calculate route to all the other nodes based on length and the others weights in case of
            # distance shorter than 1000 meters

            node_from = (node_from_init.x, node_from_init.y)
            node_to = (node_to_init['geometry'].x, node_to_init['geometry'].y)

            # cases to avoid ( go to the next point )
            str_node_to = str(node_to)
            str_node_from = str(node_from)
            # return in case of source and destination are the same points
            if str_node_from == str_node_to:
                return
            # since the graph is undirected p1-->p2 route is the same as p2-->p1
            if str(node_to) + str(node_from) in self.dic:
                # this pair are already checked
                return
            else:
                self.dic[str(node_from) + str(node_to)] = True
            # for source target nodes within a distance of 2000 meters calculate paths/ routs and costs
            shortest = nx.shortest_path(self.G, source=node_from, target=node_to, weight='length')
            optimal = nx.shortest_path(self.G, source=node_from, target=node_to, weight='r_pdflw_pk')
            shortest_length = nx.shortest_path_length(self.G, source=node_from, target=node_to, weight='length')
            optimal_weight = nx.shortest_path_length(self.G, source=node_from, target=node_to,
                                                     weight=self.optimal_field)
            new_row = {'from': str(node_from), 'to': str(node_to), 'length shortest': shortest_length,
                       'weight optimal': optimal_weight, 'geometry': Point(node_from_init.x, node_from_init.y)}
            if shortest == optimal:
                # when shortest path is equal to the optimal :
                new_row['weight shortest'] = new_row['weight optimal']
                new_row['length optimal'] = new_row['length shortest']
                new_row['ratio length'] = new_row['ratio weight'] = 1
            else:
                # otherwise complete missing information using field_cost_route function
                new_row['weight shortest'] = self.field_cost_route(shortest, self.optimal_field)
                new_row['length optimal'] = self.field_cost_route(optimal, 'length')
                new_row['ratio length'] = new_row['length optimal'] / new_row['length shortest']
                new_row['ratio weight'] = new_row['weight shortest'] / new_row['weight optimal']
            self.from_to_route_cost = self.from_to_route_cost.append(new_row, ignore_index=True)
        except nx.exception.NetworkXNoPath:
            return

    def field_cost_route(self, path, field):
        """
        this method calculate for the the given route a cost based on the given field
        :param path: given route
        :param field: length or other weight
        :param G: the graph
        :return: cost based on the given field
        """
        path_len = len(path)
        new_weight = 0
        for i in range(0, path_len - 1):
            new_weight += self.G[path[i]][path[i + 1]][field]
        return new_weight


if __name__ == '__main__':
    parameters = {'is_parallel': False}
    # convert shp file to graph and do it undirected
    # build a CalcRoutes member by send the network path and points network path to work on
    routs = CalcRoutes('output\Barking and Dagenham\Barking and Dagenham.shp',
                       'output\Barking and Dagenham\pnt_Barking and Dagenham_ntwrk.shp')
    # my_data_set = SameAreaCell(G_list, 2000)

    # make a buffer around each point
    buffers = routs.points_network['geometry'].buffer(1000)
    buffers = gpd.GeoDataFrame(crs=routs.points_network.crs, geometry=buffers)
    buffers['geometry_pnt'] = routs.points_network['geometry']
    # calculate route from each points to others in buffer of 1000 meters and save the results in our database
    if parameters['is_parallel']:
        df_split = np.array_split(buffers, 8)
        pool = Pool(8)
        pool.map_async(routs.parallelize_dataframe, df_split)
        pool.close()
        pool.join()
    else:
        buffers.apply(lambda x: routs.cal_routs_one_pnt(x['geometry_pnt'], x['geometry']), axis=1)

    # test_list = []

    # convert the dataframe to shpfile
    routs.from_to_route_cost.to_file('routs.shp')
    print(routs.from_to_route_cost['ratio length'].mean())
    print(routs.from_to_route_cost['ratio weight'].mean())
# 30.9.2020
# def field_cost_route(path, field, G):
#     """
#     this method calculate for the the given route a cost based on the given field
#     :param path: given route
#     :param field: length or other weight
#     :param G: the graph
#     :return: cost based on the given field
#     """
#     path_len = len(path)
#     new_weight = 0
#     for i in range(0, path_len - 1):
#         new_weight += G[path[i]][path[i + 1]][field]
#     return new_weight
#
#
# if __name__ == '__main__':
#     # convert shp file to graph and do it undirected
#     G = nx.readwrite.nx_shp.read_shp('New_Folder/Camden.shp')
#     G = G.to_undirected()
#     # Dataframe to save all the necessary information
#     from_to_route_cost = gpd.GeoDataFrame(
#         columns=['from', 'to', 'length optimal', 'weight optimal', 'length shortest', 'weight shortest', 'ratio length',
#                  'ratio weight'])
#     # For each node calculate route to all the other nodes based on length and the others weights in case of
#     # distance shorter than 2000 meters
#     G_list = list(G.nodes)
#     len_list = len(G_list)
#     for ind_from, node_from in enumerate(G_list):
#         print("Local time:", time.ctime(time.time()))
#         print("Progress {:2.1%}".format(ind_from / len_list))
#         for ind_to in range(ind_from + 1, len_list):
#             optimal_field = 'r_pdflw_pk'
#             node_to = G_list[ind_to]
#             dist_temp = dist(node_to, node_from)
#             if dist_temp < 2000:
#                 # for source target nodes within a distance of 2000 meters calculate paths/ routs and costs
#                 shortest = nx.shortest_path(G, source=node_from, target=node_to, weight='length')
#                 optimal = nx.shortest_path(G, source=node_from, target=node_to, weight='r_pdflw_pk')
#                 shortest_length = nx.shortest_path_length(G, source=node_from, target=node_to, weight='length')
#                 optimal_weight = nx.shortest_path_length(G, source=node_from, target=node_to, weight=optimal_field)
#                 new_row = {'from': node_from, 'to': node_to, 'length shortest': shortest_length,
#                            'weight optimal': optimal_weight}
#                 if shortest == optimal:
#                     # when shortest path is equal to the optimal :
#                     new_row['weight shortest'] = new_row['weight optimal']
#                     new_row['length optimal'] = new_row['length shortest']
#                     new_row['ratio length'] = new_row['ratio weight'] = 1
#                 else:
#                     # otherwise complete missing information using field_cost_route function
#                     new_row['weight shortest'] = field_cost_route(shortest, optimal_field, G)
#                     new_row['length optimal'] = field_cost_route(optimal, 'length', G)
#                     new_row['ratio length'] = new_row['length optimal'] / new_row['length shortest']
#                     new_row['ratio weight'] = new_row['weight shortest'] / new_row['weight optimal']
#                 from_to_route_cost = from_to_route_cost.append(new_row, ignore_index=True)
#     # convert the dataframe to shpfile
#     from_to_route_cost['geometry'] = from_to_route_cost['from']
#     from_to_route_cost.to_file('routs.shp')
#     print(from_to_route_cost['ratio length'].mean())
#     print(from_to_route_cost['ratio weight'].mean())
# 23.9.2020
# def optimal_shortest_route(path_short, pnode_toath_opt, G):
#     # find the ratio between length  of the optimal path and shourtest path
#     u = time.time()
#     acc = 0
#     # go over all the optional route ( shorter then the cutoff) in the path_short dictionary
#     for key, values in path_short.items():
#         for key2, length_short in values.items():
#             # ignore path to itself
#             if length_short == 0:
#                 continue
#             else:
#                 path = path_opt[key][key2]
#                 length_opt = 0
#                 # calculate the length of the optimal route with same source and destination points
#                 for i in range(len(path) - 1):
#                     length_opt += G[path[i]][path[i + 1]]['length']
#                 print('p{},p{} --,{},{}'.format(path[0], path[-1], length_short, length_opt))
#                 acc += (length_opt / length_short) - 1
#
#     print(time.time() - u)
#     return acc
# if __name__ == '__main__':
#     # wards = gpd.read_file('New_Folder/small_area.shp')
#     # G = ox.graph_from_polygon(wards['geometry'][0], network_type='walk')
#     # G = ox.project_graph(G)
#     # G= G.to_undirected()
#
#
#
#     # gdf_format = ox.graph_to_gdfs(G)
#     # pnts = gdf_format[0].loc[:, ['geometry']].to_file('New_Folder/pnts.shp')
#     # ox.graph_to_gdfs(G,nodes= False).loc[:, ['geometry']].to_crs(epsg=3857).to_file('New_Folder/lines.shp')
#     G = nx.readwrite.nx_shp.read_shp('New_Folder/Camden.shp')
#     G= G.to_undirected()
#     # project the file to compatible coordinate system
#     # plt.subplot(121)
#     # nx.draw(G)
#
#     # # for optimal path return the route and for shortest path return the route length
#     path_opt = dict(nx.all_pairs_dijkstra_path(G, weight='length',cutoff= 2000))
#     print(path_opt)
# plt.show()
# path_short = dict(nx.all_pairs_dijkstra_path_length(G, weight='length', cutoff=2000))
# print(time.time() - g)
# optimal_shortest_route(path_short, path_opt, G)

# 22.9.2020

# df = pd.DataFrame({'num_legs': [2, 4, -5, -6],
#                    'num_wings': [2, 0, 0, -6],
#                    'num_specimen_seen': [10, 2, 1, 8]},
#                   index=['falcon', 'dog', 'spider', 'fish'])
# print(df)
# df[df['num_legs'] < 0] = 0
# print(df)
# print(list(range(7,10)) + list(range(16,19)))
# print(len(range(7,10)))
# 16.9.2020
# G = nx.Graph()
# G.add_edges_from([(1, 2, {'length': 9, 'final': 8}), (2, 3, {'length': 10, 'final': 31}),
#                   (1, 6, {'length': 27, 'final': 13}), (5, 6, {'length': 12, 'final': 22})
#                      , (4, 5, {'length': 13, 'final': 18}), (1, 4, {'length': 15, 'final': 17}),
#                   (1, 3, {'length': 8, 'final': 22}), (3, 4, {'length': 12, 'final': 16})])
#
# # bb = nx.edge_betweenness_centrality(G, normalized=False)
# # print(bb)
# # nx.set_edge_attributes(G, bb, 'final')
# path_opt = dict(nx.all_pairs_dijkstra_path(G, weight='final'))
# path_short = dict(nx.all_pairs_dijkstra_path_length(G, weight='length', cutoff=30))
# print(path_opt)
# print(path_short)
# acc = 0
# for key,values in path_short.items():
#     for key2 ,length_short in values.items():
#         if length_short==0:
#             continue
#         else:
#             path = path_opt[key][key2]
#             length_opt = 0
#             for i in range(len(path)-1):
#                 length_opt+= G[path[i]][path[i+1]]['length']
#             print('p{},p{} --,{},{}'.format(path[0],path[-1],length_short,length_opt))
#             acc += (length_opt/length_short)  - 1
#
# print(acc)
# plt.subplot(111)
# nx.draw(G, with_labels=True, font_weight='bold')
# plt.show()

# # convert list to string if necessary
# def list_to_str(row):
#     try:
#         for column, value in row.items():
#             if (column != 'geometry') & (isinstance(row[column], list)):
#                 row[column] = ','.join(str(row[column]))
#     except:
#         print('fdkljf;das')
#     return row
#
#
# print('download graph')
# graph = ox.graph_from_point((51.5118134, -0.0912761), dist=100 ,network_type='walk')
#
# print('prepare')
# graph_pr = ox.project_graph(graph)
# G = graph_pr.to_undirected()
#
#
# # create new attributes
# print('create new attributes')
# G = nx.Graph(G)
# bb = nx.edge_betweenness_centrality(G, normalized=False)
# nx.set_edge_attributes(G, bb, 'final')
#
# # # G = nx.MultiGraph(G)
# print('calculate graph across the network')
# g = time.time()
# # for optimal path return the route and for shortest path return the route length
# path_opt = dict(nx.all_pairs_dijkstra_path(G, weight='final'))
# path_short = dict(nx.all_pairs_dijkstra_path_length(G, weight='length', cutoff=50))
# u = time.time()
# print(u-g)
# acc = 0
# # find the ratio between length  of the optimal path and shourtest path
# acc = 0
# # go over all the optional route ( shorter then the cutoff) in the path_short dictionary
# for key,values in path_short.items():
#     for key2 ,length_short in values.items():
#         # ignore path to itself
#         if length_short==0:
#             continue
#         else:
#             path = path_opt[key][key2]
#             length_opt = 0
#             # calculate the length of the optimal route with same source and destination points
#             for i in range(len(path)-1):
#                 length_opt+= G[path[i]][path[i+1]]['length']
#             print('p{},p{} --,{},{}'.format(path[0],path[-1],length_short,length_opt))
#             acc += (length_opt/length_short)  - 1
#
# print(acc)
# print(time.time()-u)
# print(time.time() - g)
# #
# plt.subplot(111)
#
# nx.draw(G, node_size=20)
# plt.show()
# print(path)
# path = dict(nx.all_pairs_bellman_ford_path(G))
# print(path)
# print(path[0][4])
# plt.subplot(111)
# ox.io.save_graph_shapefile('test')
# edges = ox.graph_to_gdfs(graph_pr, nodes=False)
# edges_new = edges.apply(lambda row: list_to_str(row), axis=1)
# edges_new.to_file('test.shp')

# 13.9.2020
# add normalization fields to final results
# units_df = gpd.read_file(r'output\general_output\acc_index_london_districts.shp')
# units_df['norm_index'] = (units_df['index'] - units_df['index'].min()) / (
#             units_df['index'].max() - units_df['index'].min())
# units_df['norm_cen'] = (units_df['index_cen'] - units_df['index_cen'].min()) / (
#             units_df['index_cen'].max() - units_df['index_cen'].min())
# units_df.to_file(r'output\general_output\acc_index_london_districts2.shp')
#
# units_df = gpd.read_file(r'output\general_output\acc_index_london_wards.shp')
# units_df['norm_index'] = (units_df['index'] - units_df['index'].min()) / (
#             units_df['index'].max() - units_df['index'].min())
# units_df['norm_cen'] = (units_df['index_cen'] - units_df['index_cen'].min()) / (
#             units_df['index_cen'].max() - units_df['index_cen'].min())
# units_df.to_file(r'output\general_output\acc_index_london_wards2.shp')
# 9.9.2020

# # Step 1: Redefine, to accept `i`, the iteration number
# def howmany_within_range2(i, row, minimum, maximum):
#     """Returns how many numbers lie within `maximum` and `minimum` in a given `row`"""
#     count = 0
#     for n in row:
#         if minimum <= n <= maximum:
#             count = count + 1
#     return (i, count)
# if __name__ == '__main__':
#     # Prepare data
#     np.random.RandomState(100)
#     arr = np.random.randint(0, 10, size=[200000, 5])
#     data = arr.tolist()
#     data[:5]
#
#     ## Parallel processing with Pool.apply_async()
#
#     import multiprocessing as mp
#     pool = mp.Pool(mp.cpu_count())
#     results = []
#
#
#
#
#     # Step 2: Define callback function to collect the output in `results`
#     def collect_result(result):
#         global results
#         results.append(result)
#
#
#     # Step 3: Use loop to parallelize
#     for i, row in enumerate(data):
#         pool.apply_async(howmany_within_range2, args=(i, row, 4, 8), callback=collect_result)
#
#     # Step 4: Close Pool and let all the processes complete
#     pool.close()
#     pool.join()  # postpones the execution of next line of code until all processes in the queue are done.
#
#     # Step 5: Sort results [OPTIONAL]
#     results.sort(key=lambda x: x[0])
#     results_final = [r for i, r in results]
#
#     print(results_final[:10])

# > [3, 1, 4, 4, 4, 2, 1, 1, 3, 3]
# # 16.8.2020
# folder= r'pedestrian_flow\germany\output\final'
# os.chdir(folder)
# final_gpd = gpd.GeoDataFrame()
# for file in glob.glob("*.shp"):
#     print(file)
#     # for each network get the location from old network
#     new_gpd = gpd.read_file(file)
#
#     print(new_gpd.shape[0])
# 12.08.2020
# array =np.array([0.225,0.235,0.258])
# print((array*100).astype(int))
# pr
# print((array*100))
# 08.10.2020
# file = pd.read_csv(r'C:\Users\achituv\Downloads/aaa.csv')
# file2= gpd.read_file('avital3.shp')
# file['osm_id'] =file['osm_id'].astype(int)
# file2['osm_id'] =file2['osm_id'].astype(int)
# new = file2.merge(file,how='left',on='osm_id')
# new.to_file('avital4.shp')
# file = pd.read_csv(r'C:\Users\achituv\Downloads/TelAvivRoads.csv')
# file['geometry'] = file['WKT'].apply(wkt.loads)
# from shapely import wkt
# test= gpd.GeoDataFrame(file,geometry=file['geometry'],crs="EPSG:4326")
# test.to_file('avital.shp')
# 02.08.2020
# graph_pr= nx.petersen_graph()
# plt.subplot(111)
#
# nx.draw(graph_pr, with_labels=True, font_weight='bold')
# # plt.show()
# path = dict(all_pairs_shortest_path_length(graph_pr,cutoff=1))
# print(path)
# store the integration index results for each edge

# main_dict = {}
# len_edge = len(graph_pr.edges)
# # for each edge, the algorithm goes over all the nodes in graph and store the min shortest path between the node
# # and its two nodes than add it to to int_index.
# # at the end of each loop int_index divide by the number of lines -1  (normalization)
# # is literally the integration for the edge
# for i, edge in enumerate(graph_pr.edges):
#     print("Progress {:2.1%}".format(i / len_edge))
#     int_index = 0
#     len_nodes = len(graph_pr.nodes)
#     for j, node in enumerate(graph_pr.nodes):
#         print("     Progress {:2.1%}".format(j / len_nodes))
#         weight_1 = len(path[edge[0]][node])
#         weight_2 = len(path[edge[1]][node])
#         miny = min(weight_1, weight_2)
#         int_index += miny - 1
#     main_dict[edge] = int_index / (len_edge - 1)
# print(main_dict)
# find the most similar string in teh list
# word= 'Bahnhofstra?e, Saarbr?cken'
# possibilities =['Bahnhofstraße, Saarbrücken','Bahnhofstraße (Süd), Bielefeld']
# print(difflib.get_close_matches(word, possibilities, n=1))
# 30.7.2020
# Test get features

# 28.7.2020
# integration index calculation with networkX

# G = nx.petersen_graph()
# # Calculate shortest path between all nodes in the graph
# path = dict(all_pairs_shortest_path(G))
# # store the integration index results for each edge
# main_dict = {}
# len_edge = len(G.edges)
# # for each edge, the algorithm goes over all the nodes in graph and store the min shortest path between the node
# # and its two nodes than add it to to int_index.
# # at the end of each loop int_index divide by the number of lines -1  (normalization)
# # is literally the integration for the edge
# for edge in G.edges:
#     int_index = 0
#     for node in G.nodes:
#         weight_1 = len(path[edge[0]][node])
#         weight_2 = len(path[edge[1]][node])
#         miny = min(weight_1, weight_2)
#         int_index += miny - 1
#     main_dict[edge] = int_index / (len_edge - 1)

# add the results as a new properties to the edge's graph
# nx.set_edge_attributes(G, main_dict, 'integration')
# print(nx.get_edge_attributes(G, 'integration'))
# plt.subplot(111)
#
# nx.draw(G, with_labels=True, font_weight='bold')
# plt.show()
# # this variable will store the integration index results for each node
# g_keys = path.keys()
# size = len(g_keys)
# int_dict = {k: sum(map(len, path[k].values())) / size for k in g_keys}
# int_dict_edges = {k: min(int_dict[k[0]], int_dict[k[1]]) for k in G.edges()}
# nx.set_node_attributes(G, int_dict, 'integration')
# print(nx.get_node_attributes(G, 'integration'))

# print(G.edges())
# for key in path.keys():
#     print(path[key])
#
# print(sum(map(len, path[0].values())))
# nx.set_node_attributes()_attributes(G, , 'betweenness')
# draw the graph

# Solution Without Paralleization

# Step 1: Redefine, to accept `i`, the iteration number
# def howmany_within_range2(i, row, minimum, maximum):
#     """Returns how many numbers lie within `maximum` and `minimum` in a given `row`"""
#     count = 0
#     for n in row:
#         if minimum <= n <= maximum:
#             count = count + 1
#     return (i, count)
#
#
# # Step 2: Define callback function to collect the output in `results`
# def collect_result(result):
#     global results
#     results.append(result)
#
#
# if __name__ == "__main__":
#     print("Number of processors: ", mp.cpu_count())
#
#     # Prepare data
#     np.random.RandomState(100)
#     arr = np.random.randint(0, 10, size=[200000, 5])
#     data = arr.tolist()
#
#     results = []
#
#     # Parallelizing using Pool.apply()
#
#     # Step 1: Init multiprocessing.Pool()
#     pool = mp.Pool(mp.cpu_count())
#
#     # Step 2: `pool.apply` the `howmany_within_range()`
#     time = datetime.now()
#     # Step 3: Use loop to parallelize
#     for i, row in enumerate(data):
#         pool.apply_async(howmany_within_range2, args=(i, row, 4, 8), callback=collect_result)
#
#     # Step 4: Close Pool and let all the processes complete
#     pool.close()
#     pool.join()  # postpones the execution of next line of code until all processes in the queue are done.
#     print(datetime.now() - time)
#
#     # Step 5: Sort results [OPTIONAL]
#     results.sort(key=lambda x: x[0])
#     results_final = [r for i, r in results]
#
#     print(results_final[:10])

# 22.7.2020
# dates = pd.date_range('20130101', periods=6)
# df = pd.DataFrame(np.random.randn(6, 4), index=dates, columns=list('ABCD'))
# print(df)
# df['A'] = df['A'].append(pd.Series(data= [1]))
# print(df)
# print(df['A'])
# # 20.7.2020
# pd1 = pd.read_excel('germany/all__raw_data2.xlsx', encoding='utf-8-sig')
# pd2 = pd.read_csv('germany/all__raw_data.csv', encoding='utf-8-sig')
# my_lisy= list(pd2['location'])
# for local in pd1['location']:
#     if local in my_lisy:
#         continue
#     else:
#         print('{} not in all__raw_data'.format(local))
# print(pd['location'].head())
# 19.7.2020
# integration index calculation with networkX

# G = nx.petersen_graph()
# # Calculate shortest path between all nodes in the graph
# path = dict(all_pairs_shortest_path(G))
# # store the integration index results for each edge
# main_dict = {}
# len_edge = len(G.edges)
# # for each edge, the algorithm goes over all the nodes in graph and store the min shortest path between the node
# # and its two nodes than add it to to int_index.
# # at the end of each loop int_index divide by the number of lines -1  (normalization)
# # is literally the integration for the edge
# for edge in G.edges:
#     int_index = 0
#     for node in G.nodes:
#         weight_1 = len(path[edge[0]][node])
#         weight_2 = len(path[edge[1]][node])
#         miny = min(weight_1, weight_2)
#         int_index += miny - 1
#     main_dict[edge] = int_index / (len_edge - 1)
#
# # add the results as a new properties to the edge's graph
# nx.set_edge_attributes(G, main_dict, 'integration')
# print(nx.get_edge_attributes(G, 'integration'))
# plt.subplot(111)
#
# nx.draw(G, with_labels=True, font_weight='bold')
# plt.show()
# # this variable will store the integration index results for each node
# g_keys = path.keys()
# size = len(g_keys)
# int_dict = {k: sum(map(len, path[k].values())) / size for k in g_keys}
# int_dict_edges = {k: min(int_dict[k[0]], int_dict[k[1]]) for k in G.edges()}
# nx.set_node_attributes(G, int_dict, 'integration')
# print(nx.get_node_attributes(G, 'integration'))
#

# print(G.edges())
# for key in path.keys():
#     print(path[key])
#
# print(sum(map(len, path[0].values())))
# # nx.set_node_attributes()_attributes(G, , 'betweenness')
# # draw the graph
#

# # 13.7.2020
# lms only with highway = traffic signal
# lm = gpd.read_file('output/lm.shp')
# lm = lm[lm['highway'] == 'traffic_signals']
# accessibility_dic = {'traffic_signals:vibration': 'vibration',
#                      'traffic_signals:sound': 'sound', 'button_operated': 'button',
#                      'traffic_signals:minimap': 'minimap',
#                      'traffic_signals:arrow': 'arrow', 'traffic_signals:floor_light': 'light',
#                      'traffic_signals:floor_vibration': 'floor'}
# columns_list = list(lm.columns)
# columns_accessibility =[]
# for key in accessibility_dic.keys():
#     if key in columns_list:
#         columns_accessibility.append(key)
# lm = lm[lm.loc[:, columns_accessibility].any(axis=1, skipna=False, bool_only=True)]
# lm.to_file('output/test.shp')
# # 12.7.2020
# test = [8.0382985, 52.2641336, 8.0615705, 52.2822274]
# result = str(test)
#
# result= result.replace('[', '').replace(']','')
# print(result)
# print(type(result))
#
# point0 = Point(2, 3)
# point1 = Point(20, 3)
# point3 = Point(20, 30)
#
# s = gpd.GeoSeries([Point(1, 1), Point(2, 2), Point(3, 3)])
#
# print(point3.distance(s))
# lattice = [ [(i + j) for i in range(3)] for j in range(3) ]
# print(lattice)

# exclude rows that all values in tags is none
# df = gpd.read_file(r'output/lm.shp')
# df = df['traffic_si'].dropna()
# # lm[lm.loc[:, lm.columns.values[:-1]].any(axis=1, skipna=False, bool_only=True)]
# df.to_csv('test.csv')

# df_2 = df[df['traffic_signals']]
# print(df_2.head())
# df = df[df.loc[:, df.columns.values[:-1]].any(axis=1, skipna=False, bool_only=True)]
# df['test'] = df.loc[:, df.columns.values[:-1]].any(axis=1, skipna=False, bool_only=True)
# df_2 = df[~df['test']]
# df_2.to_csv(r'output/test2.csv')
# my_dict = {1: (1, 2), 2: (3, 4)}
# print(my_dict)
# for key in my_dict:
#     my_dict[key] = my_dict[key] + (key,)
# print(my_dict)
# import networkx as nx
# G = nx.path_graph(3)
# bb = nx.edge_betweenness_centrality(G, normalized=False)
# nx.set_edge_attributes(G, bb, 'betweenness')
# G.edges[1, 2]['betweenness']
