#!/usr/bin/python3
import datetime
from collections import namedtuple

# This script will read data from serial connected to the digital meter P1 port

# Created by Jens Depuydt
# https://www.jensd.be
# https://github.com/jensdepuydt

import serial
import sys, os
import crcmod.predefined
import re
import pickle


from rich.traceback import install
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.layout import Layout
from rich.panel import Panel
from rich import print, json
from rich.live import Live

install(width=180, extra_lines=10, show_locals=True)

# Change your serial port here:
serialport = '/dev/ttyUSB0'

rate_dict = {"Gas": {"+": 0.5},
             "Water": {"+": 0.5},
             "Electricity": {"+": {"Day": 0.4, "Night": 0.3},
                             "-": {"Day": 0.1, "Night": 0.1}}}

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
        self.e_rate = rate_dict["Electricity"]
        self.g_rate = rate_dict["Gas"]["+"]
        self.w_rate = rate_dict["Water"]["+"]


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

class Screen:
    """ this is a class to make a screen for the console"""
    def __init__(self):
        self.console = Console(color_system="truecolor")
        super().__init__()

    def make_layout(self) -> Layout:
        """ make a layout for the console"""
        layout = Layout(name="root")
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=7)
        )
        layout["main"].split_row(
            Layout(name="side"),
            Layout(name="telegram_table", ratio=2, minimum_size=60),
        )
        layout["side"].split(Layout(name="usage"), Layout(name="month_peak", size=19))
        layout["footer"].split_row(
            Layout(name="log"),
            Layout(name="quarter_peak"),
        )
        layout["usage"].split(Layout(name="rate", size=5), Layout(name="usage_table"))
        return layout

    def make_header(self) -> Panel:
        grid = Table.grid(expand=True)
        grid.add_column(justify="center", ratio=1)
        grid.add_column(justify="center")
        grid.add_row("Digital Meter - P1 Telegram",
                     f"Version 1.0 {self.ts_str(self.cur_time) if hasattr(self, 'cur_time') else 'no time yet'}")
        return Panel(grid, style="white on blue")

    def make_telegram_table(self) -> Table:
        table = Table(show_lines=False, expand=True)
        table.add_column("Obis", justify="left", style="cyan", no_wrap=True)
        table.add_column("Thing", justify="left", style="magenta")
        table.add_column("Description", justify="left", style="green")
        table.add_column("Value", justify="left", style="blue")
        for row in self.p1_table:
            table.add_row(*row)
        return table

    def make_rate_table(self) -> Table:
        table = Table(show_lines=False, expand=True, box=None)
        for rate_c in self._rate_columns():
            # make the column for the rate table cyan if it is the current rate else magenta
            hit = True if "kWh" not in rate_c else \
                ((self.cur_rate == 1) and ("Day" in rate_c)) or ((self.cur_rate == 2) and ("Night" in rate_c))
            table.add_column(rate_c, justify="center", style="magenta" if hit else "cyan")
        for sign in ["+", "-"]:
            rend = []
            for tpe in ["Electricity", "Gas", "Water"]:
                if sign not in rate_dict[tpe]:
                    rend.append("")
                elif isinstance(rate_dict[tpe][sign], dict):
                    rend.append(f"{rate_dict[tpe][sign]['Day']:.2f}")
                    rend.append(f"{rate_dict[tpe][sign]['Night']:.2f}")
                else:
                    rend.append(f"{rate_dict[tpe][sign]:.2f}")
            table.add_row(sign, *rend)
        return table

    def make_usage_table(self) -> Table:
        """ beware, styling is contingent on the text in the first column, such as "Day" or "Night" or "Total" """
        table = Table(show_lines=False, expand=True)
        table.add_column("Usage/Cost", justify="left", style="magenta")
        for x in self._usage_columns():
            table.add_column(x, justify="right", style="cyan")
        for pos, line in enumerate(self._usage_rows()):
            # highlight day or night usage depending on the current rate
            hit = (self.cur_rate == 1 and "Day" in line or self.cur_rate == 2 and "Night" in line)
            table.add_row(line, *[f"{self.usage[x][pos]:.2f}" for x in self._usage_columns()],
                          style="green" if hit else "blue", end_section=True if "Σ" in line else False)
        return table

    def make_log_table(self) -> Table:
        table = Table.grid()
        table.add_column(justify="left", style="cyan")
        table.add_column(justify="left", style="magenta")
        table.add_column(justify="left", style="magenta")
        for row in sorted(self.log, reverse=True):
            table.add_row(row, " ", self.log[row])
        return table


    def make_month_peak_table(self) -> Table:
        table = Table(show_lines=False, expand=True)
        table.add_column("Month", justify="left", style="cyan", no_wrap=True)
        table.add_column("When", justify="left", style="magenta")
        table.add_column("Peak", justify="left", style="green")
        table.add_column("Unit", justify="left", style="green")
        # show current month peak first
        table.add_row("Current Month", self.ts_str(self.month_peak["time"]), f"{self.month_peak['value']:06.3f}",
                      self.month_peak["unit"])
        for m in sorted(getattr(self, "months_peak_past", {}).get("table", {}), reverse=True):
            it = self.months_peak_past["table"][m]
            table.add_row(self.ts_str(m), self.ts_str(it[0]), *it[1:])
        return table

    def make_quarter_peak_table(self) -> Table:
        pass

    def update_layout(self, layout):
        """ update the layout with the data from the class"""
        layout["header"].update(self.make_header())
        layout["telegram_table"].update(Panel(self.make_telegram_table(), title="Telegram"))
        layout["month_peak"].update(Panel(self.make_month_peak_table(), title="Months Peak"))
        layout["log"].update(Panel(self.make_log_table(), title="Log"))
        layout["usage_table"].update(Panel(self.make_usage_table(), title="Usage"))
        layout["rate"].update(Panel(self.make_rate_table(), title="Rate"))



