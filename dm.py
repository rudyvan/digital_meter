#!/usr/bin/python3

# This script will read and process data from serial P1 port of the digital meter as used in Belgium.
# https://github.com/rudyvan/digital_meter

from config import serial_port, socket_info

from dm_app import BusMeter

from .app import log_app, pickle_app, SocketApp

from rich.traceback import install

install(width=180, extra_lines=10, show_locals=True)

class DigitalMeter(BusMeter):
    def __init__(self):
        self.log_app = log_app
        self.pickle_app = pickle_app
        self.socket_app = SocketApp(socket_info)
        super().__init__(serial_port)
        self.log_app.console = self.console
    def run(self):
        super().run()

if __name__ == '__main__':
    DigitalMeter().run()