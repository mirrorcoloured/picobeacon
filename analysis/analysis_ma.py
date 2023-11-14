import copy
from pprint import pprint
import os

import numpy as np
import pandas as pd

os.listdir('../server/')

data_file = "../server/data-2023-08-06-wifi-1.csv"

df = pd.read_csv(data_file, encoding='utf-8')
df.head(2)

def get_link(source, target, prefix=''):
    return '_'.join(sorted([
        source.replace(':', '').replace(prefix, ''),
        target.replace(':', '').replace(prefix, '')
    ]))

# Add columns
df['mac_bbsid'] = (df.mac + '_' + df.bssid).str.replace(':', '')
df['bbsid_mac'] = (df.bssid + '_' + df.mac).str.replace(':', '')
df['link'] = df.apply(lambda df: get_link(df.mac, df.bssid, '28cdc1026b'), axis=1)
df.head(2)

# Explore
df.head(2).T
df.mac.value_counts()
df.ssid.value_counts()
df.bssid.value_counts()

# Compare direction
(
    df.groupby('mac_bbsid').agg({'rssi': [np.mean, np.std]})
        .merge(
            df.groupby('bbsid_mac').agg({'rssi': [np.mean, np.std]}),
            left_on='mac_bbsid',
            right_on='bbsid_mac'
        )
)

# Groupby
df.groupby('link').agg({'rssi': [np.mean, np.std]})

# Compute mean abs signal
dist_df = df.groupby('link').apply(lambda df: df.rssi.abs().mean()).reset_index()
dist_df.columns = ['link', 'dist']
dist_df['source'] = dist_df['link'].apply(lambda s: s.split('_')[0])
dist_df['target'] = dist_df['link'].apply(lambda s: s.split('_')[1])
dist_df = dist_df.set_index(['source', 'target'])
dist_df

pos_dict = {
    'a0': {'x': 0, 'y': 0, 'z': 0}, # x, y, z: fixed
    'a6': {'x': 0, 'y': 0, 'z': 0}, # x, y, z: fixed
    'a8': {'x': 0, 'y': 0, 'z': 0}, # z: fixed
    'aa': {'x': 0, 'y': 0, 'z': 0},
}


# Override with fixed values and high values for flex values
pos_dict['a6']['x'] = dist_df.loc[('a0', 'a6')].dist
pos_dict['a8'] = {'x': 100, 'y': 100, 'z': 0}
pos_dict['aa'] = {'x': 100, 'y': 100, 'z': 100}


def compute_dist(source_point, target_point):
    return (
        (source_point['x'] - target_point['x'])**2 +
        (source_point['y'] - target_point['y'])**2 +
        (source_point['z'] - target_point['z'])**2
    )**0.5


def cost_function(dist_df, pos_dict):
    sum_sqr = 0
    for (source, target) in dist_df.index:
        dist = dist_df.loc[(source, target)].dist
        act_dist = compute_dist(pos_dict[source], pos_dict[target])
        sum_sqr = sum_sqr + (act_dist - dist)**2
    return sum_sqr**0.5




moveable_points = [
    ('a8', 'x'),
    ('a8', 'y'),
    ('aa', 'x'),
    ('aa', 'y'),
    ('aa', 'z'),
]

i = 0
last_cost = 10**6
while i < 10**2:
    options = []
    for mp in moveable_points:
        for prop in [0.9, 0.99, 0.999, 1.001, 1.01, 1.1]:
            # TODO: Implement without copy.
            copy_dict = copy.deepcopy(pos_dict)
            # copy_dict = pos_dict.copy() # This is a shallow copy and doesn't work
            copy_dict[mp[0]][mp[1]] = copy_dict[mp[0]][mp[1]] * prop
            cost = cost_function(dist_df, copy_dict)
            options.append(
                {
                    'mp': mp,
                    'cost': cost,
                    'pos_dict': copy_dict,
                }
            )
    best_option = sorted(options, key=lambda d: d['cost'])[0]
    best_cost = best_option['cost']
    if i % 10 == 0:
        print(best_cost)
    if (best_cost > last_cost):
        break
    pos_dict = best_option['pos_dict']
    last_cost = best_cost
    i = i + 1

pprint(pos_dict)




