#!/usr/bin/python3
# This script will manage the charging of electrical vehicles.

from time import sleep

from aiohttp import ClientSession
import asyncio

import logging
import json

from pathlib import Path

# from ev_app import ElectricVehicle
from rich import print
from rich.live import Live
from rich.text import Text
from rich.console import Console
from rich import inspect

from rich.traceback import install

install(width=180, extra_lines=10, show_locals=True)

from config import cable_info, cable_control_json

socket_info = {
    "remote_ips":  ["192.168.15.89"],  # hosts able to give instructions to the meter
    "server_port": 8080,               # port for the digital meter server
    "dest_ip": "192.168.15.89",        # destination ip for meter data and notifications
    "dest_port": 8080,                 # destination port for meter data and notifications
    "ws_url": "ws://{dest_ip}:{dest_port}/ws"}  # websocket url


# Import the audiconnectpy package.
from audiconnectpy import AudiConnect

# read the secrets from the secrets.json file located in the home directory
# should contain the following keys in "audiconnect": "username", "password", "country", "spin"
# and a list of cars in e-cars that the ev app should manage
with open(Path.home() / "secrets.json", encoding="UTF-8", mode="r") as f:
    secrets = json.loads(f.read())

async def main():
    # set the logging to debug level for now
    console = Console(color_system="truecolor")
    logger = logging.getLogger("audiconnectpy")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    with Live(Text("[bold red]vehicle management"), refresh_per_second=4) as live:
        while True:
            async with ClientSession() as session:
                api = AudiConnect(session, *[secrets["audiconnect"][x] for x in ["username", "password", "country", "spin"]])
                try:
                    await api.async_login()
                except Exception as error:
                    import traceback
                    traceback.print_exception(type(error), error, error.__traceback__)
                while api.is_connected:
                    for vehicle in api.vehicles:
                        if vehicle.vin not in secrets["e-cars"]:
                            continue
                        inspect(vehicle, console=console)
                        # sleep 15 minutes and try again
                        for i in range(15):
                            for y in range(60):
                                asyncio.sleep(1)
                        # now go mary round again
                await api.async_close()
                live.update(Text(f"[bold red]vehicle management still to make {i}"))

if __name__ == "__main__":
    asyncio.run(main())
