import glob
import os
from datetime import datetime

import networkx as nx
import pandas as pd

# Upload correct address file
correct_addresses = pd.read_csv('network_for_ml.csv', low_memory=False, encoding='utf-8-sig')
location_correct = list(correct_addresses['location'].unique())

# Upload incorrect address network
location_dict = {}
os.chdir('output')

# for each network keep all rows with locations and find the current location name on location_correct list
for shapefile in glob.glob("*.shp"):
    time_0 = datetime.now()
    # network = gpd.read_file(os.path.join(shapefile))
    G = nx.read_shp(shapefile)
    print(G)
    print(datetime.now() - time_0)
    break
    locations = network[network['location'].notnull()]['location'].unique()
    for location in locations:
        network.at[network['location'] == location, 'location'] = \
            difflib.get_close_matches(location, location_correct, n=1)[0]
    network.to_csv('new/test.csv', encoding='utf-8-sig')
    break
