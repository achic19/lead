import os

import pandas as pd


# functions
def calculate_ped_flow(ped_value):
    """

    :param ped_value: number of pedestrian per hour per link
    :return: 1- crowdy 2- optimal 3- empty
    """
    try:
        space_meter_sec = 60 * 60 * speed / ped_value
    except ZeroDivisionError:
        return 1
    if space_meter_sec > 15:
        return 1
    if space_meter_sec < 1:
        return 3
    else:
        return 2


# Parameters
folder_data = 'hystreet'

big_file = pd.DataFrame()
speed = 0.833
# read all data and merge it to one big file
for csv_file in os.listdir(folder_data):
    path = os.path.join(folder_data, csv_file)
    big_file = big_file.append(pd.read_csv(path))

# Split the columns to extract the necessary data

split_file = big_file.iloc[:, 0].str.split(';', expand=True)
split_file.reset_index(inplace=True)
# Extract time
time_date = split_file.iloc[:, 2].str.split(expand=True)
big_file.reset_index(inplace=True)
big_file['time'] = time_date.iloc[:, 1].str.split(':', expand=True).iloc[:, 0].astype(
    int)
# Extract day
days = {"Monday": 2, "Tuesday": 3, "Wednesday": 4, "Thursday": 5, "Friday": 6, "Saturday": 7, "Sunday": 1}
big_file['day'] = list(map(lambda x: days[x], split_file.iloc[:, 3]))
# Calculate pedestrian flow level
big_file['ped_flow'] = split_file.iloc[:, 4].apply(lambda x: calculate_ped_flow(int(x)))
# Extract date
big_file['date'] = time_date.iloc[:, 0]
# Extract location
big_file['location'] = split_file.iloc[:, 0].astype(str) + ',' + split_file.iloc[:, 1].astype(str)

# output data
big_file = big_file.iloc[:, 2:]
big_file.to_csv('labels.csv', encoding='utf-8-sig')
