import geopandas as gpd
import osmnx as ox
from shapely.geometry import Point

from accessibility_dic import accessibility_dic
from same_area import SameAreaCell


def dissolve_geometry(to_dissolve):
    """
    This function get a geodatabase and merge the same geometry polygons into one and add new attribute that
    counts the number of same geometry
    :param to_dissolve: the geodatabase to merge the same geometry polygons
    :return: geodatabase with new column 'lm' that store for each polygon how many lm within.
    """
    to_dissolve['geometry_wkt'] = to_dissolve['geometry'].apply(lambda x: x.wkt).values
    groups = to_dissolve.groupby(['geometry_wkt'])
    main_list = []
    for group_name in groups.groups:
        group = groups.get_group(group_name)
        att_list = [group['geometry'].iloc[0], group['seg_name'].iloc[0]]
        att_list.append(group.shape[0])
        main_list.append(att_list)
    new_data_frame = gpd.GeoDataFrame(main_list, columns=['geometry', 'seg_name', 'lm'], crs=to_dissolve.crs)
    return new_data_frame


class Landmark:
    def __init__(self, what_to_run, polygon, network_name):
        """
        Calculating a value in respect to Landmark criterion
        :param start_point: where to start the process (from the beginning (start_point= 0) up to calculate
        only lm in intersection (start_point= 3)
        :param polygon: to download the data from osm
        :param network_name:  the network file name
        """
        self.dict_poi = {'natural': 'tree', 'power': 'pole', 'leisure': 'picnic_table',
                         'shop': ['supermarket', 'bakery'],
                         'highway': ['street_lamp', 'traffic_signals', 'crossing', 'bus_stop', 'stop', 'steps'],
                         'amenity': ['telephone', 'fast_food', 'fountain', 'fuel', 'bicycle_parking', 'bicycle_rental',
                                     'waste_disposal', 'food_court', 'bus_station',
                                     'waste_basket', 'vending_machine', ' recycling', 'post_box', 'bench', 'grit_bin']}
        temp_dic = {key: True for key in accessibility_dic}
        self.dict_poi = {**self.dict_poi, **temp_dic}
        # A variable help to analysis run time
        self.i = 0
        self.num_of_edges = ''
        # variable for same_area algorithm - a lm point can be count only once in a polyline
        self.dict_of_pnt = {}
        self.my_data_set = []
        self.polygon = polygon
        self.network_name = network_name
        # Download for the first time
        if 'lm_from_osm_to_shp' in what_to_run:
            self.lm_from_osm_to_shp()

        # It's a separate step since any work well when the gpd read shapefile. In this step features with no
        # date in all tags will be deleted from lm
        if 'delete empty rows' in what_to_run:
            print(' delete empty rows')
            lm = gpd.read_file(r'more_files/lm.shp')
            self.lm = lm[lm.loc[:, lm.columns.values[:-1]].any(axis=1, skipna=False, bool_only=True)]
            self.lm.to_file(r'more_files/lm.shp')
        else:
            self.lm = gpd.read_file(r'more_files/lm.shp')

        # Here each buffer will store the number of lm within and than
        # join buffer with data about number of lm to the network
        if 'calc_lm_near' in what_to_run:
            self.calc_lm_near()

        # add lm in intersections
        if 'calc_lm_inter' in what_to_run:
            self.calc_lm_inter()

    def lm_from_osm_to_shp(self):
        """
        retrieve data from OSM about the lm based on tags in dict_poi variable and save it as
        shapefile
        :return:
        """
        print(' lm_from_osm_to_shp')
        # create landmarks layer
        # read landmarks elements
        lm = ox.pois.pois_from_polygon(self.polygon, tags=self.dict_poi)

        # handle accessibility tags
        columns_accessibility = []
        columns_list = list(lm.columns)
        accessibility_dic_new = {}
        # store only records in accessibility_dic that exist also in lm column
        for key in accessibility_dic.keys():
            if key in columns_list:
                columns_accessibility.append(key)
                # this to rename field name later
                accessibility_dic_new[key] = accessibility_dic[key]
        # store only intersection of columns in self.dict_poi and lm
        columns = [value for value in list(self.dict_poi.keys()) if value in list(lm.columns)]
        # append more tags to save to shp results
        columns.append('geometry')
        columns.extend(columns_accessibility)
        lm = lm.loc[:, columns]
        # Save only Point type
        lm = lm[lm['geometry'].type == 'Point']
        # project the results to UTM and save it to shape file
        lm = lm.to_crs(epsg=3857)
        # rename long field name
        lm.rename(columns=accessibility_dic_new, inplace=True)
        lm.to_file(r'more_files/lm.shp')
        # lm.to_csv(r'output/lm.csv')

    def calc_lm_near(self):
        """
        Create shapefile that store for each edge the number of LM in a distance
        less than 5 meter
        :return:
        """
        print(' calc_lm_near')
        shp = gpd.read_file(self.network_name + "_ped_flow.shp")
        # delete irrelevant columns
        columns_to_drop = ['highway', 'amenity', 'office', 'tourism', 'shop', 'building', 'natural',
                           'leisure', 'landuse', 'time', 'day']
        edges_shp = shp.drop(columns_to_drop, axis=1)
        edges_shp['highway'] = edges_shp["new_highwa"]
        edges_shp = edges_shp.drop("new_highwa", axis=1)
        edges_shp['seg_name'] = edges_shp.index
        buffer = edges_shp.geometry.buffer(5, cap_style=2)
        buffer = gpd.GeoDataFrame(crs=edges_shp.crs, geometry=buffer)
        buffer['seg_name'] = edges_shp.index

        # Join to buffer polygons within lm
        buffer_with_lm = gpd.sjoin(buffer, self.lm, how="inner", op='intersects')
        buffer_with_lm.to_file("more_files/buffer_with_lm.shp")

        # Dissolve by geometry so each buffer will store the number of lm within
        buffer_dissolve = dissolve_geometry(buffer_with_lm)
        buffer_dissolve.to_file("more_files/buffer_lm_count.shp")

        # # join buffer data into our network (how='left' keep all the network records and suffixes=('', '_y')
        # for the geometry column)
        network_with_features = edges_shp.merge(buffer_dissolve, how='left', on='seg_name', suffixes=('', '_y'))
        network_with_features.drop(['geometry_y', 'seg_name'], axis=1, inplace=True)
        # Delete unnecessary coulmns
        network_with_features.to_file(self.network_name + "_lm.shp")

    def calc_lm_inter(self):
        print(' calc_lm_inter')
        edges_with_lm = gpd.read_file(self.network_name + "_lm.shp")
        # Build a Qtree dataset with landmarks
        self.my_data_set = SameAreaCell(self.lm['geometry'], 5)

        self.num_of_edges = edges_with_lm.shape[0]
        edges_with_lm["lm_inter"] = edges_with_lm.apply(
            lambda x: self.sum_lm_intersect(x['geometry']), axis=1)
        # calculate the total number of lm around each polyline
        edges_with_lm['lm_tot'] = edges_with_lm["lm_inter"] + edges_with_lm["lm"]
        edges_with_lm.to_file(self.network_name + "_lm.shp")

    def sum_lm_intersect(self, geometrey):
        """
        :param geometrey: geometry of network polyline
        :return: the number of lm around an intersection points
        """
        # for each polyline calculate the the number of lm around ( the first and the end point)
        print("Progress {:2.1%}".format(self.i / self.num_of_edges))
        self.i = self.i + 1
        xy = geometrey.xy
        end_index = len(xy[0]) - 1
        point_0 = Point(xy[0][0], xy[1][0])
        point_1 = Point(xy[0][end_index], xy[1][end_index])

        return self.find_points_list(point_0) + self.find_points_list(point_1)

    def find_points_list(self, point):
        in_x, in_y = self.my_data_set.find_cell(point)
        points_list = []
        shape = (len(self.my_data_set.data_set), len(self.my_data_set.data_set[0]))
        for i in [in_x - 1, in_x, in_x + 1]:
            if i < shape[1]:
                for j in [in_y - 1, in_y, in_y + 1]:
                    if j < shape[0]:
                        points_list.extend(self.my_data_set.data_set[j][i].points)
        return self.find_lm_near(point, points_list)

    def find_lm_near(self, p, lm_list):
        """
        :param lm_list:
        :param p: find all the lm points close to p
        :return:
        """
        # if the lm is in a distance of less than 5 meters return 2 ( multiple effect on the user)
        lm_count = 0

        if lm_list is not None:
            for lm in lm_list:
                if lm.distance(p) < 5:
                    if str(lm) not in self.dict_of_pnt:
                        lm_count += 2
                        self.dict_of_pnt[str(lm)] = True
        return lm_count
