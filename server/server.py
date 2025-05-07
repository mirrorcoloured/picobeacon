import datetime
import json
import os
import time

from flask import Flask, request

app = Flask(__name__)

today = datetime.date.today().isoformat()
experiment = "ble-2"


@app.route("/", methods=["GET"])
def home():
    print("Got home request")
    return "Hi I am server", 200


def flatten_obj(
    obj: any, delimiter: str = "-", md: dict = {}, path: list = []
) -> dict[str, any]:
    """Turns a nested dict into a flat dict by concatenating traversal keys"""
    if type(obj) == dict:
        for k, v in obj.items():
            flatten_obj(v, delimiter, md, path + [str(k)])
    elif type(obj) == list:
        for i, o in enumerate(obj):
            flatten_obj(o, delimiter, md, path + [str(i)])
    else:
        md[delimiter.join(path)] = obj
    return md


def wifi_beacon_to_lines(data):
    # yield json.dumps(data)
    for network in data["networks"]:
        if network["ssid"][:7] in ["beacon-", "Firelin"]:
            data_row = ",".join(
                [
                    str(time.time()),
                    str(data["time"]),
                    str(data["uid"]),
                    str(network["ssid"]),
                    str(network["bssid"]),
                    str(network["rssi"]),
                ]
            )
            yield (data_row)


def ble_beacon_to_lines(data):
    # yield json.dumps(data)
    for network in data["networks"]:
        data_row = ",".join(
            [
                str(time.time()),
                str(data["time"]),
                str(data["uid"]),
                str(network["name"]),
                str(network["device"]),
                str(network["rssi"]),
                str(network["services"]),
                str(network["manufacturer"]),
                str(network["resp_data"]),
                str(network["adv_data"]),
            ]
        )
        yield (data_row)


sleep_request = 10


@app.route("/log_data", methods=["POST"])
def log_data():
    data = json.loads(request.data.decode())
    print("Message from device", data["uid"])

    filename = f"data-{today}-{experiment}.csv"
    # headers = ['stime', 'ctime', 'uid', 'ssid', 'bssid', 'rssi']
    headers = [
        "stime",
        "ctime",
        "uid",
        "name",
        "device",
        "rssi",
        "services",
        "manufacturer",
        "resp_data",
        "adv_data",
    ]

    if not os.path.exists(filename):
        with open(filename, "w") as file:
            file.write(",".join(headers) + "\n")
    with open(filename, "a") as file:
        # for line in wifi_beacon_to_lines(data):
        for line in ble_beacon_to_lines(data):
            file.write(line + "\n")

    return {"sleep_request": sleep_request}, 200


if __name__ == "__main__":
    # app.run(host="0.0.0.0", debug=True)
    app.run(host="0.0.0.0")
