#!/usr/bin/python3

import aiohttp, asyncio
from aiohttp import web
import websockets
import socket
import json
import datetime

app = web.Application()

from digital_meter.config import ths_map


class SocketApp:
    """aiohttp web application"""
    def __init__(self, socket_info, log_app, *args, **kwargs):
        self.socket_info = socket_info
        self.log_app = log_app
        super().__init__(*args, **kwargs)

    def json_it(self, dct):
        """ dump the data in json format"""
        encode_JSON = lambda x: self.ts_str(x) if isinstance(x, datetime.datetime) else repr(x)
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
        self.log_app.add(f"Websocket Queue {ip}: {len(data)} bytes")
        if self._send_queues[ip].full():
            return self.log_app.log_it_info(f"Websocket Queue {ip} full", tpe="error")
        # could add test for not sending repeat data
        await self._send_queues[ip].put(data if isinstance(data, str) else self.json_it(data))

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
                self.log_app.add(f"Websocket {end_p} --> {data}")
                await websocket.send(data)
            except websockets.ConnectionClosed:
                continue

    def my_assert(self, c, m):
        """ return assert c and log error m if fails """
        if not (ret_val := bool(c)):
            self.log_app.log_it_info(m, tpe="error")
        return ret_val


    async def reply_ws(self, data, ip, ws):
        """ reply to a websocket server request
            below code is propriety and should be adapted to your specific needs in communicating obdis values to external websocket servers
        """
        self.log_app.add(f"Websocket Server: rcv from {ip}: {data}")
        all_keys = ["type", "cmd", "th", "val"]
        data_dct = json.loads(data)
        if not self.my_assert(all(x in data_dct for x in all_keys),
                              f"Websocket {ip} ? data missing keys {all_keys} not in {data_dct}") or \
           not self.my_assert(th := data_dct["th"] in ths_map, f"Websocket {ip} ?? {th=} not in {ths_map}"):
            return
        data_dct["cmd"] = "reply"
        obdis_th = self.DM_selfie.ths_map[th]
        data_dct["val"] = getattr(self.DM_selfie, obdis_th, 0.0)
        return await self.send_ws(data_dct, ip)


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
            return self.log_app.add("Web socket server not started, ?server port, ?remote ips in socket_info")
        app.add_routes([web.get('/ws', self.websocket_handler)])
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host=self.my_ip, port=self.socket_info["server_port"])
        await site.start()

    async def websocket_handler(self, request):
        """aiohttp websocket request handler"""
        if request.remote not in self.socket_info.get("remote_ips", []):
            self.log_app.add(f"rejected {request.remote=}")
            return web.Response(text=f"<p>NOK - rejected</p>", status=400)
        ws = web.WebSocketResponse()
        try:
            await ws.prepare(request)
            async for msg in ws:
                match msg.type:
                    case aiohttp.WSMsgType.TEXT:
                        await self.reply_ws(msg.data, request.remote, ws)
                    case aiohttp.WSMsgType.ERROR:
                        self.log_app.add(f"error web socket {request.remote} {ws.exception()} {msg.type=}")
                    case _:
                        self.log_app.add(f"error web socket {request.remote} {msg.type=}")
        except ConnectionResetError as e:  # f.i. e=="Cannot write to closing transport":
            pass
        except Exception as e:
            self.log_app.add(f"error web socket {request.remote} {e=}")
        return ws


