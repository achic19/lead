import os

import geopandas as gpd
import pandas as pd

from get_features import GetFeatures
from network import Network
from pedestrian_flow.merge_labels_features import MergeLabelFeatures

# parameters = ['country' ,'network': True, 'get_features': True,'merge_labels_features']
parameters = {'country': 'Germany', 'merge_labels_features': True}
if parameters['country'] == 'Germany':
    os.chdir('germany')
    list_place = ['Innenstadt,Osnabrück,Germany',
                  'Altstadt,Mainz,Germany',
                  'Mitte,Bielefeld,Germany',
                  'Hauptbahnhof,Saarbrücken,Germany',
                  'Altstadt,Trier,Germany',
                  'Innenstadt,Augsburg,Germany',
                  'Innenstadt,Braunschweig,Germany',
                  'Stadtbezirk 1,Düsseldorf,Germany',
                  'Charlottenburg,Berlin,Germany',
                  'Bonn-Zentrum,Bonn,Germany',
                  ]
else:
    os.chdir('tel_aviv')
    list_place = ['Tel Aviv,Tel Aviv,Israel', ]

# Calculate features
keys_parameters = parameters.keys()
if 'network' in keys_parameters or 'get_features' in keys_parameters:
    for place in list_place:
        print(place)
        if parameters['country'] == 'Germany':
            city = place.split(',')[1]
            output = os.path.join('networks', city + '.shp')
        else:
            # special case with Tel Aviv
            city = 'tel_aviv'
            place = place['geometry'][0]
            output = os.path.join('networks', 'tel_aviv.shp')

        if 'network' in keys_parameters:
            print(' network')
            Network(place, output, centrality=True, useful_tags_path=['highway'])

        if 'get_features' in keys_parameters:
            print(' get_features')
            gdb = gpd.read_file(output)
            GetFeatures(gdb, place, 'output/' + city + '.shp')

# merge labels and features
if 'merge_labels_features' in keys_parameters:
    print(' merge_labels_features')

    if parameters['country'] == 'Germany':
        features_folder = 'output'
        features_file = MergeLabelFeatures.merge_location_to_features(features_folder)
        os.chdir(os.path.dirname(__file__))
        # for Germany the feature file type and encoding are different
        features_file = pd.read_csv('germany/features.csv')
        labels_file = pd.read_csv('germany/labels.csv')
        encoding = 'utf-8-sig'
    else:
        os.chdir(os.path.dirname(__file__))
        features_file = pd.read_csv('tel_aviv/features.csv')
        labels_file = pd.read_csv('tel_aviv/labels.csv')
        encoding = 'utf-8'

    MergeLabelFeatures(labels_file, features_file, parameters['country'], encoding=encoding)
