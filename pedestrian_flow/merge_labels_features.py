import difflib
import glob
import os

import geopandas as gpd
import pandas as pd


class MergeLabelFeatures:

    def __init__(self, labels_file: pd.DataFrame, features_files: pd.DataFrame, country, encoding='utf-8'):
        """

        :param labels_file: dataframe with labels
        :param features_files: dataframe with features
        :param country: determine how to merge
        :param encoding: in case of Germany wouldn't be the default
        """
        if country == 'Germany':
            network_for_ml = features_files.merge(labels_file, how='left', on='location')
        else:
            network_for_ml = labels_file.merge(features_files, how='left', on='location')
        network_for_ml.to_csv(country + '/network_for_ml.csv', encoding=encoding)

    @staticmethod
    def create_features_file(folder):
        """
        # פונקצייה ישנה
        :param folder store all the network with the rows to merge ( field location is not null)
        """
        gpd_to_convert = gpd.GeoDataFrame()
        os.chdir(folder)
        for file in glob.glob("*.shp"):
            temp_gpd = gpd.read_file(os.path.join(file))
            temp_gpd = temp_gpd[temp_gpd['location'].notnull()]
            gpd_to_convert = gpd_to_convert.append(temp_gpd)
        gpd_to_convert.to_excel('features.xlsx')

    @staticmethod
    def merge_location_to_features(folder):
        """

        :param folder: with shapefiles
        :return:
        """
        os.chdir(folder)
        final_gpd = gpd.GeoDataFrame()
        for file in glob.glob("*.shp"):
            print(file)
            # for each network get the location from old network
            new_gpd = gpd.read_file('final/' + file)
            print(new_gpd.length)
            new_gpd.drop('LENGTH', axis=1, inplace=True)

            new_gpd = new_gpd[new_gpd['location'].notnull()]
            final_gpd = final_gpd.append(new_gpd)

        # Upload correct address file
        addresses_path = os.path.join(os.path.dirname(__file__), 'germany', 'labels.csv')
        correct_addresses = pd.read_csv(addresses_path, low_memory=False, encoding='utf-8-sig')
        location_correct = list(correct_addresses['location'].unique())

        locations = final_gpd['location'].unique()
        for location in locations:
            "get the the correct name from location_correct  list"
            final_gpd.at[final_gpd['location'] == location, 'location'] = \
                difflib.get_close_matches(location, location_correct, n=1)[0]

        final_gpd.to_csv(os.path.join(os.path.dirname(__file__), 'germany', 'features.csv'), encoding='utf-8-sig')
        final_gpd.to_file(os.path.join(os.path.dirname(__file__), 'germany', 'features.shp'))
