#!/usr/bin/python3

import datetime
import os
import pickle

from rich import json

from .logger import log_app


class PickleIt:
    """ this is a class to pickle data to a file and unpickle it"""

    pickle_file = "data.pickle"

    def __init__(self, *args, **kwargs):
        self.log = {}
        self.file_n = PickleIt.pickle_file
        super().__init__(*args, **kwargs)

    def var_save(self):
        with open(self.file_n, "wb") as f:
            pickle.dump(self.data, f, pickle.HIGHEST_PROTOCOL)

    def var_restore(self):
        """This script manages the pickle load from a file"""
        if os.path.exists(self.file_n):
            try:
                with open(self.file_n, "rb") as f:
                    self.data = pickle.load(f)
            except Exception as e:
                log_app.log_add(f"!! err_pickle_load {self.file_n} {e}")
        else:
            log_app.log_add(f"{self.file_n} not found, started from zero")
            self.var_save()

pickle_app = PickleIt()
