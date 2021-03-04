import os

import geopandas as gpd

from complexity import Complexity
from cost_neighborhood import CostNeighborhood
from final import Final
from get_features import GetFeatures
from landmark import Landmark
from network import Network
from waytype import WayType


class Accessibility:

    def __init__(self, neighborhood, folder, what_to_run, landmark_function_to_run, name):
        """
        :param neighborhood: which neiberhood exam accessibility
        :param folder: to save the results
        :param what_to_run: in developing stage no all the function should run
        :param landmark_function_to_run: many steps in this class , so sometime I run only part of them

        """
        # build the network based on the neighborhood
        # save absulute path to pedestrian_flow_model before changing workspace folder
        pedestrian_flow_folder = os.path.dirname(__file__) + '/pedestrian_flow'
        os.chdir(folder)
        if what_to_run['Network']:
            print('run Network')
            Network(neighborhood, name + '_ntwrk.shp')

        if what_to_run['get_features']:
            print(' get_features')
            gdb = gpd.read_file(name + '_ntwrk.shp')
            GetFeatures(gdb, neighborhood, name + '_features.shp')

        if what_to_run['pedestrian flow']:
            print(' pedestrian flow')
            GetFeatures.calculate_padestrain_flow(pedestrian_flow_folder + '/finalized_model.sav',
                                                  name + '_features.shp',
                                                  pedestrian_flow_folder, name + '_ped_flow.shp')

        # Calculate landmark criterion
        if what_to_run['landmark']:
            print('run landmark')
            Landmark(landmark_function_to_run, neighborhood, name)

        # Calculate waytype criterion
        if what_to_run['WayType']:
            print('run WayType')
            WayType(name)

        # Calculate complexity criterion
        if what_to_run['Complexity']:
            print('run Complexity')
            Complexity(name)

        # Calculate final cost
        if what_to_run['Final']:
            print('run Final')
            Final(name)


if __name__ == "__main__":
    # parameters
    what_to_run = {'Network': True, 'get_features': False, 'pedestrian flow': False, 'landmark': False,
                   'WayType': False, 'Complexity': False, 'Final': False, 'Cost Neighborhoods':
                       {'run only cost neighborhood': False, 'run cost neighborhood': 'london_wards.shp',
                        'run routing': [False, 'acc_index_london_wards.shp']}}
    # landmark_function_to_run = ['lm_from_osm_to_shp', 'delete empty rows', 'calc_lm_near', 'calc_lm_inter']
    # 'Cost Neighborhoods':{True -means run only on Cost Neighborhoods,
    # (False,london_districts.shp,london_wards.shp) ,run routing  - True or False}
    landmark_function_to_run = ['lm_from_osm_to_shp', 'delete empty rows', 'calc_lm_near', 'calc_lm_inter']
    wards = gpd.read_file('inputs/london_districts_4326.shp')
    if what_to_run['Cost Neighborhoods']['run only cost neighborhood'] is False:
        # for all streets in each  district in london districts calculate accessibility index
        for name in wards['DISTRICT'].unique():
            # if name == 'Camden' or name == 'Barking and Dagenham':
            #     continue
            print(name)
            ward = wards[wards['DISTRICT'] == name].reset_index(drop=True)
            # Create if necessary new folder for each district
            os.chdir(os.path.dirname(__file__))
            folder_path = '/'.join(['output', name])
            if not os.path.isdir(folder_path):
                os.makedirs(folder_path)
                os.makedirs(folder_path + '/more_files')
            Accessibility(ward['geometry'][0], folder_path, what_to_run, landmark_function_to_run, name)
            # Accessibility(neighborhood, folder_path, what_to_run, landmark_function_to_run, name)

    # # for  each  district in london districts calculate accessibility index
    if what_to_run['Cost Neighborhoods']['run cost neighborhood'] is not False:
        print('run Cost Neighborhoods')
        CostNeighborhood(what_to_run['Cost Neighborhoods']['run cost neighborhood'], 'network')
    if what_to_run['Cost Neighborhoods']['run routing'][0]:
        CostNeighborhood(what_to_run['Cost Neighborhoods']['run routing'][1], 'routing')
