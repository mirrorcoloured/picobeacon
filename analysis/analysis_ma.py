import copy
from pprint import pprint
import os

import numpy as np
import pandas as pd
import plotly.express as px

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
df[f"{src_column}_{dst_column}"] = (df[src_column] + "_" + df[dst_column]).str.replace(":", "")
df[f"{dst_column}_{src_column}"] = (df[dst_column] + "_" + df[src_column]).str.replace(":", "")
df["link"] = df.apply(lambda df: get_link(df[src_column], df[dst_column], prefix), axis=1)
df.head(2)

# Explore
df.head(2).T
df[src_column].value_counts()
df[dst_column].value_counts()

# Compare direction
(
    df.groupby(f"{src_column}_{dst_column}")
    .agg({"dist": [np.mean, np.std]})
    .merge(
        df.groupby(f"{dst_column}_{src_column}").agg({"dist": [np.mean, np.std]}),
        left_on=f"{src_column}_{dst_column}",
        right_on=f"{dst_column}_{src_column}",
    )
)

# Groupby
stats = df.groupby("link").agg({"dist": [np.mean, np.std, len]})
stats["sd_norm"] = stats["dist"]["std"] / stats["dist"]["mean"]

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

# Compute mean abs signal
dist_df = df.groupby("link").apply(lambda df: df.dist.abs().mean()).reset_index()
dist_df.columns = ["link", "dist"]
dist_df["source"] = dist_df["link"].apply(lambda s: s.split("_")[0])
dist_df["target"] = dist_df["link"].apply(lambda s: s.split("_")[1])
dist_df

pos_dict = {node: {"x": 0, "y": 0, "z": 0} for node in {*dist_df["source"], *dist_df["target"]}}

dist_df = dist_df.set_index(["source", "target"])

# TODO continue here

# Override with fixed values and high values for flex values
pos_dict["a6"]["x"] = dist_df.loc[("a0", "a6")].dist
pos_dict["a8"] = {"x": 100, "y": 100, "z": 0}
pos_dict["aa"] = {"x": 100, "y": 100, "z": 100}


def compute_dist(source_point, target_point):
    return (
        (source_point["x"] - target_point["x"]) ** 2
        + (source_point["y"] - target_point["y"]) ** 2
        + (source_point["z"] - target_point["z"]) ** 2
    ) ** 0.5


def cost_function(dist_df, pos_dict):
    sum_sqr = 0
    for source, target in dist_df.index:
        dist = dist_df.loc[(source, target)].dist
        act_dist = compute_dist(pos_dict[source], pos_dict[target])
        sum_sqr = sum_sqr + (act_dist - dist) ** 2
    return sum_sqr**0.5


moveable_points = [
    ("a8", "x"),
    ("a8", "y"),
    ("aa", "x"),
    ("aa", "y"),
    ("aa", "z"),
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
                    "mp": mp,
                    "cost": cost,
                    "pos_dict": copy_dict,
                }
            )
    best_option = sorted(options, key=lambda d: d["cost"])[0]
    best_cost = best_option["cost"]
    if i % 10 == 0:
        print(best_cost)
    if best_cost > last_cost:
        break
    pos_dict = best_option["pos_dict"]
    last_cost = best_cost
    i = i + 1

pprint(pos_dict)
point_df = pd.DataFrame(pos_dict).T

px.scatter_3d(point_df, x="x", y="y", z="z")
