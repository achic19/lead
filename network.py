from _datetime import datetime

import networkx as nx
import osmnx as ox
from networkx.algorithms.centrality import edge_betweenness_centrality
from networkx.algorithms.shortest_paths.unweighted import all_pairs_shortest_path_length

from accessibility_dic import accessibility_dic, get_acc_tags_shp


class Network:
    def __init__(self, area, output, centrality=True,
                 useful_tags_path=None):
        """
        The class gets a name of polygon and saves shapefile which includes pedestrian network within
        the polygon extent
        :param area: the place polygon to get the walk network from
        :param output: where to store the network as shapefile
        :param centrality: add centrality indices to edges
        :param useful_tags_path: tags to download from OSM
        """
        # define the tags that should be downloaded with the network
        if useful_tags_path is None:
            useful_tags_path = ['highway', 'handrail', 'footway', 'crossing', 'sidewalk']
            useful_tags_path.extend(list(accessibility_dic.keys()))
        ox.utils.config(useful_tags_way=useful_tags_path)

        #  downloaded the graph based on the specified location and make undirected it project it
        print('download data - {}'.format(datetime.now()))
        if isinstance(area, str):
            graph = ox.graph_from_place(area, network_type='walk')
        else:
            graph = ox.graph_from_polygon(area, network_type='walk')

        # make the graph undirected graph then project  the graph
        self.graph_pr = ox.project_graph(graph)
        self.graph_pr = self.graph_pr.to_undirected()

        if centrality:
            # Calculate betweenness/choice and closeness/integration.
            # to work properly the algorithm work on graph. to run
            # graph_to_gdfs later the code convert it back to MultiGraph.
            print('calculate integration at {}'.format(datetime.now()))
            self.graph_pr = nx.Graph(self.graph_pr)
            # line_graph convert graph to line graph so edges become nodes
            edge_centrality = nx.closeness_centrality(nx.line_graph(self.graph_pr))
            nx.set_edge_attributes(self.graph_pr, edge_centrality, 'integ')

            print("calculate choice- {}".format(datetime.now()))
            dic = edge_betweenness_centrality(self.graph_pr)
            nx.set_edge_attributes(self.graph_pr, dic, 'choice')

            self.graph_pr = nx.MultiGraph(self.graph_pr)

        # from graph to geodataframe , save the point dateframe for later use
        gdf_format = ox.graph_to_gdfs(self.graph_pr)
        gdf_format[0].to_crs(epsg=3857).to_file('pnt_' + output)
        # create dataframe with the necessary columns and convert to shapefile
        edges = gdf_format[1]
        self.columns = [value for value in useful_tags_path if value in list(edges.columns)]
        edges_new = edges.apply(lambda row: self.list_to_str(row), axis=1)

        edges_new.crs = edges.crs
        self.columns.append('geometry')
        if centrality:
            self.columns.append('choice')
            self.columns.append('integ')
        edges_shp = edges_new.loc[:, self.columns]
        # rename long name (accessibility tags)
        edges_shp = get_acc_tags_shp(edges_shp)
        # project the file to compatible coordinate system
        edges_shp.to_crs(epsg=3857).to_file(output)

    # convert list to string if necessary
    def list_to_str(self, row):
        for column in self.columns:
            if isinstance(row[column], list):
                row[column] = ','.join(row[column])
        return row

    def integration(self):
        print('calculate integration at {}'.format(datetime.now()))
        # Calculate shortest path between all nodes in the graph
        path = dict(all_pairs_shortest_path_length(self.graph_pr))
        print("finish to calculate shortest path between all pairs at {}".format(datetime.now()))
        # store the integration index results for each edge
        main_dict = {}
        len_edge = len(self.graph_pr.edges)
        # for each edge, the algorithm goes over all the nodes in graph and store the min shortest path between the node
        # and its two nodes than add it to to int_index.
        # at the end of each loop int_index divide by the number of lines (normalization)
        # is literally the integration for the edge
        for i, edge in enumerate(self.graph_pr.edges):
            print("Progress {:2.1%}".format(i / len_edge))
            int_index = 0
            len_nodes = len(self.graph_pr.nodes)
            for j, node in enumerate(self.graph_pr.nodes):
                print("     Progress {:2.1%}".format(j / len_nodes))
                weight_1 = path[edge[0]][node]
                weight_2 = path[edge[1]][node]
                miny = min(weight_1, weight_2)
                int_index += miny
            main_dict[edge] = int_index / len_edge

        # add the results as a new properties to the edge's graph
        nx.set_edge_attributes(self.graph_pr, main_dict, 'integ')
