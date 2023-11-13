import network
import time
import ubinascii
import machine
import random
import urequests
import json

from beacon_bits import get_uid, connect_to_known_network, make_ap, scan_networks

uid = get_uid()
print("My UID", uid)

print("Enabling WLAN")
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

print("Connecting to home network")
connect_to_known_network(wlan)

print("Enabling access point")
ssid = 'beacon-{}'.format(uid)
password = ''.join([chr(random.randint(97, 122)) for i in range(16)])
ap = make_ap(ssid, password)

def report_networks(wlan):
    server_url = "http://192.168.1.52:5000/log_data"

    networks = scan_networks(wlan)

    data = {
        "time": time.time(),
        "uid": uid,
        "networks": networks,
        }
    response = urequests.post(server_url, data=json.dumps(data).encode())
    response_json = json.loads(response.content.decode())

    global sleep_time
    sleep_time = response_json.get('sleep_request', sleep_time)

sleep_time = 10
print("Starting main loop")
while True:
    try:
        report_networks(wlan)
        time.sleep(sleep_time)
    except Exception as e:
        print(e)
