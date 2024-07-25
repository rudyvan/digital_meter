#!/usr/bin/python3

"""This is the configuration file for the digital meter project, please customize to your situation."""

# Change your serial port here:
serial_port = '/dev/ttyUSB0'

socket_info = {
    "remote_ips":  ["192.168.15.89"], # hosts able to give instructions to the meter
    "server_port": 8080,              # port for the digital meter server
    "dest_ip": "192.168.15.89",       # destination ip for meter data and notifications
    "dest_port": 8080,                # destination port for meter data and notifications
    "ws_url": "ws://{dest_ip}:{dest_port}/ws"}  # websocket url

vehicle_info = {
    "car1": {
        "name": "Audi e-tron Q4",
        "capacity": 75,
        "max_power": 11,
        "charge_rate": 1,
        "min_charge": 20,
        "max_charge": 80,
        "min_discharge": 20,
        "max_discharge": 80,
        "charge_efficiency": 0.9,
        "discharge_efficiency": 0.9},
    "car2": {
        "name": "Tesla Model 3",
        "capacity": 75,
        "max_power": 11,
        "charge_rate": 1,
        "min_discharge": 20,
        "max_discharge": 80,
        "charge_efficiency": 0.9,
        "discharge_efficiency": 0.9}
}

cable_info = {
    "cable_main": {
        "name": "NRGKick Main 22kW",
        "ip": "192.168.15.216",
        "port": 8765,
        "uuid": "56adc033-fbe0-40b1-93cc-513b63c78c73",
        "serial": "6241023",
        "pin": "",
        "max_power": 22,
        "charge_rate": 1},
    "cable_backup": {
        "name": "NRGKick Backup 22kW",
        "ip": "192.168.15.231",
        "port": 8765,
        "uuid": "",
        "serial": "2021023",
        "pin": "",
        "max_power": 11,
        "charge_rate": 1}
}

battery_info = {

}