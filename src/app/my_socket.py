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

    @property
    def ws_ep(self):
        """return websocket end point"""
        if not hasattr(self, "_ws_ep"):
            if not all(self.socket_info.get(k, False) for k in ["dest_ip", "dest_port", "ws_url"]):
                self.log_app.add(f"send_ws failed as no end point")
                return ""
        self._ws_ep = self.socket_info["ws_url"].format_map(self.socket_info)
        return self._ws_ep

    def json_it(self, dct):
        """ dump the data in json format"""
        encode_JSON = lambda x: self.ts_str(x) if isinstance(x, datetime.datetime) else repr(x)
        return json.dumps(dct, indent=4, sort_keys=True, default=encode_JSON)

    async def send_ws(self, data, dest_ip) -> (bool, "success"):
        """send data to a socket for a host with ip, port, and path"""
        self.log_app.add(f"send_ws bytes")
        self.socket_info["dest_ip"] = dest_ip

        if not self.ws_ep:
            return False
        to_snd = data if isinstance(data, str) else self.json_it(data)
        self.log_app.add(f"send_ws {self.ws_ep} {len(to_snd)=} bytes")
        tries = 0
        while True:
            try:
                async with websockets.connect(self.ws_ep) as self.websocket:
                    await self.websocket.send_json(data)
                    return True
            except asyncio.CancelledError:
                return False
            except (asyncio.TimeoutError, ConnectionRefusedError, ConnectionError, socket.error,
                    websockets.exceptions.InvalidMessage) as e:
                tries += 1
                if tries > 3:
                    self.log_app.add(f"send_ws {self.ws_ep} failed: {e}")
                    return False  # remote server is not ready after tries
                await asyncio.sleep(0.5)
            except Exception as e:
                await asyncio.sleep(1)
            finally:
                # cannot do wrong with this, as it is a finally
                if hasattr(self, "websocket"):
                    asyncio.create_task(self.websocket.close())


    async def reply_ws(self, data, ip, ws):
        """reply to a websocket server request
        2024-08-08 18:12:23 PI-Energy !Reply? <PI-DM> for <electricity^fluvius_day> -> {'type': 'th', 'cmd': 'ask', 'th': 'electricity^fluvius_day', 'val': None}
        2024-08-08 18:12:23 PI-Energy !Reply? <PI-DM> for <electricity^fluvius_night> -> {'type': 'th', 'cmd': 'ask', 'th': 'electricity^fluvius_night', 'val': None}
        2024-08-08 18:12:23 PI-Energy !Reply? <PI-DM> for <gas^purchased_gas> -> {'type': 'th', 'cmd': 'ask', 'th': 'gas^purchased_gas', 'val': None}
        2024-08-08 18:12:23 PI-Energy !Reply? <PI-DM> for <domestic_water^pidpa> -> {'type': 'th', 'cmd': 'ask', 'th': 'domestic_water^pidpa', 'val': None}
        """
        data_dct = json.loads(data)
        data_dct["cmd"] = "reply"
        data_dct["val"] = 0.0
        await ws.send_json(data_dct)
        asyncio.create_task(self.send_ws(data_dct, ip))
        self.log_app.add(f"{ip=} -> {data} <-- {data_dct}")
        return


    @property
    def my_ip(self):  # return my ip address
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sc:
                sc.connect(("8.8.8.8", 80))
                return sc.getsockname()[0]
        except Exception:
            return ""


    async def server_start(self):
        """start the aiohttp websocket server"""
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


