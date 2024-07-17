#!/usr/bin/python3

import datetime
import os
import pickle

from rich import json


class PickleIt:
    """ this is a class to pickle data to a file and unpickle it"""

    pickle_file = "data.pickle"

    def __init__(self):
        self.log = {}
        self.file_n = PickleIt.pickle_file

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
                self.add_log(f"!! err_pickle_load {self.file_n} {e}", save=False)
        else:
            self.add_log(f"{self.file_n} not found, started from zero", save=False)
            self.var_save()
        self.set_pointers()

    def file_json(self):
        """ dump the data in json format in data.json file"""
        encode_JSON = lambda x: self.ts_str(x) if isinstance(x, datetime.datetime) else repr(x)
        with open("data.json", "w") as f:
            f.write(json.dumps(self.data, indent=4, sort_keys=True, default=encode_JSON))

    @property
    def rate_dict(self):
        if not hasattr(self, "_rate_dict"):
            self._rate_dict = json.loads(open("rate.json").read())
        return self._rate_dict

    def add_log(self, msg, save=True):
        """ add a log message to the log file, but keep the log file tidy by only keeping the last 10 messages,
            and refresh the time on repeat messages"""
        if msg in self.log.values():
            idx = list(self.log.values()).index(msg)
            self.log.pop(list(self.log)[idx], None)
        self.log[self.ts_str(datetime.datetime.now())] = msg
        if len(self.log) > 10:
            self.log = dict(list(self.log.items())[-10:])
        if save:
            self.var_save()
