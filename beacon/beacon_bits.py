import json
import time
import network
import machine
import ubinascii
import aioble

onboard_led = machine.Pin("LED", machine.Pin.OUT)

def get_uid():
    return ubinascii.hexlify(machine.unique_id(),":").decode()

def connect_to_known_network(wlan):
    # connect to local network for logging
    NETWORK_FILE = 'nets.json'
    def load_network_credentials():
        with open(NETWORK_FILE, 'r') as f:
            return json.loads(f.read())
    
    # TODO if first network isn't found, try next, etc.
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

def make_ap(ssid, password):
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=ssid, password=password)
    ap.active(True)
    return ap

def scan_networks(wlan):
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

def get_broadcast_function(name, services, appearance, interval):
    for service in services:
        aioble.register_services(aioble.Service(service))

    async def ble_broadcast():
        print("Broadcasting as a peripheral")
        while True:
            async with await aioble.advertise(
                interval,
                name=name,
                services=services,
                appearance=appearance,
            ) as connection:
                print("Connection from", connection.device)
                await connection.disconnected()
    return ble_broadcast

async def ble_scan():
    sensors = []
    seen = []
    async with aioble.scan(5000, interval_us=30000, window_us=30000, active=True) as scanner:
        async for result in scanner:
            if result.name() in seen: continue
            sensors.append(result)
            seen.append(result.name())
    return sensors