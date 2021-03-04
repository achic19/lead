import pandas as pd

df = pd.read_csv('labels.csv')
# sort dataframe by pedestrian flow( descending)  and location(ascending)
df.sort_values(by=['ped_flow', 'location'], inplace=True, ascending=[False, True])

# group by location (to save the previous sorting, here sort=False)
groups = list(df.groupby('location', sort=False).groups.keys())[:9]
pd.DataFrame(groups).to_csv('locations.csv', encoding='utf-8-sig')
