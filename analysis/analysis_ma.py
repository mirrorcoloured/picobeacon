# %% import packages and data
import copy
from pprint import pprint
import os
from itertools import product

# from functools import reduce

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import networkx as nx

datasets = [f for f in os.listdir("../server/") if os.path.splitext(f)[1] == ".csv"]
print(datasets)

# data_file = "../server/data-2023-08-06-wifi-1.csv"
# src_column = "mac"
# dst_column = "bssid"
# sig_column = "rssi"
# prefix = "28cdc1026b"

data_file = "../server/data-2023-11-12-ble-1.csv"
src_column = "uid"
dst_column = "name"
sig_column = "rssi"
prefix = "e6614103e7"
ab_column = f"{src_column}_{dst_column}"
ba_column = f"{dst_column}_{src_column}"

# %% format data
df = pd.read_csv(data_file, encoding="utf-8")
df.head(2)

one_m_rssi = -40
N = 4
df["dist"] = df[sig_column].apply(lambda val: 10 ** ((one_m_rssi - val) / (10 * N)))
df = df[df["name"] != "None"]


def get_link(source, target, prefix=""):
    return "_".join(
        sorted(
            [
                source.replace(":", "").replace(prefix, ""),
                target.replace(":", "").replace(prefix, ""),
            ]
        )
    )


# Add columns
df[ab_column] = (df[src_column] + "_" + df[dst_column]).str.replace(":", "")
df[ba_column] = (df[dst_column] + "_" + df[src_column]).str.replace(":", "")
df["link"] = df.apply(lambda df: get_link(df[src_column], df[dst_column], prefix), axis=1)
df.head(2)

# Explore
df.head(2).T
df[src_column].value_counts()
df[dst_column].value_counts()

# Compare direction
# a = df.groupby(ab_column).agg({"dist": [np.mean, np.std]})
# b = df.groupby(ba_column).agg({"dist": [np.mean, np.std]})
# a.merge(
#     b,
#     left_on=ab_column,
#     right_on=ba_column,
# )

# get stats to remove outliers
stats = df.groupby("link").agg({"dist": [np.mean, np.std, len]})

px.scatter(
    x=stats[("dist", "mean")],
    y=stats[("dist", "std")],
    hover_name=stats.index,
    color=stats[("dist", "len")],
)

# # Remove targets with insufficient data
# keepers = stats[stats["dist"]["len"] > 100].index
# df = df[df["link"].isin(keepers)]

# # Remove targets with high deviation
# keepers = stats[stats["sd_norm"] > 10].index
# df = df[df["link"].isin(keepers)]

# Remove targets with high distance
keepers = stats[stats["dist"]["mean"] < 10].index
df = df[df["link"].isin(keepers)]

# compile main df
dist_df = df.groupby("link").agg({"dist": [np.mean, np.std]}).reset_index()
dist_df.columns = ["link", "dist", "error"]
dist_df["source"] = dist_df["link"].apply(lambda s: s.split("_")[0])
dist_df["target"] = dist_df["link"].apply(lambda s: s.split("_")[1])

nodes = list({*dist_df["source"], *dist_df["target"]})
dist_df.set_index(["source", "target"], inplace=True)

# %% choose set of three nodes that have seen each other

# make graph by standard deviation (greater edge weight is higher uncertainty)
g = nx.Graph()
for n in nodes:
    g.add_node(n)
for src, dst in dist_df.index:
    g.add_edge(
        src,
        dst,
        distance=dist_df.loc[(src, dst)].dist,
        error=dist_df.loc[(src, dst)].error,
    )
nx.draw(g)
# get all 3-cycles
paths = []
for a, b, c in nx.cycle_basis(g):
    path_total = sum(
        [
            g.get_edge_data(a, b)["error"] ** 2,
            g.get_edge_data(b, c)["error"] ** 2,
            g.get_edge_data(c, a)["error"] ** 2,
        ]
    )
    paths.append(((a, b, c), path_total))
# choose cycle with lowest sumsq error
paths.sort(key=lambda x: x[1])
base_plane_nodes = paths[0][0]

# %% set up initial positions


def find_third_point(ab: float, bc: float, ac: float) -> dict[str, float]:
    """Assuming a is at (0, 0) and b is at (ab, 0), calculate the position of c"""
    x = (ab**2 + ac**2 - bc**2) / (2 * ab)
    y = (ac**2 - x**2) ** 0.5
    return {"x": x, "y": y}


# initialize positions far from origin
pos_dict = {node: {"x": 100, "y": 100, "z": 100} for node in nodes}

# place three nodes in a triangle at z=0
pos_dict[base_plane_nodes[0]] = {"x": 0, "y": 0, "z": 0}

dx = g.get_edge_data(base_plane_nodes[0], base_plane_nodes[1])["distance"]
pos_dict[base_plane_nodes[1]] = {"x": dx, "y": 0, "z": 0}

point = find_third_point(
    g.get_edge_data(base_plane_nodes[0], base_plane_nodes[1])["distance"],
    g.get_edge_data(base_plane_nodes[1], base_plane_nodes[2])["distance"],
    g.get_edge_data(base_plane_nodes[0], base_plane_nodes[2])["distance"],
)
pos_dict[base_plane_nodes[2]] = {"x": point["x"], "y": point["y"], "z": 0}


def euclidean_distance(a: dict[str, float], b: dict[str, float]) -> float:
    assert len(a.keys()) == len(b.keys())
    return sum([(a[dim] - b[dim]) ** 2 for dim in a.keys()]) ** 0.5


def cost_function(dist_df, pos_dict):
    sum_sqr = 0
    for source, target in dist_df.index:
        dist = dist_df.loc[(source, target)].dist
        act_dist = euclidean_distance(pos_dict[source], pos_dict[target])
        sum_sqr = sum_sqr + (act_dist - dist) ** 2
    return sum_sqr**0.5


moveable_points = list(product(nodes, ("x", "y", "z")))

# %% solve for positions
i = 0
last_cost = 10**6
d_cost = 10**6
stall_threshold = 0.01
max_iterations = 10**4
cost_history = []
while i < max_iterations:
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
                    "mp": mp,
                    "cost": cost,
                    "pos_dict": copy_dict,
                }
            )
    best_option = sorted(options, key=lambda d: d["cost"])[0]
    best_cost = best_option["cost"]
    cost_history.append(best_cost)
    if i % 10 == 0:
        # print(best_cost)
        px.line(y=cost_history).update_layout(xaxis_title="iterations", yaxis_title="cost").show()
    if best_cost > last_cost:
        break
    pos_dict = best_option["pos_dict"]
    d_cost = last_cost - best_cost
    if d_cost < stall_threshold:
        break
    last_cost = best_cost
    i = i + 1
print("Final cost", best_cost)

# %% display final positions

point_df = pd.DataFrame(pos_dict).T
px.scatter_3d(
    point_df,
    x="x",
    y="y",
    z="z",
    text=point_df.index,
)
pprint(pos_dict)

# %%
