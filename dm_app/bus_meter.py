#!/usr/bin/python3
import asyncio
import datetime
import re
from collections import namedtuple

import crcmod.predefined
import serial
import serial_asyncio
from rich import print
from rich.live import Live
from rich.text import Text

from .usage import Usage
from .pickleit import PickleIt
from .screen import Screen
from .web import SocketApp

p1line = bytearray()

class InputChunkProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        self.transport = transport

    def connection_lost(self, exc):
        self.transport.loop.stop()

    def data_received(self, data):
        # stop callbacks again immediately
        global p1line
        p1line += data
        self.pause_reading()

    def pause_reading(self):
        # This will stop the callbacks to data_received
        self.transport.pause_reading()

    def resume_reading(self):
        # This will start the callbacks to data_received again with all data that has been received in the meantime.
        self.transport.resume_reading()


class BusMeter(Screen, PickleIt, Usage, SocketApp):
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
        "0-0:96.3.10": obis_el("breaker_0", 70, "Electricity: 0=OFF, 1=ON, 2=Ready Reconnect"),
        "0-1:96.3.10": obis_el("breaker_1", 70, "Virtual Relay Bus 1, 0=OFF, 1=ON"),
        "0-2:96.3.10": obis_el("breaker_2", 70, "Virtual Relay Bus 2, 0=OFF, 1=ON"),
        "0-3:96.3.10": obis_el("breaker_3", 70, "Virtual Relay Bus 3, 0=OFF, 1=ON"),
        "0-4:96.3.10": obis_el("breaker_4", 70, "Virtual Relay Bus 4, 0=OFF, 1=ON"),
        "0-1:24.4.0":  obis_el("gas_breaker_1", 70, "Gas Valve Bus 1, 0=OFF, 1=ON, 2=Ready Reconnect"),
        "0-2:24.4.0":  obis_el("gas_breaker_2", 70, "Gas Valve Bus 2, 0=OFF, 1=ON, 2=Ready Reconnect"),
        "0-3:24.4.0":  obis_el("gas_breaker_3", 70, "Gas Valve Bus 3, 0=OFF, 1=ON, 2=Ready Reconnect"),
        "0-4:24.4.0":  obis_el("gas_breaker_4", 70, "Gas Valve Bus 4, 0=OFF, 1=ON, 2=Ready Reconnect")
    }

    def __init__(self, serial_port, socket_info):
        self.serial_port = serial_port
        self.socket_info = socket_info
        self.p1telegram = bytearray()
        self.obis_dict = {}
        self.bus = {}
        super().__init__()

    async def serial_start(self):
        self.transport, self.protocol = await serial_asyncio.create_serial_connection(
            asyncio.get_event_loop(), InputChunkProtocol, self.serial_port, baudrate=115200, xonxoff=1)
        # self.serial = serial.Serial(self.serial_port, 115200, xonxoff=1)


    def serial_bye(self, msg):
        self.log_add(msg)
        print(msg)
        # flush the buffer and close
        #self.serial.flush()
        #self.serial.close()

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
            self.log_add(f"Error telegram checksum mismatch: {givencrc=}, {calccrc=}")
            # self.serial.flush()
        return True

    def ts_obj(self, ts):
        # parse timestamp from telegram
        # format:YYMMDDhhmmssX, where X is the daylight saving time flag S or W
        # convert to format:YYYY-MM-DD hh:mm:ss or YYYY-MM-DD if time is zero
        if len(ts) != 13:
            self.log_add(f"Error expecting 13 characters: {ts=}")
        if ts[12] not in ["S", "W"]:
            self.log_add(f"Error expecting S or W at the end of {ts=}")
        try:
            dt = datetime.datetime.strptime(ts[:-1], '%y%m%d%H%M%S')
        except Exception as e:
            self.log_add(f"Error parsing timestamp: {ts=} {e=}")
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
                        self.log_add(f"{obis}: Grid expecting 230 or 400: {value=}")
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
                        self.log_add(msg)
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
                    self.log_add(f"!!Expecting class_id == 4 -> {ids=} in {obis=}")
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
                        return ret_val({"value": value}, Text(f"?? device type: {value}", "bold magenta"))
                self.bus[int(obis[2])] = device
                return ret_val({"value": device}, f"{value} -> {device}")
            case _:  # unknown class_id
                return ret_val({"value": "??"}, Text(f"??{class_id=} {p1line=}", "bold magenta"))


    async def main_loop(self):
        global p1line
        self.loop = asyncio.get_running_loop()
        await self.serial_start()
        # 4. start the socket server
        await self.server_start()
        last_live = None
        # 5. start the main loop with the live screen
        with Live(self.layout, console=self.console) as live:
            while True:
                try:
                    # read input from serial port
                    self.protocol.resume_reading()
                    # read line by line
                    # if P1 telegram starts with /, a new telegram is started
                    if "/" in p1line.decode('ascii'):  # "Found beginning of P1 telegram"
                        p1line = p1line[p1line.find(b"/"):]
                        self.p1telegram = bytearray()
                    elif b'\r\n' in p1line:
                        # if P1 telegram ends with \r\n, the line is complete
                        line, p1line = p1line.split(b'\r\n', 1)
                        # add line to telegram
                        self.p1telegram.extend(line)
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
                                if self.update_usage():
                                    self.update_layout(self.layout)
                                if not last_live or (datetime.datetime.now() - last_live).seconds > 3:
                                    live.refresh()
                                    #await self.loop.run_in_executor(None, live.refresh)
                                    last_live = datetime.datetime.now()
                                self.file_json()
                    await asyncio.sleep(0.1)
                except KeyboardInterrupt:
                    self.serial_bye("KeyboardInterrupt")
                    break
                except Exception as e:
                    self.console.print_exception(extra_lines=10, show_locals=True, width=200, word_wrap=True)
                    self.serial_bye(f"Something went wrong...{e}")
                    break

    def run(self):
        # 1. build the screen layout upfront
        self.layout = self.make_layout()
        # 2. set the default data in case no pickle file is present
        self.set_data()
        # 3. restore the data from pickle file if present
        self.var_restore()
        asyncio.run(self.main_loop())
