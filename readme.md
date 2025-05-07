# Setup

## WebREPL setup
1. Create `nets.json` in the `beacon/` folder with contents like:
```json
[
    {
        "ssid": "YOURSSID",
        "password": "YOURPASSWORD"
    }
]
```
2. Update `webrepl_cfg.py` with a new password (4-9 characters)
3. Plug a pico into this computer and transfer the contents of `beacon/` onto it (using Thonny or the MicroPico extension in VS Code)
4. Restart the pico. It will run `boot.py` which will connect to the wifi in `nets.json` and start the webrepl server. It should also print its IP address.
5. You can now connect to the webrepl server at the IP address printed in step 4 via a browser (ex. `http://192.168.86.201:8266`).

## Beacon setup
1. Run `server.py` to start listening for picobeacons
2. Update `serverinfo.py` with the correct URL of the listening server
3. Update `main.py` to import either `beacon` or `beacon_ble`
4. Upload `serverinfo.py` and `main.py` to the pico via webrepl or via usb if still connected


# Tips

- Using WebREPL, check file contents in-place with:
```python
from beacon_bits import print_file_contents                                                                                                       
print_file_contents("main.py")
```

# Data

## WIFI
Core data from beacon
**stime** - server `time.time()`
**ctime** - pico `time.time()`
**uid** - pico uid
**mac** - pico wifi mac address
Properties associated with each device detected from this beacon
**ssid** - ssid of detected device
**bssid** - bssid of detected device
**channel** - channel of detected device network
**rssi** - signal strength of detected device network
**authmode** - [0: open, 1: WEP, 2: WPA-PSK, 3: WPA2-PSK, 4: WPA/WPA2-PSK]
**hidden** - [0: visible, 1: hidden]

## BLE
Core data from beacon
**stime** - server `time.time()`
**ctime** - pico `time.time()`
**uid** - pico uid
**mac** - pico ble mac address
Properties associated with each device detected from this beacon
**name** - detected device name (`device.name()`)
**device** - detected device address (`device.device.addr_hex()`)
**rssi** - strength of signal to device(`device.rssi`)
**services** - list of services (`device.services()`)
**manufacturer** - list of manufacturers (`device.manufacturer()`)
**resp_data** - extra data from detected device (`device.resp_data`)
**adv_data** - extra data from detected device (`device.adv_data`)

# How to do
https://iotandelectronics.wordpress.com/2016/10/07/how-to-calculate-distance-from-the-rssi-value-of-the-ble-beacon/

https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5750706/

https://jesit.springeropen.com/articles/10.1186/s43067-023-00075-4

https://ieeexplore.ieee.org/abstract/document/7808286

# BLE for pico

Bluetooth available from latest (as of 2023-08-31) beta firmware at: https://www.raspberrypi.com/documentation/microcontrollers/micropython.html

https://www.raspberrypi.com/news/new-functionality-bluetooth-for-pico-w/

https://datasheets.raspberrypi.com/picow/connecting-to-the-internet-with-pico-w.pdf

https://github.com/raspberrypi/pico-micropython-examples/tree/master/bluetooth

https://github.com/micropython/micropython-lib/tree/master/micropython/bluetooth/aioble/examples
