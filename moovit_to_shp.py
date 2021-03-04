import tkinter as tk
from tkinter import filedialog

import geopandas as gpd
import pandas as pd
from shapely import wkt


def data_to_shp():
    csv_file = filedialog.askopenfilename(
        title="select pedestrain estimation with osm id",
        filetypes=(
            ("csv files", "*.csv"), ("all files", "*.*")))
    csv_file = pd.read_csv(csv_file)
    osm_network = gpd.read_file('osm_network.shp')
    csv_file['osm_id'] = csv_file['OSM'].astype(int)
    osm_network['osm_id'] = osm_network['osm_id'].astype(int)
    osm_network_new = osm_network.merge(csv_file, how='left', on='osm_id')
    osm_network_new.to_file('osm_network_new.shp')


def polygon_to_shp():
    csv_file = filedialog.askopenfilename(
        title="select polygon csv file",
        filetypes=(
            ("csv files", "*.csv"), ("all files", "*.*")))

    csv_file['geometry'] = csv_file['WKT'].apply(wkt.loads)
    test = gpd.GeoDataFrame(csv_file, geometry=csv_file['geometry'], crs="EPSG:4326")
    test.to_file('osm_network.shp')


if __name__ == '__main__':
    root = tk.Tk()

    canvas1 = tk.Canvas(root, width=300, height=300)
    canvas1.pack()

    button1 = tk.Button(text='merge pedestrain estimation to osm_network', command=data_to_shp, bg='brown', fg='white')
    canvas1.create_window(200, 200, window=button1)

    button2 = tk.Button(text='polygon to shape file', command=data_to_shp, bg='brown', fg='white')
    canvas1.create_window(100, 100, window=button2)

    root.mainloop()
# file = pd.read_csv(r'C:\Users\achituv\Downloads/TelAvivRoads.csv')
# file['geometry'] = file['WKT'].apply(wkt.loads)
# from shapely import wkt
# test= gpd.GeoDataFrame(file,geometry=file['geometry'],crs="EPSG:4326")
# test.to_file('avital.shp')
