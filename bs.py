#!/usr/bin/python3

# This script will manage the storage of electricity in batteries.


# from bs_app import BatteryStorage

from config import battery_info, socket_info

from rich.traceback import install

install(width=180, extra_lines=10, show_locals=True)


if __name__ == '__main__':
    print("battery storage yet to make")
    i = input("press enter to continue")
    # BatteryStorage(socket_info, battery_info).run()