class BusMeter(Screen, PickleIt, Usage):
    """ this is a class to read data from a digital meter connected to the P1 port """

    obis_el = namedtuple('OBIS', ['th_n', 'class_id', 'description'])

    # OBIS codes for P1 telegram from eMUCS-P1 version 2.1.1

    obiscodes = {
        "0-0:96.1.4":  obis_el("version", 1, "Version major.minor (current is 50221)"),
        "0-0:1.0.0":   obis_el("time_now", 8, "Timestamp current time"),
        "0-0:96.13.0": obis_el("message", 1, "Text Message, max 1024 chars"),
        "0-0:96.14.0": obis_el("active_rate", 1, "Current rate (1=day,2=night)"),
        "1-0:1.8.1":   obis_el("kwH_day_plus", 3, "Rate 1 (day) - total consumption"),
        "1-0:1.8.2":   obis_el("kwH_night_plus", 3, "Rate 2 (night) - total consumption"),
        "1-0:2.8.1":   obis_el("kwH_day_min", 3, "Rate 1 (day) - total production"),
        "1-0:2.8.2":   obis_el("kwH_night_min", 3, "Rate 2 (night) - total production"),
        "1-0:1.7.0":   obis_el("kW_plus", 3, "All phases current consumption"),
        "1-0:2.7.0":   obis_el("kW_min", 3, "All phases current production"),
        "1-0:21.7.0":  obis_el("L1_plus", 3, "L1 consumption"),
        "1-0:41.7.0":  obis_el("L2_plus", 3, "L2 consumption"),
        "1-0:61.7.0":  obis_el("L3_plus", 3, "L3 consumption"),
        "1-0:22.7.0":  obis_el("L1_min", 3, "L1 production"),
        "1-0:42.7.0":  obis_el("L2_min", 3, "L2 production"),
        "1-0:62.7.0":  obis_el("L3_min", 3, "L3 production"),
        "1-0:32.7.0":  obis_el("V_L1", 3, "L1 voltage"),
        "1-0:52.7.0":  obis_el("V_L2", 3, "L2 voltage"),
        "1-0:72.7.0":  obis_el("V_L3", 3, "L3 voltage"),
        "1-0:31.7.0":  obis_el("A_L1", 3, "L1 current"),
        "1-0:51.7.0":  obis_el("A_L2", 3, "L2 current"),
        "1-0:71.7.0":  obis_el("A_L3", 3, "L3 current"),
        "1-0:94.32.1": obis_el("V_grid", 1, "Grid Config: 230=3x230V, 400=3x400V"),
        "0-0:17.0.0":  obis_el("kW_limit", 71, "Max power, 99.999 = deactivated"),
        "1-0:31.4.0":  obis_el("A_limit", 21, "Max current, 999.99 = deactivated"),
        "1-0:1.6.0":   obis_el("month_peak", 4, "Current Month Peak:Time/Power"),
        "0-0:98.1.0":  obis_el("months_peak_past", 7, "Past Months (13) Peak:Time/Power"),
        "1-0:1.4.0":   obis_el("quarter_peak", 5, "Quarter Hour Average Power"),
        "0-1:24.1.0":  obis_el("dev_bus_1", 72, "Device Type Bus 1 (gas=3, water=7, ..)"),
        "0-2:24.1.0":  obis_el("dev_bus_2", 72, "Device Type Bus 2 (gas=3, water=7, ..)"),
        "0-3:24.1.0":  obis_el("dev_bus_3", 72, "Device Type Bus 3 (gas=3, water=7, ..)"),
        "0-4:24.1.0":  obis_el("dev_bus_4", 72, "Device Type Bus 4 (gas=3, water=7, ..)"),
        "0-0:96.1.2":  obis_el("ean_electr", 10, "EAN code Electricity"),
        "0-1:96.1.2":  obis_el("ean_bus_1", 10, "EAN code Bus 1"),
        "0-2:96.1.2":  obis_el("ean_bus_2", 10, "EAN code Bus 2"),
        "0-3:96.1.2":  obis_el("ean_bus_3", 10, "EAN code Bus 3"),
        "0-4:96.1.2":  obis_el("ean_bus_4", 10, "EAN code Bus 4"),
        "0-0:96.1.1":  obis_el("meter_electr", 10, "Meter Serial Electricity"),
        "0-1:96.1.1":  obis_el("meter_bus_1", 10, "Meter Serial Bus 1"),
        "0-2:96.1.1":  obis_el("meter_bus_2", 10, "Meter Serial Bus 2"),
        "0-3:96.1.1":  obis_el("meter_bus_3", 10, "Meter Serial Bus 3"),
        "0-4:96.1.1":  obis_el("meter_bus_4", 10, "Meter Serial Bus 4"),
        "0-1:24.2.3":  obis_el("gas_meter", 4, "Gas consumption / capture time, Bus 1"),
        "0-2:24.2.3":  obis_el("gas_meter", 4, "Gas consumption / capture time, Bus 2"),
        "0-3:24.2.3":  obis_el("gas_meter", 4, "Gas consumption / capture time, Bus 3"),
        "0-4:24.2.3":  obis_el("gas_meter", 4, "Gas consumption / capture time, Bus 4"),
        "0-1:24.2.1":  obis_el("water_meter", 4, "Water consumption / capture time, Bus 1"),
        "0-2:24.2.1":  obis_el("water_meter", 4, "Water consumption / capture time, Bus 2"),
        "0-3:24.2.1":  obis_el("water_meter", 4, "Water consumption / capture time, Bus 3"),
        "0-4:24.2.1":  obis_el("water_meter", 4, "Water consumption / capture time, Bus 4"),
        "0-0:96.3.10": obis_el("breaker_electr", 70, "Electricity Breaker State: 0=disc, 1=conn, 2=ready reconnect"),
        "0-1:96.3.10": obis_el("breaker_1", 70, "Virtual Relay Bus 1, 0=disc, 1=conn"),
        "0-2:96.3.10": obis_el("breaker_2", 70, "Virtual Relay Bus 2, 0=disc, 1=conn"),
        "0-3:96.3.10": obis_el("breaker_3", 70, "Virtual Relay Bus 3, 0=disc, 1=conn"),
        "0-4:96.3.10": obis_el("breaker_4", 70, "Virtual Relay Bus 4, 0=disc, 1=conn"),
        "0-1:24.4.0":  obis_el("gas_breaker_1", 70, "Gas Valve Bus 1, 0=disc, 1=conn, 2=ready reconnect"),
        "0-2:24.4.0":  obis_el("gas_breaker_2", 70, "Gas Valve Bus 2, 0=disc, 1=conn, 2=ready reconnect"),
        "0-3:24.4.0":  obis_el("gas_breaker_3", 70, "Gas Valve Bus 3, 0=disc, 1=conn, 2=ready reconnect"),
        "0-4:24.4.0":  obis_el("gas_breaker_4", 70, "Gas Valve Bus 4, 0=disc, 1=conn, 2=ready reconnect")
    }

    def __init__(self):
        self.serial = serial.Serial(serialport, 115200, xonxoff=1)
        self.p1telegram = bytearray()
        self.obis_dict = {}
        self.bus = {}
        super().__init__()

    def checkcrc(self, p1telegram):
        # check CRC16 checksum of telegram and return False if not matching
        # split telegram in contents and CRC16 checksum (format:contents!crc)
        for match in re.compile(b'\r\n(?=!)').finditer(p1telegram):
            p1contents = p1telegram[:match.end() + 1]
            # CRC is in hex, so we need to make sure the format is correct
            givencrc = hex(int(p1telegram[match.end() + 1:].decode('ascii').strip(), 16))
        # calculate checksum of the contents
        calccrc = hex(crcmod.predefined.mkPredefinedCrcFun('crc16')(p1contents))
        # check if given and calculated match
        if givencrc != calccrc:
            self.add_log(f"Error telegram checksum mismatch: {givencrc=}, {calccrc=}")
        return True

    def ts_obj(self, ts):
        # parse timestamp from telegram
        # format:YYMMDDhhmmssX, where X is the daylight saving time flag S or W
        # convert to format:YYYY-MM-DD hh:mm:ss or YYYY-MM-DD if time is zero
        if len(ts) != 13:
            self.add_log(f"Error expecting 13 characters: {ts=}")
        if ts[12] not in ["S", "W"]:
            self.add_log(f"Error expecting S or W at the end of {ts=}")
        try:
            dt = datetime.datetime.strptime(ts[:-1], '%y%m%d%H%M%S')
        except Exception as e:
            self.add_log(f"Error parsing timestamp: {ts=} {e=}")
            dt=datetime.datetime.now()
        return dt

    ts_str = lambda self, dt: dt.strftime('%Y-%m-%d %H:%M:%S')

    @property
    def cur_rate(self):
        return int(self.obis_dict.get("0-0:96.14.0", {}).get("value", 1))

    def parsetelegramline(self, p1line):
        def ret_val(result_dct, result_str):
            self.obis_dict[obis] = result_dct
            setattr(self, th_n, result_dct["value"])
            return obis, th_n, description, result_str

        # parse a single line of the telegram and try to get relevant data from it
        if not p1line or p1line[0] in ["/", "!"]:
            # / FLU5\253967035_D  is the header
            # ! 6E4B is the checksum
            return "-", "-", "-", Text(p1line, "bold magenta")
        # get OBIS code from line (format:OBIS(value)
        elif "(" not in p1line:
            return "-", "-", Text("?? No OBIS code in line", "bold magenta"), p1line
        obis = p1line.split("(")[0]
        # check if OBIS code is something we know and parse it
        if not (obis_guide := BusMeter.obiscodes.get(obis, False)):
            return "", "", Text(f"?? OBIS code {obis} not recognised", "bold magenta"), p1line
        th_n, class_id, description = obis_guide
        values = re.findall(r"\(.*?\)", p1line)
        # decode the value based on the class_id
        match class_id:
            case 1 | 10:  # data
                value = values[0][1:-1]
                if class_id == 10:
                    value = bytearray.fromhex(value).decode()
                if obis == "1-0:94.32.1":  # vgrid
                    if value not in ["230", "400"]:
                        self.add_log(f"{obis}: Grid expecting 230 or 400: {value=}")
                return ret_val({"value": value}, value)
            case 3 | 5 | 21 | 71:  # register, demand register, register monitor, limiter
                value_str, _, unit = values[0][1:-1].partition("*")
                value = float(value_str) if "." in value_str else int(value_str)
                result_dct = {"value": value, "unit": unit}
                result_str = f"{value_str} {unit}"
                # check if all phases are above 200 V
                if (self.obis_dict.get("1-0:94.32.1", None) and
                    self.obis_dict["1-0:94.32.1"]["value"] == "400" and
                    any(x == obis for x in ["1-0:32.7.0", "1-0:52.7.0", "1-0:72.7.0"])):
                    if int(value) < 200:
                        msg = f"!! PHASE DEACTIVE {result_str}"
                        self.add_log(msg)
                        return ret_val(result_dct, Text(msg, "bold red"))
                return ret_val(result_dct, result_str)
            case 4:  # extended register
                value_time = self.ts_obj(values[0][1:-1])
                value, _, unit = values[1][1:-1].partition("*")
                value = float(value) if "." in value else int(value)
                return ret_val({"value": {"value": value, "unit": unit, "time": value_time}},
                               f"{self.ts_str(value_time)} {value} {unit}")
            case 7:  # profile generic
                # first no of lines, then the id's of the lines, then the values of those id's
                lines = int(values[0][1:-1])
                ids = [r[1:-1] for r in values[1:1+lines]]
                # expect class 4 at this point, check it for all id's
                if not all(BusMeter.obiscodes.get(x).class_id == 4 for x in ids):
                    self.add_log(f"!!Expecting class_id == 4 -> {ids=} in {obis=}")
                get_val = lambda x: [x.partition("*")[0], x.partition("*")[2]]
                table = {self.ts_obj(values[x][1:-1]): [self.ts_obj(values[x+1][1:-1]), *get_val(values[x+2][1:-1])]\
                         for x in range(lines+1, len(values)-1, 3)}
                return ret_val({"value": {"lines": lines, "ids": ids, "table": table}}, f"{lines=}")
            case 8:  # timestamp
                self.cur_time = self.ts_obj(values[0][1:-1])
                return ret_val({"value": self.cur_time}, f"{self.ts_str(self.cur_time)}")
            case 70:  # disconnect control
                dc = int(values[0][1:-1])
                result_dct = {"value": dc}
                if dc == 2:
                    text = f"!! Reconnect={dc}"
                    text += " press yellow button 5s" if obis == "0-0:96.3.10" else ""
                    return ret_val(result_dct, Text(text, "bold red"))
                return ret_val(result_dct, f"{dc}")
            case 72:  # M-Bus Client
                value = values[0][1:-1]
                match value:
                    case "003":  # gas
                        device = "gas"
                    case "007":  # water
                        device = "water"
                    case _:
                        return obis, th_n, description, Text(f"Unknown device type: {value}", "bold magenta")
                self.bus[int(obis[2])] = device
                return ret_val({"value": device}, f"{value} -> {device}")
            case _:  # unknown class_id
                return "", "", Text(f"?? class_id code {class_id} not recognised", "bold magenta"), p1line

    def run(self):
        layout = self.make_layout()
        self.set_data()
        self.var_restore()
        with Live(layout, console=self.console) as live:
            while True:
                try:
                    # read input from serial port
                    p1line = self.serial.readline()
                    # if P1 telegram starts with /, a new telegram is started
                    if "/" in p1line.decode('ascii'):  # "Found beginning of P1 telegram"
                        self.p1telegram = bytearray()
                    # add line to telegram
                    self.p1telegram.extend(p1line)
                    # P1 telegram ends with ! + CRC16 checksum
                    if "!" in p1line.decode('ascii'):
                        if self.checkcrc(self.p1telegram):  # "Checksum correct"
                            # make the table
                            self.obis_dict = {}
                            self.p1_table = []
                            # parse telegram contents, line by line
                            for line in self.p1telegram.split(b'\r\n'):
                                if line:
                                    self.p1_table.append(self.parsetelegramline(line.decode('ascii')))
                            self.update_usage()
                            self.update_layout(layout)
                            live.refresh()
                            self.file_json()
                except KeyboardInterrupt:
                    print("Stopping...")
                    # flush the buffer
                    self.serial.flush()
                    self.serial.close()
                    break
                except Exception as e:
                    self.console.print_exception(extra_lines=10, show_locals=True, width=200, word_wrap=True)
                    # traceback.print_exc()
                    print(f"Something went wrong...{e}")
                    # flush the buffer
                    self.serial.flush()
                    self.serial.close()
                    break

if __name__ == '__main__':
    BusMeter().run()