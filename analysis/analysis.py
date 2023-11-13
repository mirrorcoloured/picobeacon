# https://en.wikipedia.org/wiki/Trilateration
# https://electronics.stackexchange.com/questions/83354/calculate-distance-from-rssi
# https://stackoverflow.com/questions/4357799/convert-rssi-to-distance
# https://iotandelectronics.wordpress.com/2016/10/07/how-to-calculate-distance-from-the-rssi-value-of-the-ble-beacon/
# https://math.stackexchange.com/a/1033561/396153
# http://ambrnet.com/TrigoCalc/Circles2/circle2intersection/CircleCircleIntersection.htm

#%%
import math

import numpy as np
from numpy import sqrt, dot, cross
from numpy.linalg import norm
import pandas as pd
import plotly.express as px

data_file = "../server/data-2023-08-06-wifi-1.csv"

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

px.scatter_3d(
    netsummary_flat,
    x='src',
    y='dst',
    z='dist|mean',
    error_z='dist|std',
    color='dist|mean',
    category_orders={
        'src': uids,
        'dst': uids,
    }
).update_traces(error_z_color="black")

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
finals.to_csv('wifi-1.csv', index=False)

# px.bar(finals, 'edge', 'dist', error_y='err')
px.bar(finals, 'edge', 'dist')
#%% 1d
locs = {}

a, b, c = uids[3], uids[1], uids[2]
print('Using points as base plane:', a, b, c)
# assume first point at origin
locs[a] = np.array([0, 0, 0])
# assume second point in positive x direction
a_to_b = finals[finals['edge'] == '-'.join(sorted([a, b]))]['dist'].iloc[0]
locs[b] = np.array([a_to_b, 0, 0])
# assume third point in positive y direction
a_to_c = finals[finals['edge'] == '-'.join(sorted([a, c]))]['dist'].iloc[0]
b_to_c = finals[finals['edge'] == '-'.join(sorted([b, c]))]['dist'].iloc[0]
c_x = (a_to_c ** 2 - b_to_c ** 2 + a_to_b ** 2) / (2 * a_to_b)
c_y = math.sqrt(a_to_c ** 2 - c_x ** 2)
locs[c] = np.array([c_x, c_y, 0])

# find remaining points

# https://stackoverflow.com/a/18654302/8305404
# Find the intersection of three spheres
# P1,P2,P3 are the centers, r1,r2,r3 are the radii
# Implementaton based on Wikipedia Trilateration article.
def trilaterate(P1,P2,P3,r1,r2,r3):
    temp1 = P2-P1
    e_x = temp1/norm(temp1)
    temp2 = P3-P1
    i = dot(e_x,temp2)
    temp3 = temp2 - i*e_x
    e_y = temp3/norm(temp3)
    e_z = cross(e_x,e_y)
    d = norm(P2-P1)
    j = dot(e_y,temp2)
    x = (r1*r1 - r2*r2 + d*d) / (2*d)
    y = (r1*r1 - r3*r3 -2*i*x + i*i + j*j) / (2*j)
    temp4 = r1*r1 - x*x - y*y
    if temp4<0:
        raise Exception("The three spheres do not intersect!")
    z = sqrt(temp4)
    p_12_a = P1 + x*e_x + y*e_y + z*e_z
    p_12_b = P1 + x*e_x + y*e_y - z*e_z
    return p_12_a, p_12_b

for p in uids:
    if p in locs: continue
    print('finding point', p)
    a_to_p = finals[finals['edge'] == '-'.join(sorted([a, p]))]['dist'].iloc[0]
    b_to_p = finals[finals['edge'] == '-'.join(sorted([b, p]))]['dist'].iloc[0]
    c_to_p = finals[finals['edge'] == '-'.join(sorted([c, p]))]['dist'].iloc[0]
    opt1, opt2 = trilaterate(locs[a], locs[b], locs[c], a_to_p, b_to_p, c_to_p)
    locs[p] = opt1

locs
#%%