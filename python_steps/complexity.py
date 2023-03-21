import math

import geopandas as gpd


class Complexity:
    def __init__(self, name):
        # Name: CalculateField_Centroids.py
        # Description: Use CalculateField to assign centroid values to new fields

        # Input
        fc = gpd.read_file(name + "_wytyp.shp")
        fc["complexity"] = fc.apply(
            lambda x: self.count_complexity(x['geometry']), axis=1)
        # Output
        fc.to_file(name + "_cmplxty.shp")

    def count_complexity(self, geometry):

        # Enter for loop for each feature
        weight = 0
        PI = math.pi
        for i in range(len(geometry.xy[0]) - 2):
            # calc slope as  an angle
            x1 = geometry.xy[0][i]
            y1 = geometry.xy[1][i]
            x2 = geometry.xy[0][i + 1]
            y2 = geometry.xy[1][i + 1]
            x3 = geometry.xy[0][i + 2]
            y3 = geometry.xy[1][i + 2]
            angle1 = math.atan2(x2 - x1, y2 - y1)
            angle2 = math.atan2(x3 - x2, y3 - y2)

            # calc angle between two lines
            angle_b = PI - angle1 + angle2
            if angle_b < 0:
                angle_b = angle_b + 2 * PI
            if angle_b > 2 * PI:
                angle_b = angle_b - 2 * PI

            # if the distance between two points are less than 10 meters or the angle between two lines are larger
            # than 10 degrees add the angle to the weight
            test_angle = abs(angle_b - PI)
            if test_angle > math.radians(10) or ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5 < 10:
                weight += test_angle
        return weight

    # except Exception:
    #     e = sys.exc_info()[1]
    #     print(e.args[0])
