from _datetime import datetime

import networkx as nx
import osmnx as ox
from networkx.algorithms.centrality import edge_betweenness_centrality
from networkx.algorithms.shortest_paths.unweighted import all_pairs_shortest_path_length

from python_steps.accessibility_dic import accessibility_dic, get_acc_tags_shp


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
            print('calculate closeness at {}'.format(datetime.now()))
            self.graph_pr = nx.Graph(self.graph_pr)
            # line_graph convert graph to line graph so edges become nodes
            edge_centrality = nx.closeness_centrality(nx.line_graph(self.graph_pr))
            nx.set_edge_attributes(self.graph_pr, edge_centrality, 'closeness')

            print("calculate betweenness- {}".format(datetime.now()))
            dic = edge_betweenness_centrality(self.graph_pr)
            nx.set_edge_attributes(self.graph_pr, dic, 'betweenness')

            self.graph_pr = nx.MultiGraph(self.graph_pr)

        # from graph to geodataframe , save the point dateframe for later use
        gdf_format = ox.graph_to_gdfs(self.graph_pr)
        gdf_format[0].to_crs(epsg=3857).to_file(output, driver='GPKG', layer='_ntwrk_pnt')
        # create dataframe with the necessary columns and convert to shapefile
        edges = gdf_format[1]
        self.columns = [value for value in useful_tags_path if value in list(edges.columns)]
        edges_new = edges.apply(lambda row: self.list_to_str(row), axis=1)

        edges_new.crs = edges.crs
        self.columns.append('geometry')
        if centrality:
            self.columns.append('betweenness')
            self.columns.append('closeness')
        edges_shp = edges_new.loc[:, self.columns]
        # rename long name (accessibility tags)
        self.edges_shp = get_acc_tags_shp(edges_shp).to_crs(epsg=3857)
        # project the file to compatible coordinate system
        self.edges_shp.to_file(output, driver='GPKG', layer='_ntwrk')

    # convert list to string if necessary
    def list_to_str(self, row):
        for column in self.columns:
            if isinstance(row[column], list):
                row[column] = ','.join(row[column])
        return row

