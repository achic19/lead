import pickle

import geopandas as gpd
import numpy as np
import osmnx as ox
import pandas as pd


class GetFeatures:
    def __init__(self, network, polygon, output_name):
        """
        :param network to join feature to
        :param polygon to download elements in within the polygon extent
        :param output_name file name to save the results
        """
        # buffer of 20 meters around the network
        print('  calculate buffer')
        network['seg_name'] = network.index  # 'seg_name' to merge in the end
        buffer = network.geometry.buffer(20, cap_style=2)
        buffer = gpd.GeoDataFrame(crs=network.crs, geometry=buffer)
        buffer['seg_name'] = network.index

        # # download poi elements to calculate spatial features
        print('  download data')
        self.dict_poi = {'amenity': True, 'office': True, 'tourism': True, 'shop': True, 'building': True,
                         'natural': True, 'leisure': True, 'landuse': True}
        # download and project poi
        if isinstance(polygon, str):
            lm = ox.pois.pois_from_place(polygon, tags=self.dict_poi)
        else:
            lm = ox.pois.pois_from_polygon(polygon, tags=self.dict_poi)
        lm = lm.to_crs(epsg=3857)
        # determine which column to save to shp file
        columns = [value for value in list(self.dict_poi.keys()) if value in list(lm.columns)]
        columns.append('geometry')
        lm = lm.loc[:, columns]
        columns.append('seg_name')

        # save the poi to the disk for testing
        GetFeatures.save_lm(lm)
        # join poi data to buffer polygon
        print('  calculete spatial join')
        buffer_with_lm = gpd.sjoin(buffer, lm, how="inner", op='intersects')
        # group by geometry and for each group (same geometry) for each tag
        # (except landuse for which save the first not null instance) count the
        # number of instances ( not null) and then keep all in new geo data frame
        buffer_with_lm['geometry_wkt'] = buffer_with_lm['geometry'].apply(lambda x: x.wkt).values
        groups = buffer_with_lm.groupby(['geometry_wkt'])
        main_list = []
        for group_name in buffer_with_lm['geometry_wkt'].unique():
            group = groups.get_group(group_name)
            list_temp = list(group.count())
            att_list = list_temp[3:10]
            if list_temp[10] > 0:
                notna_group = group[group['landuse'].notna()]
                landuse = notna_group.groupby(['landuse']).count()['geometry'].sort_values(ascending=False).index[0]
                att_list.append(landuse)
            else:
                att_list.append('0')
            att_list.extend([group['geometry'].iloc[0], group['seg_name'].iloc[0]])
            main_list.append(att_list)
        new_data_frame = gpd.GeoDataFrame(main_list, columns=columns, crs=buffer_with_lm.crs)

        # # join buffer data into our network (how='left' keep all the network records and suffixes=('', '_y')
        # for the geometry column)
        print('  merge buffer with lm data to network file')
        network_with_features = network.merge(new_data_frame, how='left', on='seg_name', suffixes=('', '_y'))
        network_with_features.drop(['geometry_y', 'seg_name'], axis=1, inplace=True)
        network_with_features['landuse'].fillna('0', inplace=True)
        network_with_features.to_file(output_name)

    @staticmethod
    def save_lm(lm):
        # delete unnecessary rows
        for geometry_type in ['Point', 'Polygon']:
            print(' ' + geometry_type)
            output = ''.join(['more_files/', geometry_type, '.shp'])
            lm_temp = lm[lm['geometry'].type == geometry_type]
            lm_temp.to_file(output)
            lm_temp = gpd.read_file(output)
            # delete unnecessary rows
            lm_temp = lm_temp[lm_temp.loc[:, lm_temp.columns.values[:-1]].any(axis=1, skipna=False, bool_only=True)]
            lm_temp.to_file(output)

    @staticmethod
    def assign_values(category_value_dict, category):
        """

        :param category_value_dict: get values from
        :param category: category of the current row
        :return:
        """
        try:
            return category_value_dict[category]['code']
        except KeyError:
            # in case of new category
            return 0

    @staticmethod
    def calculate_padestrain_flow(model_file, network_file, category_value_foder, name):
        """
        :param category_value_folder: change the categories to values in network based on files in this folder
        :param network_file: calculate pedestrian flow for
        :param model_file: sav file with a model that predict pedestrian flow
        :return:
        """
        # upload files

        loaded_model = pickle.load(open(model_file, 'rb'))
        network = gpd.read_file(network_file)

        # Normalize tags features
        columns = ['highway', 'choice', 'integ', 'amenity', 'office', 'tourism', 'shop', 'building', 'natural',
                   'leisure', 'landuse', 'time', 'day']
        for i in range(3, 10):
            network[columns[i]] = network[columns[i]] / network.length

        # highway and landuse
        network["new_highway"] = network["highway"]  # for latter
        for column in ["highway", "landuse"]:
            category_value = pd.read_csv(category_value_foder + '/' + column + '_category_value.csv',
                                         index_col='category')
            category_value_dict = category_value.to_dict('index')
            # apply on network[column] assign_values function with category_value_dict find code/value for each row
            network[column] = network.apply(lambda x: GetFeatures.assign_values(category_value_dict, x[column]), axis=1)

        # integ
        # file_to_normlized = pd.read_csv(category_value_foder + '/all_date_to_ml.csv',encoding='utf-8-sig')
        # network['integ'] = network['integ'] / network['integ'].max()

        # Run the model 3 times in peak hour ,  off hour ( till 22:00) and in weekend
        network = GetFeatures.run_the_model(network, columns, loaded_model, list(range(7, 10)) + list(range(16, 19)),
                                            range(2, 7), 'pk_hr')
        network = GetFeatures.run_the_model(network, columns, loaded_model, list(range(10, 16)) + list(range(19, 22)),
                                            range(2, 7), 'off_hr')
        network = GetFeatures.run_the_model(network, columns, loaded_model, range(7, 22), [1, 7], 'wknd')
        network.to_file(name)

    @staticmethod
    def run_the_model(network, columns, loaded_model, range_1, range_2, name):
        '''

        :param network: network/area to calculate pedestrian flow
        :param columns: tags features
        :param loaded_model: the machine learning model to predict pedestrian flow
        :param range_1: hours
        :param range_2: days. based on hours and days the average will be perfromed
        :param name:  peak hour ,  off hour ( till 22:00) and  weekend
        :return:
        '''
        temp_result = np.zeros((network.shape[0], len(range_1) * len(range_2)))
        k = 0
        for i in range_2:
            for j in range_1:
                print('{} , {}'.format(i, j))
                network['day'] = i
                network['time'] = j
                X = network.loc[:, columns].fillna(0).to_numpy()
                temp_result[:, k] = loaded_model.predict(X)
                k += 1
        network["pdflw_" + name] = np.mean(temp_result, axis=1)
        return network
