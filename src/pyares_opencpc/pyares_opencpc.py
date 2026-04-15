#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /src/pyares_opencpc/pyares_opencpc.py
# Project: pyares-opencpc
# Created Date: Tuesday, April 14th 2026, 4:42:51 pm
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

from typing import Dict, Any
from .opencpc import OpenCPC

class OpenCPCAresWrapper:
    """
    A wrapper class that interfaces the OpenCPC Python driver with PyAres.
    """
    def __init__(self, port: str):
        print(f"Connecting to OpenCPC on {port}...")
        self.cpc = OpenCPC(port=port)
    
    def get_state(self) -> Dict[str, Any]:
        """
        Required by PyAres: Provides the current status/state of the device 
        for continuous logging and tracking by the ARES system.
        """
        return {
            "concentration": self.cpc.get_concentration(),
            "flow_rate": self.cpc.get_flow(),
            "saturator_temperature": self.cpc.get_saturator_temp(),
            "condenser_temperature": self.cpc.get_condenser_temp(),
            "sample_dewpoint": self.cpc.get_sample_dewpoint(),
            "tcr": self.cpc.get_tcr(),
            "averaging_time": self.cpc.get_time_averaging()
        }
    
    def safe_mode(self) -> None:
        """
        Required by PyAres: A safety fallback to put the device into a known safe state.
        For the CPC, we can stop any active data streaming as a precaution.
        """
        print("[Safety] Enter safe mode triggered! Stopping active data streams.")
        self.cpc.stop_stream()

    # --- ARES Command Methods ---
    
    def get_concentration(self) -> float:
        """ARES Command: Retrieves the current particle concentration."""
        print("[Info] Recevied Command get_concentration!")
        return self.cpc.get_concentration()

    def set_time_averaging(self, seconds: float) -> float:
        """ARES Command: Sets the time averaging window."""
        self.cpc.set_time_averaging(seconds)
        print("[Info] Received Command set_time_averaging!")
        return self.cpc.get_time_averaging()

    def get_diagnostics(self) -> Dict[str, Any]:
        """ARES Command: Retrieves all core diagnostic metrics at once."""
        print("[Info] Received Command get_diagnostics!")
        return {
            "flow_rate": self.cpc.get_flow(),
            "saturator_temperature": self.cpc.get_saturator_temp(),
            "condenser_temperature": self.cpc.get_condenser_temp(),
            "tcr": self.cpc.get_tcr()
        }
    
    def get_buffer_index(self) -> int:
        """ARES Command: Reads monotonically increasing count frame index."""
        print("[Info] Received Command get_buffer_index!")
        return self.cpc.get_buffer_index()

    def get_tcr(self) -> float:
        """ARES Command: Reads time-averaged Threshold Count Ratio (TCR) value."""
        print("[Info] Received Command get_tcr!")
        return self.cpc.get_tcr()

    def get_flow(self) -> float:
        """ARES Command: Reads current time averaged flow in ccm."""
        print("[Info] Received Command get_flow!")
        return self.cpc.get_flow()

    def get_saturator_temp(self) -> float:
        """ARES Command: Reads saturator temperature and converts from mC to Celsius."""
        print("[Info] Received Command get_saturator_temp!")
        return self.cpc.get_saturator_temp()

    def get_condenser_temp(self) -> float:
        """ARES Command: Reads condenser temperature and converts from mC to Celsius."""
        print("[Info] Received Command get_condenser_temp!")
        return self.cpc.get_condenser_temp()

    def get_sample_dewpoint(self) -> float:
        """ARES Command: Reads inlet sample dewpoint in Celsius."""
        print("[Info] Received Command get_sample_dewpoint!")
        return self.cpc.get_sample_dewpoint()

    def get_status(self) -> list[str]:
        """ARES Command: Reads the status of the instrument and returns active warnings/errors."""
        print("[Info] Received Command get_status!")
        return self.cpc.get_status()

    def get_time_averaging(self) -> float:
        """ARES Command: Reads current time averaging in seconds."""
        print("[Info] Received Command get_time_averaging!")
        return self.cpc.get_time_averaging()

    def get_header(self) -> str:
        """ARES Command: Provides header information for variable list of R.ALL."""
        print("[Info] Received Command get_header!")
        return self.cpc.get_header()

    def get_all_data(self) -> list[float]:
        """ARES Command: Provides comma-separated response for all data points."""
        print("[Info] Received Command get_all_data!")
        return self.cpc.get_all_data()

    def stream_data(self, interval_sec: float) -> Dict[str, Any]:
        """ARES Command: Starts the data stream at the specified interval."""
        print("[Info] Received Command stream_data!")
        self.cpc.stream_data(interval_sec)
        return {
            "streaming": True,
            "interval": interval_sec
        }

    def stop_stream(self) -> Dict[str, Any]:
        """ARES Command: Stops the streaming function."""
        print("[Info] Received Command stop_stream!")
        self.cpc.stop_stream()
        return {
            "streaming": False
        }

    def read_stream_line(self) -> str:
        """ARES Command: Helper method to read a single line while streaming is active."""
        print("[Info] Received Command read_stream_line!")
        return self.cpc.read_stream_line()

    def set_echo(self, state: bool) -> bool:
        """ARES Command: Configure terminal character readback (Echo)."""
        print("[Info] Received Command set_echo!")
        self.cpc.set_echo(state)
        return state

    def set_response(self, state: bool) -> bool:
        """ARES Command: Configure if commands should report success."""
        print("[Info] Received Command set_response!")
        self.cpc.set_response(state)
        return state