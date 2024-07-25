#!/usr/bin/python3

# This script will manage the charging of electrical vehicles.


# from ev_app import ElectricVehicle

from rich.traceback import install

install(width=180, extra_lines=10, show_locals=True)

vehicle_info = {

}

socket_info = {
    "remote_ips":  ["192.168.15.89"], # hosts able to give instructions to the meter
    "server_port": 8080,              # port for the digital meter server
    "dest_ip": "192.168.15.89",       # destination ip for meter data and notifications
    "dest_port": 8080,                # destination port for meter data and notifications
    "ws_url": "ws://{dest_ip}:{dest_port}/ws"}  # websocket url

if __name__ == '__main__':
    print("electrical vehicle still to make")
    i = input("press enter to continue")
    # ElectricalVehicle(socket_info, vehicle_info).run()