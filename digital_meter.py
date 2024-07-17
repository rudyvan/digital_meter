#!/usr/bin/python3

# This script will read data from serial connected to the digital meter P1 port

# Created by Jens Depuydt
# https://www.jensd.be
# https://github.com/jensdepuydt


from rich.traceback import install

from dm_app import BusMeter

install(width=180, extra_lines=10, show_locals=True)

# Change your serial port here:
serial_port = '/dev/ttyUSB0'

if __name__ == '__main__':
    BusMeter(serial_port).run()