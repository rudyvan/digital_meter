#!/usr/bin/python3

# This script will read data from serial connected to the digital meter P1 port

# Created by Jens Depuydt
# https://www.jensd.be
# https://github.com/jensdepuydt


from dm_app import BusMeter

from rich.traceback import install

install(width=180, extra_lines=10, show_locals=True)

# Change your serial port here:
serial_port = '/dev/ttyUSB0'

socket_info = {
    "remote_ips":  ["192.168.15.89"], # hosts able to give instructions to the meter
    "server_port": 8080,              # port for the digital meter server
    "dest_ip": "192.168.15.89",       # destination ip for meter data and notifications
    "dest_port": 8080,                # destination port for meter data and notifications
    "ws_url": "ws://{dest_ip}:{dest_port}/ws"} # websocket url
if __name__ == '__main__':
    BusMeter(serial_port, socket_info).run()