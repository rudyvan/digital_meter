#!/usr/bin/python3

import aiohttp, asyncio
from aiohttp import web
import websockets
import socket
import json


app = web.Application()


class SocketApp:
    """aiohttp web application"""
    def __init__(self):
        super().__init__()
        self.ws_url = "ws://{dest_ip}:{dest_port}/ws"

    @property
    def ws_ep(self):
        """return websocket end point"""
        return "" if not all(self.socket_info.get(k, False) for k in ["dest_ip", "dest_port"]) else\
            self.ws_url.format_map(self.socket_info)

    async def send_ws(self, data, **_) -> (bool, "success"):
        """send data to a socket for a host with ip, if a server side connection exist, use it else initiate
        assume exceptions are handled outside this script"""
        to_snd = data if isinstance(data, str) else json.dumps({"type": "dm", "cmd": "data", "data": data})
        if not self.ws_ep:
            self.log_add(f"send_ws {self.remote_ip} failed: no end point")
            return False
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
                    self.log_add(f"send_ws {self.remote_ip} failed: {e}")
                    return False  # remote server is not ready after tries
                await asyncio.sleep(0.5)
            except Exception as e:
                await asyncio.sleep(1)
            finally:
                if hasattr(self, "websocket"):
                    asyncio.create_task(self.websocket.close())


    async def process_frame(self, data, ip):
        """process the frame"""
        await asyncio.sleep(1)
        return f"processed {len(data)} bytes from {ip}"


    def task_done(self, task):
        """show the result if the task ended in Exception"""
        try:
            if isinstance(task.result(), Exception):
                self.log_add(f"!!TaskDone {task.get_name()=} => {task.result()=}")
        except:  # ignore errors, such as in case no event loop exists as the program is terminating..
            pass


    async def server_init(self):
        """start the aiohttp websocket server"""
        if not self.socket_info or not all(self.socket_info.get(k, False) for k in ["server_port", "remote_ip"]):
            return self.log_add("server_init failed: no server port or remote ip")
        if self.socket_info and "remote_ip" in self.socket_info:
            self.remote_ip = self.socket_info["remote_ip"]
            app.add_routes([web.get('/ws', self.websocket_handler)])
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host="192.168.15.223", port=self.socket_info["server_port"])
        await site.start()

    async def websocket_handler(self, request):
        """aiohttp websocket request handler"""
        if request.remote != self.remote_ip:
            self.log_add(f"rejected {request.remote=}")
            return web.Response(text=f"<p>NOK - rejected</p>", status=400)
        ws = web.WebSocketResponse()
        try:
            await ws.prepare(request)
            async for msg in ws:
                match msg.type:
                    case aiohttp.WSMsgType.TEXT:
                        id = f"process_frames={len(msg.data)} of {self.remote_ip}"
                        tsk = asyncio.create_task(self.process_frame(msg.data, self.remote_ip))
                        tsk.add_done_callback(self.task_done)
                        tsk.set_name(id)
                        # no logging, it fills up to quickly
                    case aiohttp.WSMsgType.ERROR:
                        self.log_add(f"error web socket {self.remote_ip} {ws.exception()!s} {msg.type=}")
                    case _:
                        self.log_add(f"error web socket {self.remote_ip} {msg.type=}")
        except ConnectionResetError as e:  # f.i. e=="Cannot write to closing transport":
            pass
        except Exception as e:
            self.log_add(f"error web socket {self.remote_ip} {e=}")
        return ws



