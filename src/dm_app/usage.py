#!/usr/bin/python3

import datetime
import json
from ..app import pi
from ..config import usage_columns, usage_rows, day_peak_columns

class Usage:
    def __init__(self, *args, **kwargs):
        self.producing = False
        self.prev_kW_min = 0.0
        super().__init__(*args, **kwargs)

    # unfortunately namedtuples cannot be used in pickle, so for day_peak we have to use a list
    _day_peak_zero = [0, None]

    @property
    def zero_cumul(self):
        if not hasattr(self, "_zero_cumul"):
            self._zero_cumul = [0 for _ in range(len(usage_rows))]
        return self._zero_cumul

    def get_delta_cumul(self, new_cumul, old_cumul):
        """ calculate the difference between 2 cumuls, but consider that the meter values can flip over,
            f.e. when the meter goes from 9999 to 0, the difference is 1, not -9999"""
        # the counter flipped over if new < old
        get_diff_meter_flips = lambda old, new: 10**(len(str(abs(old)).partition(".")[0])) + new - old if abs(new) < abs(old) else new - old
        delta_cumul = []
        for x, r in enumerate(usage_rows):
            match r:
                case "+Day" | "-Day" | "+Night" | "-Night":
                    delta_cumul.append(get_diff_meter_flips(old_cumul[x], new_cumul[x]))
                case "+€ Day":
                    delta_cumul.append(get_diff_meter_flips(old_cumul[0], new_cumul[0])*self.e_rate["+"]["Day"])
                case "-€ Day":
                    delta_cumul.append(get_diff_meter_flips(old_cumul[1], new_cumul[1])*self.e_rate["-"]["Day"])
                case "+€ Night":
                    delta_cumul.append(get_diff_meter_flips(old_cumul[2], new_cumul[2])*self.e_rate["+"]["Night"])
                case "-€ Night":
                    delta_cumul.append(get_diff_meter_flips(old_cumul[3], new_cumul[3])*self.e_rate["-"]["Night"])
                case _:
                    delta_cumul.append(new_cumul[x] - old_cumul[x])
        return delta_cumul

    def set_data(self):
        # make a default data structure, read actual from pickle if any, else start from this
        self.data = {"meters": {"Electricity": {"+Day": 0, "-Day": 0, "+Night": 0, "-Night": 0, "unit": "kWh"},
                                "Gas": {"value": 0, "time": datetime.datetime.now(), "unit": "m3"},
                                "Water": {"value": 0, "time": datetime.datetime.now(), "unit": "m3"} },
                     "usage": dict((x, self.zero_cumul[:]) for x in usage_columns),
                     "cur_time": datetime.datetime.now(),
                     "start_time": datetime.datetime.now(),
                     "day_peak": dict((x, Usage._day_peak_zero[:]) for x in day_peak_columns),
                                           #  peak value, time of peak
                     "quarter_peak": 0}

    @property
    def rates_dct(self):
        if not hasattr(self, "_rates_dct"):
            self._rates_dct = json.loads(open("rates.json").read())
        return self._rates_dct

    def set_pointers(self):
        # these pointer must be set before self.data is used (after restore or creation)
        self.water_meter = self.data["meters"]["Water"]  # beware, self.water_meter is updated automatically
        self.gas_meter = self.data["meters"]["Gas"]      # beware, self.gas_meter is updated automatically
        self.usage = self.data["usage"]                  # beware, self.usage is updated automatically
        self.day_peak = self.data["day_peak"]
        self.e_meter = self.data["meters"]["Electricity"]
        self.peak_forecast = self.data["quarter_peak"]
        # pointers into rates_dct
        self.e_rate = self.rates_dct["Electricity"]
        self.g_rate = self.rates_dct["Gas"]["+"]
        self.w_rate = self.rates_dct["Water"]["+"]

    def json_it(self, dct):
        """ dump the data in json format"""
        encode_JSON = lambda x: self.ts_str(x) if isinstance(x, datetime.datetime) else repr(x)
        return json.dumps(dct, indent=4, sort_keys=True, default=encode_JSON)

    def json_file(self, dct, file_n):
        """ dump the data in json format in history_dir/file_n"""
        with open(f"{pi.log_app.prefix_history}{file_n}", "w") as f:
            f.write(self.json_it(dct))

    def update_quarter_peak(self):
        self.clock_todo = 15*60  # seconds in a quarter
        self.clock_done = (self.cur_time.minute % 15) * 60 + self.cur_time.second  # seconds in the current quarter
        if not all(hasattr(self, x) for x in ["prev_time", "cur_time"]):
            self.peak_gap_style = "green"
            return False
        self.new_peak_forecast = self.quarter_peak
        if clock_step := (self.cur_time - self.prev_time).total_seconds():
            peak_step = self.quarter_peak - self.data["prev_quarter_peak"]
            self.new_peak_forecast += peak_step / clock_step * (self.clock_todo - self.clock_done)
        # for the first 5 seconds in the quarter, if the peak forecast is not within 1kW of the prev_quarter_peak,
        # then use the prev_quarter_peak as the forecast peak
        if self.clock_done > 5 or abs(self.peak_forecast - self.new_peak_forecast) < 1.0:
            self.peak_forecast = self.new_peak_forecast
        # check against the day peak
        if (self.clock_todo - self.clock_done) < 5:
            if self.peak_forecast > self.day_peak["Today"][0]:
                # add nty new peak for the day
                self.day_peak["Today"] = [self.peak_forecast, self.cur_time-datetime.timedelta(seconds=self.clock_done)]
                pi.log_app.add(f"New Day Peak - {self.day_peak['Today']=}")
                pi.pickle_app.var_save(self)
        # beware, when producing energy, the quarter_peak is ZERO
        self.peak_gap = self.month_peak['value']-self.peak_forecast
        self.peak_gap_style = "green" if self.peak_gap > 0 else "red"
        return True

    @property
    def sum_utilities(self):
        if not hasattr(self, "usage"):
            return [f"{x:.2f}" for x in self.zero_cumul]
        self.usage["Σ € Utilities"] = [f"{sum(self.usage[c][usage_rows.index(r)] for r in ["Σ € kWh", "Σ € Gas", "Σ € Water"]):.2f}" for c in usage_columns]
        return self.usage["Σ € Utilities"]


    def update_usage(self):
        """ calculate delta between 2 readings for electricity day/night produced/consumed, water and or gas
            use the meter timestamp for the day/week/month/year transition and reset
        return True if usage has been calculated, else False"""
        def end_of(period):
            str_period = f"{', '.join(f'{u}={self.usage[period][x]:.2f}' for x, u in enumerate(usage_rows))}"
            pi.log_app.add(f"{period} Ended --> {self.sum_utilities[usage_columns.index(period)]:.2f} Σ € Utilities\n{str_period}")
            self.usage[period] = self.zero_cumul[:]
        def end_of_day():
            self.json_file(self.data, "data.json")
            # move the usage and day_peak one day back
            for old, prev in [("Day-3", "Day-2"), ("Day-2", "Day-1"), ("Day-1", "Today")]:
                if prev in self.usage:
                    self.usage[old] = self.usage[prev].copy()
                if prev in self.day_peak:
                    self.day_peak[old] = self.day_peak[prev].copy()
            end_of("Today")
            pi.log_app.add(f"Day Peak - {self.day_peak['Today']=}")
            self.day_peak["Today"] = Usage._day_peak_zero[:]
        # 1. if no current time then return
        if not hasattr(self, "cur_time"):
            return False
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
            self.delta_cumul = self.get_delta_cumul(self.now_cumul, self.prev_cumul)
            if self.prev_time.day != self.cur_time.day:
                # a new day has started, push the last data as json file
                end_of_day()
                # check if a new week, month or year has started
                if self.prev_time.weekday() == 6:
                    end_of("Week")
                if self.prev_time.month != self.cur_time.month:
                    end_of("Month")
                if self.prev_time.year != self.cur_time.year:
                    end_of("Year")
                # save and restart the log
                pi.log_app.log_restart()
        else:  # first time, no previous measurement
            self.delta_cumul = self.zero_cumul[:]
            self.prev_time = self.cur_time
            self.data["quarter_peak"] = 0
        # 5. add the difference between both measurements to the usage
        for period in usage_columns:
            if "Day-" in period:
                continue  # these are not updated
            for pos, val in enumerate(self.delta_cumul):
                self.usage[period][pos] += val
        # 6. update Σ € Utilities
        self.data["cur_time"] = self.cur_time
        self.data["cumul"] = self.now_cumul
        self.data["prev_quarter_peak"], self.data["quarter_peak"] = self.data["quarter_peak"], self.quarter_peak
        self.sum_utilities
        pi.pickle_app.var_save(self)
        if self.producing and self.kW_min < 0.01:
            self.producing = False
            pi.log_app.add("Producing stopped")
            self.prev_kW_min = self.kW_min
        elif not self.producing and self.kW_min > 0.01:
            self.producing = True
            pi.log_app.add(f"Producing Energy Started {self.kW_min=}")
        if self.producing and abs(self.kW_min - self.prev_kW_min) > 1:
            pi.log_app.add(f"Producing Energy going {'up' if self.kW_min > self.prev_kW_min else 'down'} {self.kW_min=}")
            self.prev_kW_min = self.kW_min
        return self.update_quarter_peak()

