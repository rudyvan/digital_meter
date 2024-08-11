#!/usr/bin/python3

"""This is the configuration file for the digital meter project, please customize to your situation."""

# Change your serial port here:
serial_port = '/dev/ttyUSB0'

socket_info = {
    # make this empty if you don't have a remote socket server to connect to
    "remote_ips":  ["192.168.15.89", "192.168.15.38", "192.168.15.35"],  # hosts able to give instructions to the meter
    "server_port": 8081,               # port for the digital meter server
    "ws_ip": "192.168.15.38",          # destination ip for meter data
    "dest_port": 8081,                 # destination port for meter data and notifications
    "update_freq": 30,                 # update frequency in seconds
    "ws_url": "ws://{ip}:{port}/ws"}   # websocket url

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

# client specific mapping for web_socket communications purposes
ths_map = {
    "electricity^fluvius_night": "kW_night",
    "electricity^fluvius_night^sensor": "kW_plus",
    "electricity^fluvius_night^minus_meter": "kwH_night_min",
    "electricity^fluvius_night^plus_meter": "kwH_night_plus",
    "electricity^fluvius_day": "kW_day",
    "electricity^fluvius_day^sensor": "kW_plus",
    "electricity^fluvius_day^minus_meter": "kwH_day_min",
    "electricity^fluvius_day^plus_meter": "kwH_day_plus",
    "gas^purchased_gas": "gas_meter",
    "domestic_water^pidpa": "water_meter",
}