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
