import json
import random
import time

import machine
import network
import ubinascii
import urequests
from beacon_bits import (
    connect_to_known_network,
    get_uid,
    get_wifi_mac,
    make_ap,
    scan_networks,
)
from serverinfo import server_url

uid = get_uid()
mywifimac = get_wifi_mac()
print("My UID", uid)

print("Enabling WLAN")
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

print("Connecting to home network")
connect_to_known_network(wlan)

print("Enabling access point")
ssid = "beacon-{}".format(mywifimac)
password = "".join([chr(random.randint(97, 122)) for i in range(16)])
ap = make_ap(ssid, password)


def report_networks(wlan):
    networks = scan_networks(wlan)

    data = {
        "time": time.time(),
        "uid": uid,
        "mywifimac": mywifimac,
        "networks": networks,
    }
    response = urequests.post(
        f"{server_url}/log_data_wifi", data=json.dumps(data).encode()
    )
    response_json = json.loads(response.content.decode())

    global sleep_time
    sleep_time = response_json.get("sleep_request", sleep_time)


sleep_time = 10
print("Starting main loop")
while True:
    try:
        report_networks(wlan)
        time.sleep(sleep_time)
    except Exception as e:
        print(e)
