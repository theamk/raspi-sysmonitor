#!/usr/bin/python3 -B
import time
import os
import sys
import subprocess

sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lcd_5110'))
from lcd5110 import LCD5110

import RPi.GPIO as GPIO
import wpa_info

# A poweoff button support: the button should be connected between this pin 
# and GND. It's a board pin number because LCD library sets board mode
POWERDN_PIN = 22
# To prevent accidental activation, the button must be held for correct number of
# cycles, here is that range:
POWERDOWN_ARM_CNT   = 10
POWEDOWN_CANCEL_CNT = 15

def short_timestamp():
    return time.strftime('%b%d %H:%M:%S', time.localtime())

def main():
    lcd = LCD5110()
    lcd.backlight(True)

    lcd.clear()

    wifi_info = wpa_info.WifiWPAInfo()
    sys.stdout.flush()
    update_count = 0
    btn_hit_count = 0

    if POWERDN_PIN is not None:
        GPIO.setup([POWERDN_PIN], GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def update_data(wifi):
        with open('/proc/uptime', 'r') as f:
            uptime_s = float(f.read().split()[0])

        return [
            os.uname().nodename,  # hostname
            (wifi.status or wifi.ip)[-14:],
            "%4s %s" % (wifi.rssi or "??", wifi.ssid or '<no-ssid>'),
            "",  # TODO put CPU/disk usag here
            time.strftime("%b%d %H:%M UP", time.localtime(time.time() - uptime_s)),
            short_timestamp()
        ]

    # display is 84x48, font is 6x8 -> we have 6 lines, 14 chars each
    last_lines = [''] * 6
    last_wifi = None
    try:
        while True:
            wifi = wifi_info.poll()

            new_lines = update_data(wifi)

            if POWERDN_PIN is not None and not GPIO.input(POWERDN_PIN):
                # button hit! Increase the counter and let user know.
                if not btn_hit_count:
                    print('button pressed')
                btn_hit_count += 1
                if btn_hit_count < POWERDOWN_ARM_CNT:
                    new_lines[0] = 'Poweroff? %d' % (POWERDOWN_ARM_CNT - btn_hit_count)
                elif btn_hit_count < POWEDOWN_CANCEL_CNT:
                    new_lines[0] = 'RELEASE to off'
                elif btn_hit_count < 3 * POWEDOWN_CANCEL_CNT:
                    new_lines[0] = 'pwroff CANCEL'
                # else button is stuck, so stop showing anything...
            elif POWERDOWN_ARM_CNT <= btn_hit_count < POWEDOWN_CANCEL_CNT:
                # button released while armed -- go do shutdown
                print('Button released at', btn_hit_count, ', starting shutdown')
                btn_hit_count = 0
                sys.stdout.flush()
                new_lines[0] = 'SHUTDOWN!'
                subprocess.Popen("sudo poweroff", shell=True)
            elif btn_hit_count:
                print('Button released at', btn_hit_count)
                btn_hit_count = 0

            update_count += 1
            if (update_count % 30) == 0:
                last_lines = [''] * 6
                lcd.reinit()

            for i, (old, new) in enumerate(zip(last_lines, new_lines)):
                new = new[:14].ljust(14)
                if new != old:
                    lcd.inverse(i in [0, 5])
                    lcd.cursor(i + 1, 1)
                    lcd.printStr(new)
                    last_lines[i] = new

            wifi = wifi._replace(rssi=None)   # Do not log changes in RSSI
            if wifi != last_wifi:
                print('wifi info', update_count, wifi)
                last_wifi = wifi
            if update_count == 1:
                print('first cycle done')
            sys.stdout.flush()
            # For perf testing, comment out line below and uncomment one below it, then run:
            #    python3 -mcProfile -scumtime ./syslcd.py
            time.sleep(1)
            # if update_count > 100: break
    except KeyboardInterrupt:
        print('interrupted!')
        lcd.inverse(False)
        lcd.clear()
        lcd.cursor(1, 1)
        lcd.printStr("SHUTTING DOWN")
        lcd.cursor(6, 1)
        lcd.printStr(short_timestamp())


if __name__ == '__main__':
    main()
