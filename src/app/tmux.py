#!/usr/bin/python3
# encoding=utf-8

"""contains everything in relation with screens in tmux"""
import functools
import os, sys, shutil
import libtmux
import tempfile
import asyncio

from rich.live import Live
from rich.console import Console
from rich.text import Text

class TMux:
    """ manage tmux screens for the dm application"""
    def __init__(self):
        self.tmux = libtmux.Server()
        self.tmux_sessions = {"dm": {"tmp_dir": None, "files": {}, "paths": {}}}
        sf, sn = self.tmux_sessions["dm"]["files"], self.tmux_sessions["dm"]["paths"]
        for st in ["stdout", "stderr", "stdin"]:
            sf[st], sn[st] = getattr(sys, st), st
        self.log_console = self.create_session("log")
        self.tmux.cmd("switch", "-t", "dm:0")

    def create_session(self, session_name, switch=False):
        """ create a new tmux session with associated rich console, and return dict with the file objects
            assume an error session exists"""
        tmp_dir = tempfile.mkdtemp()
        self.tmux_sessions[session_name] = {"tmp_dir": tmp_dir, "files": {}, "paths": {}}
        sf, sn = self.tmux_sessions[session_name]["files"], self.tmux_sessions[session_name]["paths"]
        for st in ["stdout", "stdin"]:
            sn[st] = os.path.join(tmp_dir, st)
            os.mkfifo(sn[st])  # do not open the files yet, this will be done after the tmux session
        win_cmd = "cat {} & cat > {}".format(*[sn[st] for st in ["stdout", "stdin"]])
        for session in self.tmux.sessions:
            if session_name == session.name:
                session.kill_session()
        self.tmux.new_session(session_name=session_name, attach=False, window_command=win_cmd)
        if switch:
            self.tmux.cmd("switch",  "-t", f"{session_name}:0")
        # now open the files for writing with buffering=1
        for st in ["stdout", "stdin"]:
            sf[st] = open(sn[st], "r" if st == "stdin" else "w", buffering=1)
        stderr_file = sf["stdout"] if session_name == "log" else self.tmux_sessions["dm"]["files"]["stdout"]
        console = Console(file=sf["stdout"], force_terminal=True, stderr=stderr_file)
        # console.size = ConsoleDimensions(width=240, height=54)
        self.tmux_sessions[session_name]["console"] = console
        console.print(Text(f"Tmux session {session_name} started", style="red"))
        return console

    def close_session(self, session_name):
        """ close the tmux session and remove the tmp_dir, but skip session luce and stderr"""
        if session_name in ["dm", "stderr"]:
            return
        for session in self.tmux.sessions:
            if session.name == session_name:
                session.kill_session()
        for st in ["stdout", "stderr", "stdin"]:
            if st in self.tmux_sessions[session_name]["files"]:
                self.tmux_sessions[session_name]["files"][st].close()
            if st in self.tmux_sessions[session_name]["paths"]:
                shutil.rmtree(self.tmux_sessions[session_name]["tmp_dir"], ignore_errors=True)
        del self.tmux_sessions[session_name]

    def close_sessions(self):
        """ close the session and remove the tmp_dir"""
        for s_n, s_d in self.tmux_sessions.copy().items():
            self.close_session(s_n)

    def session(self, name: ('name of session to create', str), switch: ('session switched to in tmux?', bool) = False,
                sleep: ('seconds to wait before repeat', float) = 0.1):
        """wrapper of async tasks to create tmux sessions and consoles
           if switch is True, the session is switched to in tmux
           sleep is the time between updates of the layout
           beware: the wrapped function must be an async function AND
                   must contain 2 methods:
                   - update_layout(layout) -> Layout
                   - make_layout() -> Layout
        """
        def _session_wrap(coro):
            @functools.wraps(coro)
            async def _a_session_wrap(selfie, *args, **kwargs):
                if not all(hasattr(selfie, x) for x in ["make_layout", "update_layout"]):
                    self.log_console.print(f"!! screens.session wrap {selfie!r} must have make_layout and update_layout methods")
                selfie.console = self.create_session(name, switch=switch)
                selfie.layout = selfie.make_layout()
                with Live(selfie.layout, console=selfie.console, auto_refresh=False) as live:
                    while True:
                        await asyncio.gather(coro(selfie, *args, **kwargs), asyncio.sleep(sleep))
                        await selfie.update_layout(selfie.layout)
                        live.update(selfie.layout, refresh=True)
            return _a_session_wrap
        return _session_wrap


