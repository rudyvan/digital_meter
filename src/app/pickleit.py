#!/usr/bin/python3

import datetime
import os
import pickle

from ..config import pickle_file

class PickleIt:
    """ this is a class to pickle data to a file and unpickle it"""

    # pickle_file = "data.pickle"

    def __init__(self, log_app, *args, **kwargs):
        self.log_app = log_app
        self.file_n = pickle_file
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
                self.log_app.log_add(f"!! err_pickle_load {self.file_n} {e}")
        else:
            self.log_app.log_add(f"{self.file_n} not found, started from zero")
            self.var_save()


