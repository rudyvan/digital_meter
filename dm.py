#!/usr/bin/python3

# This script will read and process data from serial P1 port of the digital meter as used in Belgium.
# https://github.com/rudyvan/digital_meter

from config import serial_port, socket_info

from dm_app import BusMeter

from app import pi

from rich.traceback import install

install(width=180, extra_lines=10, show_locals=True)

pi.install(socket_info)

if __name__ == '__main__':
    BusMeter(serial_port).run()