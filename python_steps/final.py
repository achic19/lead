import os
from math import pi as PI

import geopandas as gpd

from delete_file import delete_shape_files


class Final:
    def __init__(self, name):
        """
        :param name: name of area which will be the name of the last file to save
        """
        self.final_network = gpd.read_file(name + "_cmplxty.shp")
        # Normalize:  complexity by 2*pi and lm by length
        self.final_network['lm_tot'].fillna(value=0, inplace=True)
        self.final_network['length'] = self.final_network['geometry'].length
        self.final_network['coxty_norm'] = self.final_network['complexity'] / (2 * PI)
        self.final_network['lm_norm'] = self.final_network['lm_tot'] / self.final_network['length']

        # calculate final weight
        self.final_network['final'] = self.final_network['waytype'] + self.final_network['coxty_norm'] - \
                                      self.final_network['lm_norm']

        # scale the length to way type range (1 to 6)
        self.calculate_new_length()
        # add pedestrian flow cost for 3 different cases, and also calculate cost for routing (consider length)
        for field in ['pdflw_pk_h', 'pdflw_off_', 'pdflw_wknd']:
            self.field_name = field  # use it later to create new fields with new costs
            self.add_ped_flow_fo_final_cost()

        # save the final network
        if os.path.isfile(name + ".shp"):
            delete_shape_files(name)
        self.final_network.to_file(name + ".shp")

    def calculate_new_length(self):
        # scale the length to way type range (1 to 6)
        old_min = self.final_network['length'].min()
        old_max = self.final_network['length'].max()

        new_min = 1
        new_max = 6

        old_range = old_max - old_min
        new_range = new_max - new_min
        self.final_network['new_length'] = (self.final_network['length'] - old_min) * new_range / old_range + new_min

    def routing(self, update_cost_field):
        """
        :param update_cost_field: the current field to use to create new cost considering length
        :return:
        """
        # calculate cost for routing (consider length)

        route_field = 'r_' + self.field_name  # the format of the field_name is f_~ , so the code eliminate it
        self.final_network[route_field] = self.final_network['new_length'] + self.final_network[update_cost_field]
        self.final_network.loc[self.final_network[route_field] < 0, route_field] = 0

    def add_ped_flow_fo_final_cost(self):
        # add pedestrian flow critreion to cost based on the value in  self.field_name
        # and also calculate cost for routing (consider length)
        new_cost = 'f_' + self.field_name
        self.final_network[new_cost] = self.final_network['final']
        self.final_network.loc[self.final_network[self.field_name] < 1.5, new_cost] = \
            self.final_network[new_cost] + 1
        self.final_network.loc[self.final_network[self.field_name] > 2.5, new_cost] = self.final_network[new_cost] + 2
        self.routing(new_cost)
