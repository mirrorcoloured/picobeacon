import network
from beacon_bits import connect_to_known_network, get_uid, make_ap, scan_networks

uid = get_uid()
print("My UID", uid)

print("Enabling WLAN")
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

print("Connecting to home network")
connect_to_known_network(wlan)
