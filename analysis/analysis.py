# https://electronics.stackexchange.com/questions/83354/calculate-distance-from-rssi
# https://stackoverflow.com/questions/4357799/convert-rssi-to-distance
# https://iotandelectronics.wordpress.com/2016/10/07/how-to-calculate-distance-from-the-rssi-value-of-the-ble-beacon/

#%%
import math

import pandas as pd
import plotly.express as px

data_file = "../server/data.csv"

df = pd.read_csv(data_file, encoding='utf-8')

#%% create clean dataframe
net = pd.DataFrame()
net['time'] = df['stime']
net['src'] = df['mac']
net['dst'] = df['ssid'].apply(lambda val: val.split('-')[1])
# net['dist'] = df['rssi']
one_m_rssi = -40
net['dist'] = df['rssi'].apply(lambda val: 10 ** ((one_m_rssi - val) / (10 * 2)))

# shorten names
net['src'] = net['src'].apply(lambda val: val[-2:])
net['dst'] = net['dst'].apply(lambda val: val[-2:])

# alphabetize order
uids = set(net['src'].unique().tolist())
uids.update(set(net['dst'].unique().tolist()))
uids = sorted(list(uids))

# replace with means
netsummary = net.groupby(['src', 'dst']).aggregate({'dist': ['mean', 'std']})
netsummary_flat = netsummary.reset_index()
netsummary_flat.columns = netsummary_flat.columns.map("|".join).str.strip("|")

# px.scatter_3d(
#     net,
# #   netsummary,
#     x='src',
#     y='dst',
#     z='dist',

#     color='time',

# #   z='dist|mean',
# #   error_z='dist|std',
# #   color='src',

#     category_orders={
#     'src': uids,
#     'dst': uids,
#     }
# )

finals = []
for i in range(len(uids)):
    for j in range(i+1, len(uids)):
        finals.append({
            'a': uids[i],
            'b': uids[j],
            'edge': f"{uids[i]}-{uids[j]}",
            'dist': (netsummary.loc[uids[i], uids[j]]['dist']['mean'] +
                     netsummary.loc[uids[j], uids[i]]['dist']['mean']) / 2,
            'err': (netsummary.loc[uids[i], uids[j]]['dist']['std'] ** 2 +
                    netsummary.loc[uids[j], uids[i]]['dist']['std'] ** 2) / 2,
        })

finals = pd.DataFrame(finals)
finals.to_csv('test-00.csv', index=False)

# px.bar(finals, 'edge', 'dist', error_y='err')
px.bar(finals, 'edge', 'dist')
#%% 1d
locs = {u:[] for u in uids}

origin = uids[0]
locs[origin] = [{'x': 0}]

edges = dict(zip(
    finals[finals['a'] == origin]['b'].to_list(),
    finals[finals['a'] == origin]['dist'].to_list()
))
edges.update(dict(zip(
    finals[finals['b'] == origin]['a'].to_list(),
    finals[finals['b'] == origin]['dist'].to_list()
)))
for edge, dist in edges.items():
    locs[edge].append({'x': dist})
    locs[edge].append({'x': -dist})

finals[finals['b'] == origin]

#%%