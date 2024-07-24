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
    def __init__(self):
        super().__init__()

    @property
    def ws_ep(self):
        """return websocket end point"""
        return "" if not all(self.socket_info.get(k, False) for k in ["dest_ip", "dest_port", "ws_url"]) else\
            self.socket_info["ws_url"].format_map(self.socket_info)

    async def send_ws(self, data, **_) -> (bool, "success"):
        """send data to a socket for a host with ip, port, and path"""
        if not self.ws_ep:
            self.log_add(f"send_ws failed as no end point")
            return False
        encode_JSON = lambda x: self.ts_str(x) if isinstance(x, datetime.datetime) else repr(x)
        to_snd = data if isinstance(data, str) else json.dumps({"type": "dm", "cmd": "data", "data": data},
                                                               indent=4, sort_keys=True, default=encode_JSON)
        self.log_add(f"send_ws {self.ws_ep} {len(to_snd)=} bytes")
        tries = 0
        while True:
            try:
                async with websockets.connect(self.ws_ep) as self.websocket:
                    await self.websocket.send(to_snd)
                    return True
            except asyncio.CancelledError:
                return False
            except (asyncio.TimeoutError, ConnectionRefusedError, ConnectionError, socket.error,
                    websockets.exceptions.InvalidMessage) as e:
                tries += 1
                if tries > 3:
                    self.log_add(f"send_ws {self.ws_ep} failed: {e}")
                    return False  # remote server is not ready after tries
                await asyncio.sleep(0.5)
            except Exception as e:
                await asyncio.sleep(1)
            finally:
                # cannot do wrong with this, as it is a finally
                if hasattr(self, "websocket"):
                    asyncio.create_task(self.websocket.close())


    async def process_frame(self, data, ip):
        """process the frame"""
        await asyncio.sleep(1)
        if data == "?":
            await self.send_ws(self.data)
        self.log_add(f"processed {len(data)} bytes from {ip}")
        return


    def task_done(self, task):
        """show the result if the task ended in Exception"""
        try:
            if isinstance(task.result(), Exception):
                self.log_add(f"!!TaskDone {task.get_name()=} => {task.result()=}")
        except:  # ignore errors, such as in case no event loop exists as the program is terminating..
            pass

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
            return self.log_add("Web socket server not started, ?server port, ?remote ips in socket_info")
        app.add_routes([web.get('/ws', self.websocket_handler)])
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host=self.my_ip, port=self.socket_info["server_port"])
        await site.start()

    async def websocket_handler(self, request):
        """aiohttp websocket request handler"""
        if request.remote not in self.socket_info.get("remote_ips", []):
            self.log_add(f"rejected {request.remote=}")
            return web.Response(text=f"<p>NOK - rejected</p>", status=400)
        ws = web.WebSocketResponse()
        try:
            await ws.prepare(request)
            async for msg in ws:
                match msg.type:
                    case aiohttp.WSMsgType.TEXT:
                        id = f"process_frames={len(msg.data)} of {request.remote}"
                        tsk = asyncio.create_task(self.process_frame(msg.data, request.remote))
                        tsk.add_done_callback(self.task_done)
                        tsk.set_name(id)
                        # no logging, it fills up to quickly
                    case aiohttp.WSMsgType.ERROR:
                        self.log_add(f"error web socket {request.remote} {ws.exception()} {msg.type=}")
                    case _:
                        self.log_add(f"error web socket {request.remote} {msg.type=}")
        except ConnectionResetError as e:  # f.i. e=="Cannot write to closing transport":
            pass
        except Exception as e:
            self.log_add(f"error web socket {request.remote} {e=}")
        return ws



