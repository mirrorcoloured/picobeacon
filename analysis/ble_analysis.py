# %%
import json
import math

import numpy as np
import pandas as pd
import plotly.express as px
from numpy import cross, dot, sqrt
from numpy.linalg import norm

data_file = "../server/data-2023-11-12-ble-1.csv"

df = pd.read_csv(data_file, encoding="utf-8")

# filter to only my beacons
df = df[df["services"] == "['UUID(0x1821)']"]

# list beacons
df.value_counts("uid")

# list unique devices
df.value_counts(["device", "name", "services"])

# %%
with open("../server/picozoo.json", "r") as f:
    zoo = json.load(f)


def uid_to_idx(uid):
    for z in zoo:
        if z["uid"] == uid:
            return z["idx"]


def uid_to_ble_mac(uid):
    for z in zoo:
        if z["uid"] == uid:
            return z["ble"]


def ble_mac_to_uid(ble_mac):
    for z in zoo:
        if z["ble"] == ble_mac:
            return z["uid"]


# %% create clean dataframe
net = pd.DataFrame()
net["time"] = df["stime"]
net["src"] = df["uid"].apply(lambda x: uid_to_idx(x))
net["dst"] = df["name"].apply(lambda x: uid_to_idx(x))
# net['dist'] = df['rssi']
one_m_rssi = -40
net["dist"] = df["rssi"].apply(lambda val: 10 ** ((one_m_rssi - val) / (10 * 2)))

# alphabetize order
uids = set(net["src"].unique().tolist())
uids.update(set(net["dst"].unique().tolist()))
uids = sorted(list(uids))

# replace with means
netsummary = net.groupby(["src", "dst"]).aggregate({"dist": ["mean", "std"]})
netsummary_flat = netsummary.reset_index()
netsummary_flat.columns = netsummary_flat.columns.map("|".join).str.strip("|")
netsummary_flat

# %% pairing mean + err
px.scatter_3d(
    netsummary_flat,
    x="src",
    y="dst",
    z="dist|mean",
    error_z="dist|std",
    color="dist|mean",
    category_orders={
        "src": uids,
        "dst": uids,
    },
).update_traces(error_z_color="black")

# %% pairings over time
px.scatter_3d(
    net,
    x="src",
    y="dst",
    z="dist",
    color="time",
    category_orders={
        "src": uids,
        "dst": uids,
    },
)

# %%
finals = []
for i in range(len(uids)):
    for j in range(i + 1, len(uids)):
        finals.append(
            {
                "a": uids[i],
                "b": uids[j],
                "edge": f"{uids[i]}-{uids[j]}",
                "dist": (
                    netsummary.loc[uids[i], uids[j]]["dist"]["mean"]
                    + netsummary.loc[uids[j], uids[i]]["dist"]["mean"]
                )
                / 2,
                "err": (
                    netsummary.loc[uids[i], uids[j]]["dist"]["std"] ** 2
                    + netsummary.loc[uids[j], uids[i]]["dist"]["std"] ** 2
                )
                / 2,
            }
        )

finals = pd.DataFrame(finals)
finals.to_csv("ble-1.csv", index=False)

# %%
