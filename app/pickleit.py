#!/usr/bin/python3

import datetime
import os
import pickle

from rich import json

from .logger import log_app
from .history import prefix_history

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
        self.set_pointers()


    def json_it(self, dct):
        """ dump the data in json format"""
        encode_JSON = lambda x: self.ts_str(x) if isinstance(x, datetime.datetime) else repr(x)
        return json.dumps(dct, indent=4, sort_keys=True, default=encode_JSON)

    def json_file(self, dct, file_n):
        """ dump the data in json format in history_dir/file_n"""
        with open(f"{prefix_history()}{file_n}", "w") as f:
            f.write(self.json_it(dct))

    @property
    def rates_dct(self):
        if not hasattr(self, "_rates_dct"):
            self._rates_dct = json.loads(open("rates.json").read())
        return self._rates_dct

pickle_app = PickleIt()
