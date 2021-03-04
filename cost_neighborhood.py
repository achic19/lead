import os
import time

import geopandas as gpd
import networkx as nx
import numpy as np


class CostNeighborhood:
    def __init__(self, units, method):
        """
        :param units: the units to calculate the accessibility index
        :param method: which method to use ? network - apply based on network segments cost or based on ratio
        between optimal to shortest route
        """
        self.units = units
        self.method = method
        # change workspace
        os.chdir(os.path.dirname(__file__))
        if method == 'network':
            units_df = gpd.read_file('inputs/' + units)
        else:
            units_df = gpd.read_file('output/general_output/' + units)

        # for each district calculate index and weighted index with or without the centrality matrices and by
        # different hours and days
        for field in ['f_pdflw_pk', 'f_pdflw_of', 'f_pdflw_wk']:
            self.field = field
            str_list = field.split('_')
            new_field = str_list[0] + '_' + str_list[2]
            units_df[new_field] = units_df.apply(
                lambda unit: self.calculate_cost_index_per_neighborhood(unit), axis=1)
            # add normalization fields to final results
            # units_df['norm_' + new_field] = (units_df[new_field] - units_df[new_field].min()) / (
            #         units_df[new_field].max() - units_df[new_field].min())
            if method == 'network':
                units_df['cen_' + new_field] = units_df.apply(
                    lambda unit: self.calculate_weights_index_per_neighborhood(unit), axis=1)
                # add normalization fields to final results
                units_df['nrm' + new_field] = (units_df['cen_' + new_field] - units_df[
                    'cen_' + new_field].min()) / (
                                                      units_df['cen_' + new_field].max() - units_df[
                                                  'cen_' + new_field].min())
                units_df.to_file(os.path.join('output/general_output', 'acc_index_' + units))
            else:
                units_df.to_file(os.path.join('output/general_output', 'routing_' + units))

    def calculate_cost_index_per_neighborhood(self, neighborhood):
        """

        :param neighborhood: district
        :return: accessibility index ( mean of all streets in the district)
        """

        network = gpd.read_file(
            (os.path.join('output', neighborhood['DISTRICT'], neighborhood['DISTRICT']) + ".shp"))
        if self.units != 'london_districts.shp':
            # In case of wards clip should be done to get the network within the ward boundary
            print(neighborhood['NAME'])
            print(time.time())
            network = gpd.clip(gdf=network, mask=neighborhood.geometry)
        network = network[network['length'] > 10]
        if self.method == 'network':
            return network[self.field].mean()
        else:
            return self.calculate_routing_index(network)

    def calculate_weights_index_per_neighborhood(self, neighborhood):
        """
        :param neighborhood: district
        :return:  weighted index by the centrality matrices (choice and integration)
        """

        # for london_districts the index will calculated based on the name for other cases a clip should
        # be executed
        network = gpd.read_file(
            (os.path.join('output', neighborhood['DISTRICT'], neighborhood['DISTRICT']) + ".shp"))
        if self.units == 'london_wards.shp':
            print(neighborhood['NAME'])
            print(time.time())
            network = gpd.clip(gdf=network, mask=neighborhood.geometry)
        network = network[network['length'] > 10]
        weights = network['choice'] + network['integ']
        return np.average(network[self.field], weights=weights)

    def calculate_routing_index(self, network):
        network.to_file('test.shp')
        G = nx.readwrite.nx_shp.read_shp('test.shp').to_undirected()
        g = time.time()
        # for optimal path return the route and for shortest path return the route length
        path_opt = dict(nx.all_pairs_dijkstra_path(G, weight='final_for_'))
        path_short = dict(nx.all_pairs_dijkstra_path_length(G, weight='length', cutoff=1000))
        print(time.time() - g)
        return self.optimal_shortest_route(path_short, path_opt, G)

    def optimal_shortest_route(self, path_short, path_opt, G):
        # find the ratio between length  of the optimal path and shourtest path
        u = time.time()
        acc = 0
        # go over all the optional route ( shorter then the cutoff) in the path_short dictionary
        for key, values in path_short.items():
            for key2, length_short in values.items():
                # ignore path to itself
                if length_short == 0:
                    continue
                else:
                    path = path_opt[key][key2]
                    length_opt = 0
                    # calculate the length of the optimal route with same source and destination points
                    for i in range(len(path) - 1):
                        length_opt += G[path[i]][path[i + 1]]['length']
                    print('p{},p{} --,{},{}'.format(path[0], path[-1], length_short, length_opt))
                    acc += (length_opt / length_short) - 1

        print(time.time() - u)
        return acc
