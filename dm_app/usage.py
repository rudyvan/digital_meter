import datetime


class Usage:
    def __init__(self):
        super().__init__()

    # for those counters that are also usage:    do not include labels for hour/minute as these are not reported
    _usage_columns = lambda self: ["Today", "Week", "Month", "Year"]
    _usage_rows = lambda self: ["+Day", "-Day", "+Night", "-Night", "Σ kWh", "+€ Day", "-€ Day", "+€ Night", "-€ Night",
                                "Σ € kWh", "m3 Gas", "Σ € Gas", "m3 Water", "Σ € Water"]
    _rate_columns = lambda self: ["Rate", "€/kWh Day", "€/kWh Night", "€/m3 Gas", "€/m3 Water"]

    @property
    def zero_cumul(self):
        if not hasattr(self, "_zero_cumul"):
            self._zero_cumul = [0 for _ in range(len(self._usage_rows()))]
        return self._zero_cumul

    def set_data(self):
        # make a default data structure, read actual from pickle if any, else start from this
        self.data = {"meters": {"Electricity": {"+Day": 0, "-Day": 0, "+Night": 0, "-Night": 0, "unit": "kWh"},
                                "Gas": {"value": 0, "time": datetime.datetime.now(), "unit": "m3"},
                                "Water": {"value": 0, "time": datetime.datetime.now(), "unit": "m3"} },
                     "usage": dict((x, self.zero_cumul) for x in self._usage_columns()),
                     "log": {},
                     "cur_time": datetime.datetime.now()}

    def set_pointers(self):
        # these pointer must be set before self.data is used (after restore or creation)
        self.water_meter = self.data["meters"]["Water"]  # beware, self.water_meter is updated automatically
        self.gas_meter = self.data["meters"]["Gas"]      # beware, self.gas_meter is updated automatically
        self.usage = self.data["usage"]                  # beware, self.usage is updated automatically
        self.e_meter = self.data["meters"]["Electricity"]
        if self.log:  # something already added before restore of self.data?
            self.data["log"].update(self.log)
        self.log = self.data["log"]
        # pointers into rate_dict
        self.e_rate = self.rate_dict["Electricity"]
        self.g_rate = self.rate_dict["Gas"]["+"]
        self.w_rate = self.rate_dict["Water"]["+"]


    def update_usage(self):
        # calculate delta between 2 readings for electricity day/night produced/consumed, water and or gas
        # use the meter timestamp for the day/week/month/year transition and reset
        # 1. if no current time then return
        if not hasattr(self, "cur_time"):
            return
        # 2. update meters values in self.data
        self.e_meter["+Day"] = self.kwH_day_plus
        self.e_meter["-Day"] = self.kwH_day_min
        self.e_meter["+Night"] = self.kwH_night_plus
        self.e_meter["-Night"] = self.kwH_night_min
        get_v = lambda x: x.get("value", 0)
        # 3. current total of the meters
        self.now_cumul = \
            [self.kwH_day_plus, self.kwH_day_min, self.kwH_night_plus, self.kwH_night_min,
             self.kwH_day_plus - self.kwH_day_min + self.kwH_night_plus - self.kwH_night_min,
             self.kwH_day_plus * self.e_rate["+"]["Day"], self.kwH_day_min * self.e_rate["-"]["Day"],
             self.kwH_night_plus * self.e_rate["+"]["Night"], self.kwH_night_min * self.e_rate["-"]["Night"],
             self.kwH_day_plus * self.e_rate["+"]["Day"] - self.kwH_day_min * self.e_rate["-"]["Day"] +
             self.kwH_night_plus * self.e_rate["+"]["Night"] - self.kwH_night_min * self.e_rate["-"]["Night"],
             get_v(self.gas_meter), get_v(self.gas_meter) * self.g_rate,
             get_v(self.water_meter), get_v(self.water_meter) * self.w_rate]
        # 4. when have prev_time, a previous total exists and the difference is 'added', else add zero and set prev_time
        if "cumul" in self.data:
            self.prev_cumul = self.data["cumul"]
            self.prev_time = self.data["cur_time"]
            # day processing is possible as we have a previous measurement
            self.delta_cumul = [self.now_cumul[x] - self.prev_cumul[x] for x in range(len(self.now_cumul))]
            if self.prev_time.day != self.cur_time.day:
                # a new day has started, notify the usage at this point
                self.usage["Today"] = self.zero_cumul
                if self.prev_time.week != self.cur_time.isocalendar()[1]:
                    self.usage["Week"] = self.zero_cumul
                if self.prev_time.month != self.cur_time.month:
                    self.usage["Month"] = self.zero_cumul
                if self.prev_time.year != self.cur_time.year:
                    self.usage["Year"] = self.zero_cumul
        else:  # first time, no previous measurement
            self.delta_cumul = self.zero_cumul[:]
        # 5. add the difference between both measurements to the usage
        for period in self._usage_columns():
            for pos, val in enumerate(self.delta_cumul):
                self.usage[period][pos] += val
        self.data["cur_time"] = self.cur_time
        self.data["cumul"] = self.now_cumul
        self.var_save()
