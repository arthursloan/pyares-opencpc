#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /tests/test_device.py
# Project: pyares-opencpc
# Created Date: Tuesday, April 14th 2026, 4:50:59 pm
# Author(s): Arthur W. N. Sloan
# -----
# MIT License
# 
# Copyright (c) 2026 Arthur Sloan
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# 
###

from pyares_opencpc import OpenCPC

def main():
    # Replace 'COM3' with the appropriate port for your OS (e.g., '/dev/ttyUSB0' on Linux)
    # The device operates in Logging to Storage mode by default, ensure it is set 
    # to Communication Mode via the display if using serial communication over USB.
    cpc = OpenCPC(port='/dev/ttys006')
    
    try:
        print("--- OpenCPC Diagnostics ---")
        print(f"Status: {cpc.get_status()}")
        print(f"Buffer Index: {cpc.get_buffer_index()}")
        print(f"Concentration: {cpc.get_concentration()} p/cm^3")
        print(f"Averaging Time: {cpc.get_time_averaging()} s")
        print(f"Flow: {cpc.get_flow()} ccm")
        print(f"Saturator Temp: {cpc.get_saturator_temp()} °C")
        print(f"Condenser Temp: {cpc.get_condenser_temp()} °C")
        print(f"Dewpoint: {cpc.get_sample_dewpoint()} °C")
        
        # Test modifying the averaging time
        print("\nChanging averaging time to 1.0s...")
        cpc.set_time_averaging(1.0)
        print(f"New Averaging Time: {cpc.get_time_averaging()} s")

    finally:
        cpc.close()

if __name__ == "__main__":
    main()