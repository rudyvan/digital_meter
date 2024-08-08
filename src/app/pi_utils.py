#!/usr/bin/python3
# encoding=utf-8
from .logger import Logger
from .pickleit import PickleIt
from .my_socket import SocketApp

from rich.console import Console

class SysEnv:
    def __init__(self):
        return

    def install(self, socket_info):
        self.console = Console(color_system="truecolor")
        self.log_app = Logger()
        self.pickle_app = PickleIt(self.log_app)
        self.socket_app = SocketApp(socket_info)

pi = SysEnv()