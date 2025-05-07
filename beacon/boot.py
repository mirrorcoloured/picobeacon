import time

import network
from beacon_bits import (
    connect_to_known_network,
    get_uid,
    make_ap,
    onboard_led,
    scan_networks,
)

uid = get_uid()
print("My UID", uid)

print("Enabling WLAN")
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

print("Connecting to home network")
connect_to_known_network(wlan)

for i in range(3):
    onboard_led.on()
    time.sleep_ms(100)
    onboard_led.off()
    time.sleep_ms(100)

print("Starting WebREPL")
import webrepl

webrepl.stop()
webrepl.start()

print("Starting main in 10s")
import time

time.sleep(10)
import main
