#!/usr/bin/python3
# encoding=utf-8
from .logger import log_app
from .pickleit import pickle_app
from .my_socket import SocketApp

class SysEnv:
    def __init__(self):
        return

    def install(self, socket_info):
        self.log_app = log_app
        self.pickle_app = pickle_app
        self.socket_app = SocketApp(socket_info)

pi = SysEnv()