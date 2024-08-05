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
                self.log_add(f"!! err_pickle_load {self.file_n} {e}", save=False)
        else:
            self.log_add(f"{self.file_n} not found, started from zero", save=False)
            self.var_save()
        self.set_pointers()

    @property
    def prefix_history(self):
        mm_dd = datetime.date.today().isoformat()[5:]
        return f"{self.dir_history}{mm_dd}_"

    def json_it(self, dct):
        """ dump the data in json format"""
        encode_JSON = lambda x: self.ts_str(x) if isinstance(x, datetime.datetime) else repr(x)
        return json.dumps(dct, indent=4, sort_keys=True, default=encode_JSON)

    def json_file(self, dct, file_n):
        """ dump the data in json format in file_n"""
        with open(f"{file_n}", "w") as f:
            f.write(self.json_it(dct))

    @property
    def rates_dct(self):
        if not hasattr(self, "_rates_dct"):
            self._rates_dct = json.loads(open("rates.json").read())
        return self._rates_dct

    def log_add(self, msg, save=True):
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
