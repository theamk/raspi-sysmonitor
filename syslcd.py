#!/usr/bin/python3 -B
import time
import os
import sys

sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lcd_5110'))
from lcd5110 import LCD5110

import wpa_info

def short_timestamp():
    return time.strftime('%b%d %H:%M:%S', time.localtime())

def main():
    lcd = LCD5110()
    lcd.backlight(True)

    lcd.clear()

    wifi_info = wpa_info.WifiWPAInfo()
    sys.stdout.flush()
    #os.system("gpio readall")
    update_count = 0



    def update_data(wifi):
        with open('/proc/uptime', 'r') as f:
            uptime_s = float(f.read().split()[0])

        return [
            os.uname().nodename,  # hostname
            (wifi.status or wifi.ip)[-14:],
            "%4s %s" % (wifi.rssi or "??", wifi.ssid or '<no-ssid>'),
            "",  # TODO unused?
            time.strftime("Up %b%d %H:%M", time.localtime(time.time() - uptime_s)),
            short_timestamp()
        ]

    # display is 84x48, font is 6x8 -> we have 6 lines, 14 chars each
    last_lines = [''] * 6
    last_wifi = None
    try:
        while True:
            wifi = wifi_info.poll()

            new_lines = update_data(wifi)
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
