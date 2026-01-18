#!/usr/bin/python3

"""This is the configuration file for the digital meter project, please customize to your situation."""

# Change your serial port here:
serial_port = '/dev/ttyUSB0'

socket_info = {
    # make this empty if you don't have a remote socket server to connect to
    "remote_ips":  ["192.168.15.130", "192.168.15.38", "192.168.15.35"],  # hosts able to give instructions to the meter
    "server_port": 8081,               # port for the digital meter server
    "ws_ip": "192.168.15.38",          # destination ip for meter data
    "dest_port": 8081,                 # destination port for meter data and notifications
    "update_freq": 30,                 # update frequency in seconds
    "ws_url": "ws://{ip}:{port}/ws"}   # websocket url


# NRG Kick cables
cable_info = {
    # ensure the local api is enabled with the json variant (not modbus)
    "cable_main": {
        "name": "NRGKick Main 22kW",
        "ip": "192.168.15.216",
        "end_points": ["info", "control", "values"],
        "port": 8765,
        "uuid": "56adc033-fbe0-40b1-93cc-513b63c78c73",
        "serial": "6241023",
        "pin": "",
        "max_power": 22,
        "charge_rate": 1},
    "cable_backup": {
        "name": "NRGKick Backup 22kW",
        "ip": "192.168.15.231",
        "end_points": ["info", "control", "values"],
        "port": 8765,
        "uuid": "",
        "serial": "2021023",
        "pin": "",
        "max_power": 11,
        "charge_rate": 1}
}

# NRG Kick control json
# is used with the control endpoint to set the charge current
cable_control_json = {
    "current_set": 0,    # charge current in ampere
    "charge_pause": 0,   # 0=charge, 1=pause
    "energy_limit": 0,   # energy limit in Wh (Watt Hours)
    "phase_count": 3     # 1=1 phase, 2=2 phase, 3=3 phase
}

battery_info = {

}

# client specific mapping for web_socket communications purposes
ths_map = {
    "electricity_mains^fluvius_night": "kW_night",
    "electricity_mains^fluvius_night^sensor": "kW_plus",
    "electricity_mains^fluvius_night^minus_meter": "kwH_night_min",
    "electricity_mains^fluvius_night^plus_meter": "kwH_night_plus",
    "electricity_mains^fluvius_day": "kW_day",
    "electricity_mains^fluvius_day^sensor": "kW_plus",
    "electricity_mains^fluvius_day^minus_meter": "kwH_day_min",
    "electricity_mains^fluvius_day^plus_meter": "kwH_day_plus",
    "gas^purchased_gas": "gas_meter",
    "gas^purchased_gas^cooking": "",
    "gas^purchased_gas^heating": "",
    "domestic_water^pidpa": "water_meter",
}