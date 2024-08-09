#!/usr/bin/python3
# encoding=utf-8
"""contains everything in relation with logging

the following logger is deployed and used:

- log_info : normal log channel

"""
import inspect
import os
import sys
import socket
import logging
import datetime

from rich.logging import RichHandler
from rich.markup import escape

from ..config import dir_history, log_name, log_file

class Logger:
    def __init__(self, console, log_console, *args, **kwargs):
        self.console, self.log_console = console, log_console
        if not os.path.exists(dir_history):
            os.makedirs(dir_history)
        super().__init__(*args, **kwargs)

    def add(self, txt, tpe="info", **kw):
        getattr(logging.getLogger(log_name), tpe)(txt, **kw)

    @property
    def host_name(self):
        return socket.gethostname().partition(".")[0]

    @property
    def prefix_history(self):
        # take yesterday date and format it to MM-DD
        mm_dd = (datetime.date.today()-datetime.timedelta(days=1)).isoformat()[5:]
        return f"{dir_history}{mm_dd}_"

    def clear_handlers(self, logger):
        while logger.hasHandlers():
            to_remove = logger.handlers[0]
            if isinstance(to_remove, logging.FileHandler):
                to_remove.close()
            logger.removeHandler(to_remove)

    def rich_handler_errors_only(self):
        # set the screen handler in tmux session luce to errors only
        for handler in logging.getLogger(log_name).handlers:
            if isinstance(handler, RichHandler):
                handler.setLevel(logging.ERROR)

    def log_start(self, why):
        """start the logger with a file and a console handler"""
        # def add_handler(_logger, _handler):
        #     _handler.setFormatter(logging.Formatter(format, datefmt="%Y-%m-%d %X"))
        #     _logger.addHandler(_handler)
        #     _logger.propagate = False
        # 1. set the log level to ERROR level only except for asyncio where is set to WARNING
        for key in logging.Logger.manager.loggerDict:
            if key == log_name:
                self.clear_handlers(logging.getLogger(key))
            else:
                logging.getLogger(key).setLevel(logging.WARNING if "asyncio" in key else logging.ERROR)
                logging.getLogger(key).propagate = True
        # format = f"%(asctime)s {self.host_name} %(message)s"
        logging.basicConfig(level=logging.DEBUG)  # format=format, datefmt="%Y-%m-%d %X")
        # 3. create the handlers
        logger = logging.getLogger(log_name)
        logger.addHandler(RichHandler(level=logging.INFO, console=self.log_console, rich_tracebacks=True))
        # _handler = logging.FileHandler(log_file)
        # _handler.setLevel(logging.DEBUG)
        logger.addHandler(logging.FileHandler(log_file))
        logger.propagate = False
        # make the files not empty and show welcome message through the handlers
        self.add(why)

    def log_down(self):
        logging.shutdown()

    def log_close(self):
        self.clear_handlers(logging.getLogger(log_name))

    def log_crash(self, txt):
        """log and print a crash and use sys.exec_info or make up a crash message
           only print the crash details if it is a crash"""
        crash = sys.exc_info()
        is_crash = any(it is not None for it in crash)
        txt_plus = f"{txt}\nstack={','.join(f'{frame.filename}@{frame.lineno}' for frame in inspect.stack())}" if is_crash else txt
        self.console.print(escape(f"!!{'' if is_crash else 'No '}Exception --> {txt}"))
        if is_crash:
            self.console.print_exception(extra_lines=10, show_locals=True, width=200, word_wrap=True)
        self.add(txt_plus, tpe="error" if is_crash else "info", exc_info=is_crash)

    def log_move(self):
        """ move the log files to the history folder, ensure with the date MM-DD one file every year"""
        if os.path.exists(log_file):
            os.rename(log_file, f"{self.prefix_history}{log_file}")

    def log_restart(self):
        self.log_close()
        self.log_move()
        self.log_start("New Day Reopen")

    __repr__ = lambda self: "Logger"

