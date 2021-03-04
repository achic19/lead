import geopandas as gpd
import pandas as pd
from shapely import wkt


def prepare_input_data(file, crs_file):
    """
    :param file: file to convert to geodataframe
    :param crs_file: shape file with the necessary crs
    :return: geodataframe with length and without unnecessary columns
    """
    # add length as new field
    file['geometry'] = file['geometry'].apply(wkt.loads)
    file = gpd.GeoDataFrame(file, crs=crs_file.crs, geometry=file['geometry'])
    file['length'] = file['geometry'].length
    file = file.loc[:, columns]
    return file


if __name__ == "__main__":
    # parameters = ['prepare', 'normalization']
    parameters = ['prepare', 'normalization']
    global columns
    columns = ['highway', 'choice', 'integ', 'amenity', 'office', 'tourism', 'shop', 'building', 'natural',
               'leisure', 'landuse', 'time', 'day', 'ped_flow', 'location', 'date', 'length']
    if 'prepare' in parameters:
        # file to build samples
        tel_aviv = pd.read_csv('tel_aviv/network_for_ml.csv')
        germany = pd.read_csv('germany/network_for_ml.csv', encoding='utf-8-sig')
        # add length to files
        tel_aviv = prepare_input_data(tel_aviv, gpd.read_file('tel_aviv/links_utm.shp'))
        germany = prepare_input_data(germany, gpd.read_file('germany/networks/Augsburg.shp'))

        # append data
        all_data_to_ml = germany.append(tel_aviv)
        all_data_to_ml.to_csv('all_date_to_ml.csv', encoding='utf-8-sig')

    if 'normalization' in parameters:
        data = pd.read_csv('all_date_to_ml.csv', encoding='utf-8-sig')
        # Reduce data volume
        data = data.sample(frac=1).reset_index(drop=True)
        small_date_set = data
        # for i in [1, 2, 3]:
        #     small_date_set = small_date_set.append(data[data['ped_flow'] == i].iloc[:25000, :])
        # Normalize tags features
        for i in range(3, 10):
            small_date_set[columns[i]] = small_date_set[columns[i]] / small_date_set['length']

        # Normalize highway and landuse

        for column in ["highway", "landuse"]:
            # for category_value: dictionary of values and category --> create  category_value
            # date frame with new categories and their name--> make the categories index and save to csv file
            temp_dic = dict(enumerate(small_date_set[column].astype('category').cat.categories))
            category_value = pd.DataFrame(columns=['category', 'code'])
            category_value['code'] = temp_dic.keys()
            category_value['category'] = temp_dic.values()
            category_value.set_index('category', inplace=True)
            category_value.to_csv(column + '_category_value.csv')

            # normalize
            small_date_set[column] = small_date_set[column].astype('category').cat.codes

        # Normalize space syntax indices
        # for column in ["integ"]:
        #     small_date_set[column] = small_date_set[column] / small_date_set[column].max()

        small_date_set.to_csv('small_date_to_ml.csv', encoding='utf-8-sig')
