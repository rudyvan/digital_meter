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

    def var_save(self, selfie):
        with open(pickle_file, "wb") as f:
            pickle.dump(selfie.data, f, pickle.HIGHEST_PROTOCOL)

    def var_restore(self, selfie):
        """This script manages the pickle load from a file"""
        if os.path.exists(pickle_file):
            try:
                with open(pickle_file, "rb") as f:
                    selfie.data = pickle.load(f)
                self.log_app.add(f"{pickle_file} loaded")

                # the following line is to remove!!!!!!!, after running the program once
                selfie.data.pop("log", None)

            except Exception as e:
                self.log_app.add(f"!! err_pickle_load {pickle_file} {e}", tpe="error")
        else:
            self.log_app.add(f"{pickle_file} not found, started from zero", tpe="error")
            self.var_save(selfie)


