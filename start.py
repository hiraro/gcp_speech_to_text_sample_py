#!/usr/bin/env python3
# coding: UTF-8
import subprocess
import os

script_path = os.path.dirname(os.path.abspath(__file__))
subprocess.run("{}/start.sh".format(script_path),
               shell=True,
               stdin=subprocess.PIPE,
               stdout=subprocess.PIPE,
               stderr=subprocess.PIPE)
