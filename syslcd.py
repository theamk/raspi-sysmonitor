#!/usr/bin/python
import time
import os
import sys

sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lcd_5110'))
from lcd5110 import LCD5110

def short_timestamp():
    return time.strftime('%b%d %H:%M:%S', time.localtime())

def main():
    lcd = LCD5110()
    lcd.backlight(True)

    lcd.clear()

    print("init ready")
    sys.stdout.flush()
    #os.system("gpio readall")
    update_count = 0

    def update_data():
          return [
             "System monitor",
             str(update_count),
             "3",
             "4",
             "5",
             short_timestamp()
          ]

    # display is 84x48, font is 6x8 -> we have 6 lines, 14 chars each
    last_lines = [''] * 6
    try:
        while True:
            new_lines = update_data()
            update_count += 1
            if (update_count % 10) == 0:
                last_lines = [''] * 6
                lcd.reinit()
                print('reinit')

            for i, (old, new) in enumerate(zip(last_lines, new_lines)):
                new = new[:14].ljust(14)
                if new != old:
                    lcd.inverse(i in [0, 5])
                    lcd.cursor(i + 1, 1)
                    lcd.printStr(new)
                    last_lines[i] = new

            sys.stdout.flush()
            time.sleep(1)
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
