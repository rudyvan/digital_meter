#!/usr/bin/python3
import asyncio
import datetime
import re

import crcmod.predefined
import serial_asyncio

from rich.live import Live
from rich.text import Text

from ..app import pi

from .usage import Usage
from .screens import Screens

from ..config import obiscodes


class InputChunkProtocol(asyncio.Protocol):

    p1line = bytearray()

    def connection_made(self, transport):
        self.transport = transport

    def connection_lost(self, exc):
        self.transport.loop.stop()

    def data_received(self, data):
        # stop callbacks again immediately
        InputChunkProtocol.p1line += data
        self.pause_reading()

    def pause_reading(self):
        # This will stop the callbacks to data_received
        self.transport.pause_reading()

    def resume_reading(self):
        # This will start the callbacks to data_received again with all data that has been received in the meantime.
        self.transport.resume_reading()


class BusMeter(Screens, Usage):
    """ this is a class to read data from a digital meter connected to the P1 port """

    def __init__(self, serial_port):
        self.serial_port = serial_port
        self.p1telegram = bytearray()
        self.obis_dict = {}
        self.bus = {}
        super().__init__()

    async def serial_start(self):
        self.transport, self.protocol = await serial_asyncio.create_serial_connection(
            asyncio.get_event_loop(), InputChunkProtocol, self.serial_port, baudrate=115200, xonxoff=1)


    def serial_bye(self, msg):
        pi.log_app.add(msg)
        self.transport.close()

    def checkcrc(self, p1telegram):
        # check CRC16 checksum of telegram and return False if not matching
        # split telegram in contents and CRC16 checksum (format:contents!crc)
        p1contents = ""
        for match in re.compile(b'\r\n(?=!)').finditer(p1telegram):
            p1contents = p1telegram[:match.end() + 1]
            # CRC is in hex, so we need to make sure the format is correct
            givencrc = hex(int(p1telegram[match.end() + 1:].decode('ascii').strip(), 16))
        # calculate checksum of the contents
        calccrc = hex(crcmod.predefined.mkPredefinedCrcFun('crc16')(p1contents))
        # check if given and calculated match
        if givencrc != calccrc:
            pi.log_app.add(f"Error telegram checksum mismatch: {givencrc=}, {calccrc=}")
            return False
        return True

    def ts_obj(self, ts):
        # parse timestamp from telegram
        # format:YYMMDDhhmmssX, where X is the daylight saving time flag S or W
        # convert to format:YYYY-MM-DD hh:mm:ss or YYYY-MM-DD if time is zero
        if len(ts) != 13:
            pi.log_app.add(f"Error expecting 13 characters: {ts=}")
        if ts[12] not in ["S", "W"]:
            pi.log_app.add(f"Error expecting S or W at the end of {ts=}")
        try:
            dt = datetime.datetime.strptime(ts[:-1], '%y%m%d%H%M%S')
        except Exception as e:
            pi.log_app.add(f"Error parsing timestamp: {ts=} {e=}")
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
        if not (obis_guide := obiscodes.get(obis, False)):
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
                        pi.log_app.add(f"{obis}: Grid expecting 230 or 400: {value=}")
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
                        pi.log_app.add(msg)
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
                ids = [r[1:-1] for r in values[1:1+2]]
                # expect class 4 at this point, check it for all id's
                if not all(x in obiscodes and obiscodes.get(x).class_id == 4 for x in ids):
                    pi.log_app.add(f"!!Expecting class_id == 4 -> {ids=} in {obis=}")
                get_val = lambda x: [x.partition("*")[0], x.partition("*")[2]]
                table = {self.ts_obj(values[x][1:-1]): [self.ts_obj(values[x+1][1:-1]), *get_val(values[x+2][1:-1])]\
                         for x in range(len(ids)+1, len(values)-1, 3)}
                return ret_val({"value": {"lines": lines, "ids": ids, "table": table}}, f"see table, month peaks ={lines}")
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
        # 1. get the event loop
        self.loop = asyncio.get_running_loop()
        # 2. start the socket server and set the buffer
        await self.serial_start()
        # 3. start the socket server
        await pi.socket_app.server_start()
        # 4. set the last live refresh time
        last_live, refresh_s = None, 3
        # 5. start the main loop with the live screens
        with Live(self.layout, console=pi.console) as live:
            while True:
                self.togather = []
                try:
                    # read input from serial port
                    self.protocol.resume_reading()
                    p1line = InputChunkProtocol.p1line
                    # read line by line, but cut between / and the ! + CRC16 checksum in the last line
                    # if P1 telegram starts with /, a new telegram is started
                    if "/" in InputChunkProtocol.p1line.decode('ascii'):  # "Found beginning of P1 telegram, cut off previous data"
                        p1line = p1line[p1line.find(b"/"):]
                        self.p1telegram = bytearray()
                    # catch up with the newlines
                    done_gram = False
                    while b'\r\n' in p1line:
                        line, _, p1line = p1line.partition(b'\r\n')
                        InputChunkProtocol.p1line = p1line
                        self.p1telegram.extend(line+b'\r\n')
                        # P1 telegram ends with ! + CRC16 checksum
                        if done_gram := ("!" in line.decode('ascii')):
                            break
                    if done_gram:
                        if self.checkcrc(self.p1telegram):  # "Checksum correct"
                            # make the table
                            self.obis_dict = {}
                            self.p1_table = [self.parsetelegramline(line.decode('ascii'))
                                             for line in self.p1telegram.split(b'\r\n') if line]
                            if self.update_usage():
                                self.update_layout(self.layout)
                            if not last_live or (datetime.datetime.now() - last_live).total_seconds() > refresh_s:
                                self.togather.append(self.loop.run_in_executor(None, live.refresh))
                                last_live = datetime.datetime.now()
                            self.json_file(self.data, f"data.json")
                    # make the async magic happen, but add sleep to avoid 100% cpu
                    self.togather.append(asyncio.sleep(0))
                    await asyncio.gather(*self.togather, return_exceptions=True)
                except (asyncio.CancelledError, KeyboardInterrupt) as error:
                    self.serial_bye(f"{error}")
                    break
                except Exception as e:
                    pi.console.print_exception(extra_lines=10, show_locals=True, width=200, word_wrap=True)
                    self.serial_bye(f"Something went wrong...{e}")
                    break

    def run(self):
        # 1. build the screens layout upfront
        pi.log_app.log_start("Starting digital meter script")
        self.layout = self.make_layout()
        # 2. set the default data in case no pickle file is present
        self.set_data()
        # 3. restore the data from pickle file if present
        pi.pickle_app.var_restore()
        self.set_pointers()
        asyncio.run(self.main_loop())
