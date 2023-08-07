import network
import time
import ubinascii
import machine
import random
import urequests
import json

# Disable power-saving mode to increase responsiveness
# wlan.config(pm = 0xa11140)

onboard_led = machine.Pin("LED", machine.Pin.OUT)

# enable wlan
print("Enabling WLAN")
wlan = network.WLAN(network.STA_IF)
wlan.active(True)


# connect to local network for logging
print("Connecting to home network")
NETWORK_FILE = 'nets.json'
def load_network_credentials():
    with open(NETWORK_FILE, 'r') as f:
        return json.loads(f.read())
my_creds = load_network_credentials()[0]
wlan.connect(my_creds['ssid'], my_creds['password'])

status_names = {
    network.STAT_CONNECTING: 'STAT_CONNECTING',   
    network.STAT_CONNECT_FAIL: 'STAT_CONNECT_FAIL',  
    network.STAT_GOT_IP: 'STAT_GOT_IP',       
    network.STAT_IDLE: 'STAT_IDLE',         
    network.STAT_NO_AP_FOUND: 'STAT_NO_AP_FOUND',  
    network.STAT_WRONG_PASSWORD: 'STAT_WRONG_PASSWORD'
}

max_wait = 20
while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    print("Waiting for connection...")
    onboard_led.on()
    time.sleep_ms(500)
    onboard_led.off()
    time.sleep_ms(500)

if wlan.status() != 3:
    print("Network connection failed", status_names.get(wlan.status(), "Unknown code: " + str(wlan.status())))
    while True:
        onboard_led.on()
        time.sleep_ms(100)
        onboard_led.off()
        time.sleep_ms(100)
else:
    print("Connected!")
    status = wlan.ifconfig()
    print("IP: ", status[0])


# enable access point
print("Enabling access point")
uid = ubinascii.hexlify(machine.unique_id(),":").decode()
mac_address = ubinascii.hexlify(wlan.config('mac'),':').decode()
print("uid", uid)
print("mac", mac_address)
ssid = 'beacon-{}'.format(mac_address)
password = ''.join([chr(random.randint(97, 122)) for i in range(16)])

ap = network.WLAN(network.AP_IF)
ap.config(essid=ssid, password=password)
ap.active(True)


# scan networks
def get_networks():
    enum_authmodes = {
        0: 'open',
        1: 'WEP',
        2: 'WPA-PSK',
        3: 'WPA2-PSK',
        4: 'WPA/WPA2-PSK',
    }
    enum_visibility = {
        0: 'visible',
        1: 'hidden',
    }
    networks = []
    for network_info in sorted(wlan.scan(), key=lambda x: x[3], reverse=True):
        ssid, bssid, channel, rssi, authmode, hidden = network_info
        networks.append({
            'ssid': ssid.decode("utf-8"),
            'bssid': ubinascii.hexlify(bssid).decode("utf-8"),
            'channel': channel,
            'rssi': rssi,
            'authmode': enum_authmodes.get(authmode, authmode),
            'hidden': enum_visibility.get(hidden, hidden),
        })
    return networks

print("Starting scan loop")
server_url = "http://192.168.1.52:5000/log_data"
sleep_time = 10
while True:
    try:
        networks = get_networks()

        data = {
            "time": time.time(),
            "mac": mac_address,
            "networks": networks,
            }
        response = urequests.post(server_url, data=json.dumps(data).encode())
        print(response.content)
        response_json = json.loads(response.content.decode())

        sleep_time = response_json.get('sleep_request', 10)
    except Exception as e:
        print(e)

    time.sleep(sleep_time)

