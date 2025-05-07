import time

import machine

onboard_led = machine.Pin("LED", machine.Pin.OUT)

while True:
    onboard_led.on()
    time.sleep_ms(300)
    onboard_led.off()
    time.sleep_ms(300)
