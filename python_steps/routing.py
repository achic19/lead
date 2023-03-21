import os
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
    folders_path = 'output'
    # for folder_name in os.listdir(folders_path):
    folder_name = 'Kensington and Chelsea'
    folder_path = os.path.join(folders_path, folder_name)

    routs = CalcRoutes(os.path.join(folder_path, folder_name + '.shp'),
                       os.path.join(folder_path, 'pnt_' + folder_name + '_ntwrk.shp'))
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
    routs.from_to_route_cost.to_file(os.path.join(folder_path, 'routes.shp'))
    print(routs.from_to_route_cost['ratio length'].mean())
    print(routs.from_to_route_cost['ratio weight'].mean())
