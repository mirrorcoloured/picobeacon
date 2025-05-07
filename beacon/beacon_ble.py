import json
import time

import aioble
import bluetooth
import machine
import network
import uasyncio as asyncio
import ubinascii
import urequests
from beacon_bits import (
    ble_scan,
    connect_to_known_network,
    get_broadcast_function,
    get_uid,
)
from micropython import const
from serverinfo import server_url

my_uid = get_uid()

print("Enabling WLAN")
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

print("Connecting to home network")
connect_to_known_network(wlan)

# https://btprodspecificationrefs.blob.core.windows.net/assigned-numbers/Assigned%20Number%20Types/Assigned_Numbers.pdf
_SERVICE_INDOOR_POSITIONING = bluetooth.UUID(0x1821)
# _CHARACTERISTIC_INDOOR_POSITIONING_CONFIGURATION = bluetooth.UUID(0x2AAD)
_APPEARANCE_ELECTRONIC_LABEL = const(2754)  # 0x0AC2
# _APPEARANCE_GENERIC_NETWORK_DEVICE = const(1280) # 0x0500
_ADV_INTERVAL_MS = 250_000

ble_broadcast = get_broadcast_function(
    my_uid,
    [_SERVICE_INDOOR_POSITIONING],
    _APPEARANCE_ELECTRONIC_LABEL,
    _ADV_INTERVAL_MS,
)


async def report_devices():
    sleep_time_ms = 10 * 1000

    while True:
        try:
            devices = await ble_scan()

            # filter to only devices of the right type
            # devices = [d for d in devices if _SERVICE_INDOOR_POSITIONING in d.services()]

            send_data = []
            for device in devices:
                send_data.append(
                    {
                        "name": device.name(),
                        "device": device.device.addr_hex(),
                        # 'device': {
                        #     'addr': device.device.addr,
                        #     'addr_type': device.device.addr_type,
                        #     'addr_hex': device.device.addr_hex(),
                        #     },
                        "connectable": device.connectable,
                        "rssi": device.rssi,
                        "services": [str(s) for s in device.services()],
                        "manufacturer": [str(m) for m in device.manufacturer()],
                        "resp_data": str(device.resp_data),
                        "adv_data": str(device.adv_data),
                    }
                )

            data = {
                "time": time.time(),
                "uid": my_uid,
                "networks": send_data,
            }
            response = urequests.post(server_url, data=json.dumps(data).encode())
            response_json = json.loads(response.content.decode())
            sleep_time = response_json.get("sleep_request", sleep_time_ms / 1000)
            sleep_time_ms = sleep_time * 1000

            await asyncio.sleep_ms(sleep_time_ms)
        except Exception as e:
            print(e)


async def main():
    t1 = asyncio.create_task(ble_broadcast())
    t2 = asyncio.create_task(report_devices())
    await asyncio.gather(t1, t2)


asyncio.run(main())
