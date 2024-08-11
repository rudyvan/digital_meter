#!/usr/bin/python3

import aiohttp, asyncio
from aiohttp import web
import websockets
import socket
import json
import datetime

app = web.Application()

class SocketApp:
    """aiohttp web application"""
    def __init__(self, socket_info, log_app, *args, **kwargs):
        self.socket_info = socket_info
        self.log_app = log_app
        super().__init__(*args, **kwargs)

    def json_it(self, dct):
        """ dump the data in json format"""
        encode_JSON = lambda x: self.DM_selfie.ts_str(x) if isinstance(x, datetime.datetime) else repr(x)
        return json.dumps(dct, indent=4, sort_keys=True, default=encode_JSON)

    async def send_ws(self, data, ip):
        """ run a task pushing data from queue to the destination websocket server
            A queue is used as not to slow down the caller
            the data is dropped if the queue is full """
        if not hasattr(self, "_send_tasks"):
            self._send_tasks = {}
            self._send_queues = {}
        # 1. check send task
        if ip not in self._send_tasks or self._send_tasks[ip].done():
            self._send_queues[ip] = asyncio.Queue(maxsize=15)
            self._send_tasks[ip] = asyncio.create_task(self.task_send_ws(ip))
        # 2. add data to the queue
        data_str = data if isinstance(data, str) else self.json_it(data)
        self.log_app.add(f"Websocket Queue {ip}: {len(data_str)} bytes added", tpe="debug")
        if self._send_queues[ip].full():
            return self.log_app.add(f"Websocket Queue {ip} full", tpe="error")
        # could add test for not sending repeat data
        await self._send_queues[ip].put(data_str)

    async def task_send_ws(self, ip):
        """ perpetual task trying to send data from a queue to a host socket server,
            The connection is closed automatically after each iteration of the loop.
            If an error occurs while establishing the connection, connect() retries with exponential backoff.
            The backoff delay starts at three seconds and increases up to one minute.
            If an error occurs in the body of the loop, you can handle the exception and connect() will reconnect with
            the next iteration; or you can let the exception bubble up and break out of the loop.
            This lets you decide which errors trigger a reconnection and which errors are fatal.
            """
        end_p = self.socket_info["ws_url"].format(ip=ip, port=self.socket_info["dest_port"])
        async for websocket in websockets.connect(end_p):
            try:
                data = await self._send_queues[ip].get()
                data_str = json.dumps(json.loads(data))  # remove newlines and tabs
                self.log_app.add(f"Websocket Send to {end_p} --> {data_str}", tpe="debug")
                await websocket.send(data)
            except websockets.ConnectionClosed:
                continue

    def my_assert(self, c, m):
        """ return assert c and log error m if fails """
        if not (ret_val := bool(c)):
            self.log_app.add(m, tpe="error")
        return ret_val

    # convert gas and water to liter and only take the value
    get_val = lambda self, val: val.get("value", 0) * 1000 if isinstance(val, dict) else val

    async def reply_ws(self, data, ip, ws):
        """ reply to a websocket server request
            below code is propriety and should be adapted to your specific needs in communicating obdis values to
            external websocket servers
        """
        ths_map = self.DM_selfie.ths_map
        self.log_app.add(f"Websocket Server: rcv from {ip}: {data}", tpe="debug")
        all_keys = ["type", "cmd", "th", "val"]
        data_dct = json.loads(data)
        # intercept special case of domestic_water^purchased_water, as the digital_meter does not registrate water from
        # pidpa, i have my own water meter registering consumption, therefore i can update
        if "domestic_water^purchased_water" in data:
            water = data_dct.get("val", 0) / 1000.0  # convert from liters to m3
            now = datetime.datetime.now()
            self.DM_selfie.water_meter = {"value": water, "unit": "m3", "time": now}
            self.DM_selfie.w_meter = {"value": water, "unit": "m3", "time": now}

            self.log_app.add(f"{self.DM_selfie.w_meter=}, {self.DM_selfie.data['meters']=}")

            if data_dct["cmd"] == "reply":  # bye if reply to our initial ask
                return
            # assume cmd==set -> return with cmd=reply
            data_dct["cmd"] = "reply"
            return await self.send_ws(data_dct, ip)
        # continue with the rest of the things
        if not self.my_assert(all(x in data_dct for x in all_keys),
                              f"Websocket {ip} ? data missing keys {all_keys} not in {data_dct}") or \
           not self.my_assert((th := data_dct["th"]) in ths_map,
                              f"Websocket {ip} ?? {th=} not in {ths_map}"):
            return
        # ignore if not ask command
        match data_dct["cmd"]:
            case "ask":  # ask for a th value
                data_dct["cmd"] = "reply"
                obdis_th = ths_map[th]
                data_dct["val"] = self.get_val(getattr(self.DM_selfie, obdis_th, 0.0))
                return await self.send_ws(data_dct, ip)
            case "cum" | "usage":  # ask for a cum or usage
                self.log_app.add(f"Things_sync ignored Forensics request: {data}", tpe="debug")
            case _:
                return

    async def send_ths(self):
        """ every config.socket_info[update_freq] seconds send the digital meter things to the remote server
            by filling the queue.
            below code is propriety and should be adapted to your specific needs in communicating obdis values to
            external websocket servers
        """
        now = datetime.datetime.now()
        if not hasattr(self, "_last_send") or (now - self._last_send).total_seconds() > self.socket_info["update_freq"]:
            ths_map = self.DM_selfie.ths_map
            data_dct = [{"type": "th", "cmd": "set", "th": th, "val": self.get_val(getattr(self.DM_selfie, th_attr, 0.0))}
                        for th, th_attr in ths_map.items()]
            await self.send_ws(data_dct, self.socket_info["ws_ip"])
            self._last_send = now

    async def request_th(self, th):
        """ ask for the things value
            below code is propriety and should be adapted to your specific needs in communicating obdis values to
            external websocket servers
        """
        await self.send_ws({"type": "th", "cmd": "ask", "th": th, "val": 0.0}, self.socket_info["ws_ip"])

    @property
    def my_ip(self):  # return my ip address
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sc:
                sc.connect(("8.8.8.8", 80))
                return sc.getsockname()[0]
        except Exception:
            return ""


    async def server_start(self, DM_selfie):
        """start the aiohttp websocket server"""
        self.DM_selfie = DM_selfie
        if not self.socket_info or not all(self.socket_info.get(k, False) for k in ["server_port", "remote_ips"]):
            return self.log_app.add("Web socket server not started, ?server port, ?remote ips in socket_info", tpe="error")
        app.add_routes([web.get('/ws', self.websocket_handler)])
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host=self.my_ip, port=self.socket_info["server_port"])
        await site.start()
        await self.request_th("domestic_water^purchased_water")

    async def websocket_handler(self, request):
        """aiohttp websocket request handler"""
        if request.remote not in self.socket_info.get("remote_ips", []):
            self.log_app.add(f"rejected {request.remote=}", tpe="error")
            return web.Response(text=f"<p>NOK - rejected</p>", status=400)
        ws = web.WebSocketResponse()
        try:
            await ws.prepare(request)
            async for msg in ws:
                match msg.type:
                    case aiohttp.WSMsgType.TEXT:
                        await self.reply_ws(msg.data, request.remote, ws)
                    case aiohttp.WSMsgType.ERROR:
                        self.log_app.add(f"error web socket {request.remote} {ws.exception()} {msg.type=}", tpe="error")
                    case _:
                        self.log_app.add(f"error web socket {request.remote} {msg.type=}", tpe="error")
        except ConnectionResetError as e:  # f.i. e=="Cannot write to closing transport":
            pass
        except Exception as e:
            self.log_app.add(f"error web socket {request.remote} {e=}", tpe="error")
        return ws


