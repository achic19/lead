from operator import itemgetter

from geopandas import GeoSeries
from shapely.geometry import Point


class Cell:
    def __init__(self):
        self.points = []


class SameAreaCell():

    def __init__(self, points_list, size):
        """
        The class gets in GeoSerie of point and convert it to a same cell spatial dataset
        :param points_list:
        """
        # Number of cell in each dimension
        self.size_cell = size
        if isinstance(points_list, GeoSeries):
            total_bound = points_list.total_bounds
            self.x_min = total_bound[0]
            self.y_min = total_bound[1]
            n_y = int((total_bound[3] - self.y_min) / self.size_cell) + 1
            n_x = int((total_bound[2] - self.x_min) / self.size_cell) + 1
        else:
            self.x_min = min(points_list, key=itemgetter(0))[0]
            self.y_min = min(points_list, key=itemgetter(1))[1]
            n_y = int((max(points_list, key=itemgetter(1))[1] - self.y_min) / self.size_cell) + 1
            n_x = int((max(points_list, key=itemgetter(0))[0] - self.x_min) / self.size_cell) + 1
        self.data_set = [[Cell() for i in range(n_x)] for j in range(n_y)]
        # self.data_set = np.empty((n_x, n_y), dtype=object)
        # self.data_set[:, :] = Cell()
        if isinstance(points_list, GeoSeries):
            points_list.apply(lambda pnt: self.add_point(pnt))
        else:
            for pnt in points_list:
                self.add_point(Point(pnt[0], pnt[1]))

    def add_point(self, pnt):
        in_x = int((pnt.x - self.x_min) / self.size_cell)
        in_y = int((pnt.y - self.y_min) / self.size_cell)
        self.data_set[in_y][in_x].points.append(Point(pnt))

    def find_cell(self, pnt):
        in_x = int((pnt.x - self.x_min) / self.size_cell)
        in_y = int((pnt.y - self.y_min) / self.size_cell)
        return in_x, in_y
