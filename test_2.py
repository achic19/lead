import time
from math import dist

import geopandas as gpd
import networkx as nx


# 30.9.2020
def field_cost_route(path, field, G):
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
        new_weight += G[path[i]][path[i + 1]][field]
    return new_weight


if __name__ == '__main__':
    # convert shp file to graph and do it undirected
    G = nx.readwrite.nx_shp.read_shp('New_Folder/Camden.shp')
    G = G.to_undirected()
    # Dataframe to save all the necessary information
    from_to_route_cost = gpd.GeoDataFrame(
        columns=['from', 'to', 'length optimal', 'weight optimal', 'length shortest', 'weight shortest', 'ratio length',
                 'ratio weight'])
    # For each node calculate route to all the other nodes based on length and the others weights in case of
    # distance shorter than 2000 meters
    G_list = list(G.nodes)
    len_list = len(G_list)
    for ind_from, node_from in enumerate(G_list):
        print("Local time:", time.ctime(time.time()))
        print("Progress {:2.1%}".format(ind_from / len_list))
        for ind_to in range(ind_from + 1, len_list):
            optimal_field = 'r_pdflw_pk'
            node_to = G_list[ind_to]
            dist_temp = dist(node_to, node_from)
            if dist_temp < 2000:
                # for source target nodes within a distance of 2000 meters calculate paths/ routs and costs
                shortest = nx.shortest_path(G, source=node_from, target=node_to, weight='length')
                optimal = nx.shortest_path(G, source=node_from, target=node_to, weight='r_pdflw_pk')
                shortest_length = nx.shortest_path_length(G, source=node_from, target=node_to, weight='length')
                optimal_weight = nx.shortest_path_length(G, source=node_from, target=node_to, weight=optimal_field)
                new_row = {'from': node_from, 'to': node_to, 'length shortest': shortest_length,
                           'weight optimal': optimal_weight}
                if shortest == optimal:
                    # when shortest path is equal to the optimal :
                    new_row['weight shortest'] = new_row['weight optimal']
                    new_row['length optimal'] = new_row['length shortest']
                    new_row['ratio length'] = new_row['ratio weight'] = 1
                else:
                    # otherwise complete missing information using field_cost_route function
                    new_row['weight shortest'] = field_cost_route(shortest, optimal_field, G)
                    new_row['length optimal'] = field_cost_route(optimal, 'length', G)
                    new_row['ratio length'] = new_row['length optimal'] / new_row['length shortest']
                    new_row['ratio weight'] = new_row['weight shortest'] / new_row['weight optimal']
                from_to_route_cost = from_to_route_cost.append(new_row, ignore_index=True)
    # convert the dataframe to shpfile
    from_to_route_cost['geometry'] = from_to_route_cost['from']
    from_to_route_cost.to_file('routs.shp')
    print(from_to_route_cost['ratio length'].mean())
    print(from_to_route_cost['ratio weight'].mean())
