#!/usr/bin/python3

import datetime
import os
import pickle

from ..config import pickle_file

class PickleIt:
    """ this is a class to pickle data to a file and unpickle it"""

    def __init__(self, log_app, *args, **kwargs):
        self.log_app = log_app
        super().__init__(*args, **kwargs)

    def var_save(self):
        with open(pickle_file, "wb") as f:
            pickle.dump(self.data, f, pickle.HIGHEST_PROTOCOL)

    def var_restore(self):
        """This script manages the pickle load from a file"""
        if os.path.exists(pickle_file):
            try:
                with open(pickle_file, "rb") as f:
                    self.data = pickle.load(f)
                self.log_app.
            except Exception as e:
                self.log_app.add(f"!! err_pickle_load {pickle_file} {e}")
        else:
            self.log_app.add(f"{pickle_file} not found, started from zero")
            self.var_save()


