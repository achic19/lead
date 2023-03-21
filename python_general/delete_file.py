import os


def delete_shape_files(shp_path):
    for ext in ['.shp', '.cpg', '.prj', '.dbf', '.shx']:
        os.remove(shp_path + ext)

    print("File Removed!")

# def delete_shape_files(folders):
# create list of folder to remove files from
# folders = []
#
# # For the future
# # folders.append(os.path.dirname(__file__) + r'\add_new_pnts_by_angle\results_file')
#
# folders.append('output')
#
# for folder in folders:
#     # Delete all the folder in output folder thate include the london's district
#     for subfoler in os.listdir(folder):
#         folder_path = os.path.join(folder, subfoler)
#         try:
#             shutil.rmtree(folder_path)
#             # elif os.path.isdir(file_path): shutil.rmtree(file_path)
#         except Exception as e:
#             print(e)
