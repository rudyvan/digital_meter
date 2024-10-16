#!/usr/bin/python3
# encoding=utf-8
from .logger import Logger
from .pickleit import PickleIt
from .my_socket import SocketApp
from .tmux import TMux

from rich.console import Console

class SysEnv:
    def __init__(self):
        return

    def install(self, socket_info):
        self.console = Console(color_system="truecolor")
        self.tmux = TMux()
        self.log_app = Logger(self.console, self.tmux.log_console)
        self.pickle_app = PickleIt(self.log_app)
        self.socket_app = SocketApp(socket_info, self.log_app) if socket_info else None

pi = SysEnv()