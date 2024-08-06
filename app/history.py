#!/usr/bin/python3
# encoding=utf-8
import os
import datetime

dir_history = "./history/"
if not os.path.exists(dir_history):
    os.makedirs(dir_history)

def prefix_history():
    mm_dd = datetime.date.today().isoformat()[5:]
    return f"{dir_history}{mm_dd}_"
