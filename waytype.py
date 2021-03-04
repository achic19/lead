import geopandas as gpd

from accessibility_dic import accessibility_dic


class WayType:

    def __init__(self, name):
        """"
        the class uploads the network  and use his dictionary variable that keeps all the rules
        in respect to this criterion.
        """

        self.dict = self.rank_highway()
        edges = gpd.read_file(name + "_lm.shp")

        accessibility_columns = [value for value in list(accessibility_dic.values()) if value in list(edges.columns)]
        # implemntation of waytype criterion on our network
        if 'handrail' in edges.columns:
            edges['waytype'] = edges.apply(
                lambda x: self.way_type(x['highway'], x['footway'], x['crossing'], x[accessibility_columns],
                                        x['handrail']),
                axis=1)
        else:
            edges['waytype'] = edges.apply(
                lambda x: self.way_type(x['highway'], x['footway'], x['crossing'], x[accessibility_columns]),
                axis=1)
        # edges = edges.loc[:, ['geometry', 'choice', 'integ', 'ped_flow', 'lm', 'waytype']]
        edges.to_file(name + "_wytyp.shp")

    def get_trafic_light(self):
        """under construction"""
        lm = gpd.read_file("output/lm.shp")
        lm = lm[lm['']]

    def rank_highway(self):
        """
        This dictionary helps to handle tags
        :return: the dictionary
        """
        return {'trunk': 10, 'primary': 10, 'secondary': 10, 'tertiary': 10, 'road': 10,
                'residential': 10, 'corridor': 10, 'elevator': 10,
                'trunk_link': 10, 'primary_link': 10, 'secondary_link': 10,
                'tertiary_link': 10,
                'footway': 11,
                'steps': 30,
                'living_street': 40, 'pedestrian': 40,
                'path': 50,
                'unclassified': 60, 'service': 60, 'track': 60, 'bridleway': 60, 'no': 60}

    def isunmarked(self, isunmarked, accessibility):
        """
            the function checks whether the crossing is marked
            @:param isunmarked is value of the tag crossing

            :return the cost
        """
        if isunmarked == 'unmarked':
            return 6
        elif accessibility[(accessibility != 'no') & (accessibility.notnull())].shape[0] == 0:
            return 4
        else:
            return 2

    def way_type(self, highway, footway, crossing, accessibility, handrail=None, ):
        # based on the row type - list or string,  is handled.
        """
            based on the argument's values, the cost in respect to waytype criterion is determined
            @:param highway the most important key, can not be empty
            @:param handrail for stairs element
            @:param footway if highway= footway the algorithm uses the footway key
            @:param crossing if footway = crossing the algorithm uses the crossing key
            @:param tactile_paving if footway = crossing the algorithm uses  also the tactile paving key
            :return the cost
        """
        if len(highway.split(',')) > 1:
            # The grade is determined by the max value according to the preset dictionary and the items in the list
            highway_temp = highway.split(',')
            grade = max([self.dict[temp] for temp in highway_temp])
        else:
            grade = self.dict[highway]

        if grade != 11 and grade != 30:
            return grade / 10
        # if the highway is steps or footway more tags should be examined
        elif grade == 30:
            if handrail == "yes":
                return 3
            else:
                return 4
        else:
            if footway is not None and len(footway.split(',')) > 1:
                if 'crossing' in footway:
                    return self.isunmarked(crossing, accessibility)
                else:
                    return 1
            else:
                if footway == 'crossing':
                    return self.isunmarked(crossing, accessibility)
                else:
                    return 1
