import geopandas as gpd

# all the accessibility tags to use over the implementation
accessibility_dic = {'tactile_paving': 'tactile_pa',
                     'traffic_signals:vibration': 'vibration',
                     'traffic_signals:sound': 'sound', 'button_operated': 'button',
                     'traffic_signals:minimap': 'minimap',
                     'traffic_signals:arrow': 'arrow', 'traffic_signals:floor_light': 'light',
                     'traffic_signals:floor_vibration': 'floor'}


def get_acc_tags_shp(shape_file: gpd.GeoDataFrame):
    # rename long name columns
    for key, value in accessibility_dic.items():
        if key in shape_file.columns:
            shape_file.rename(columns={key: value}, inplace=True)
    return shape_file

# def get_acc_tags_shp(shape_file: pd.DataFrame):
#     columns_accessibility = []
#     accessibility_dic_new = {}
#     for key in accessibility_dic.keys():
#         if key in shape_file.column:
#             columns_accessibility.append(key)
#             # this to rename field name later
#             accessibility_dic_new[key] = accessibility_dic[key]
#     return columns_accessibility, accessibility_dic_new
