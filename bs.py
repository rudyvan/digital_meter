#!/usr/bin/python3

# This script will manage the storage of electricity in batteries.

from time import sleep
# from bs_app import BatteryStorage

from config import battery_info, socket_info

from rich.live import Live
from rich.text import Text

from rich.traceback import install

install(width=180, extra_lines=10, show_locals=True)


if __name__ == '__main__':
    # BatteryStorage(socket_info, battery_info).run()
    with Live(Text("[bold red]battery management still to make"), refresh_per_second=4) as live:
        while True:
            for i in range(100):
                live.update(Text(f"[bold red]battery management still to make {i}"))
                sleep(0.1)

