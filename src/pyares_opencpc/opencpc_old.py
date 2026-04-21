#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /src/pyares_opencpc/opencpc.py
# Project: pyares-opencpc
# Created Date: Tuesday, April 14th 2026, 4:31:24 pm
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

import serial
import time
from typing import Optional, List

class OpenCPC:
    """
    Python device driver for the OpenAeros OpenCPC Condensation Particle Counter.
    """
    
    def __init__(self, port: str, timeout: float = 2.0):
        """
        Initialize the serial connection to the OpenCPC.
        
        Serial Settings based on the manual:
        - Baud Rate: 115200
        - Data Bits: 8
        - Parity: None
        - Stop Bits: 1
        - DTR/CTS: On
        """
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=115200,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                rtscts=True,  # Enables RTS/CTS (Hardware flow control)
                dsrdtr=True,  # Enables DSR/DTR (Hardware flow control)
                timeout=timeout
            )
            time.sleep(1)  # Allow time for connection initialization
            
            # Disable command echo to make parsing responses cleaner
            self.set_echo(False)
            
        except serial.SerialException as e:
            print(f"Failed to connect to OpenCPC on {port}: {e}")
            raise

    def close(self):
        """Closes the serial connection."""
        if self.ser and self.ser.is_open:
            self.ser.close()

    def _send_command(self, cmd: str) -> str:
        """
        Internal method to send a command appended with a carriage return (ASCII 13)
        and read the response.
        """
        if not self.ser.is_open:
            raise ConnectionError("Serial port is not open.")
        
        # Commands must be followed by a carriage return (\r)
        full_cmd = f"{cmd}\r"
        self.ser.write(full_cmd.encode('ascii'))
        
        # Read the response
        response = self.ser.readline().decode('ascii').strip()
        return response

    # --- Basic Commands ---

    def get_buffer_index(self) -> int:
        """Reads monotonically increasing count frame index."""
        res = self._send_command("R.BINDEX")
        return int(res) if res.isdigit() else -1

    def get_concentration(self) -> float:
        """Reads concentration at current time averaging (returns value in p/cm^3)."""
        res = self._send_command("R.CONC")
        # Example response: "3893.494 p/cm^3"
        try:
            return float(res.split()[0])
        except (ValueError, IndexError):
            return -1.0

    def get_tcr(self) -> float:
        """Reads time-averaged Threshold Count Ratio (TCR) value."""
        res = self._send_command("R.TCR")
        # Example response: "1.035 X"
        try:
            return float(res.split()[0])
        except (ValueError, IndexError):
            return -1.0

    def get_flow(self) -> float:
        """Reads current time averaged flow in ccm."""
        res = self._send_command("R.FLOW")
        # Example response: "99.754 ccm"
        try:
            return float(res.split()[0])
        except (ValueError, IndexError):
            return -1.0

    def get_saturator_temp(self) -> float:
        """Reads saturator temperature and converts from mC to Celsius."""
        res = self._send_command("R.SAT")
        # Example response: "26710 mC"
        try:
            return float(res.split()[0]) / 1000.0
        except (ValueError, IndexError):
            return -999.0

    def get_condenser_temp(self) -> float:
        """Reads condenser temperature and converts from mC to Celsius."""
        res = self._send_command("R.COND")
        # Example response: "16732 mC"
        try:
            return float(res.split()[0]) / 1000.0
        except (ValueError, IndexError):
            return -999.0

    def get_sample_dewpoint(self) -> float:
        """Reads inlet sample dewpoint in Celsius."""
        res = self._send_command("R.SDP")
        # Example response: "13.723 C"
        try:
            return float(res.split()[0])
        except (ValueError, IndexError):
            return -999.0

    def get_status(self) -> List[str]:
        """Reads the status of the instrument and returns active warnings/errors."""
        # Because status can return multiple lines, we read lines until timeout
        self._send_command("R.STATUS") # Send command directly without consuming first line
        status_lines = []
        while True:
            line = self.ser.readline().decode('ascii').strip()
            if not line:
                break
            status_lines.append(line)
        return status_lines

    def get_time_averaging(self) -> float:
        """Reads current time averaging in seconds."""
        res = self._send_command("R.FRAVG")
        # Example response: "5.0 s"
        try:
            return float(res.split()[0])
        except (ValueError, IndexError):
            return -1.0

    def get_header(self) -> str:
        """Provides header information for variable list of R.ALL."""
        return self._send_command("R.HEADER")

    def get_all_data(self) -> List[float]:
        """
        Provides comma-separated response for:
        buffer index, concentration, flow rate, TCR, Saturator temp, 
        Condenser Temp, Case temp, and sample dewpoint.
        """
        res = self._send_command("R.ALL")
        # Example: "1768,5639,834,3.406..."
        try:
            return [float(val) for val in res.split(',')]
        except ValueError:
            return []

    # --- Advanced Commands ---

    def set_time_averaging(self, seconds: float) -> bool:
        """
        Sets the current time averaging value in seconds. 
        Minimum is 0.2 and maximum is 120 seconds.
        """
        res = self._send_command(f"S.FRAVG {seconds}")
        return "Write OK" in res

    def stream_data(self, interval_sec: float):
        """
        Starts the data stream at the specified interval.
        Data must be read continually using read_stream_line() to avoid buffer overflow.
        """
        self._send_command(f"OA STREAM {interval_sec}")

    def stop_stream(self):
        """Stops the streaming function."""
        self._send_command("OA STREAM OFF")

    def read_stream_line(self) -> str:
        """Helper method to read a single line while streaming is active."""
        return self.ser.readline().decode('ascii').strip()

    def set_echo(self, state: bool):
        """Configure terminal character readback (Echo)."""
        cmd = "OA ECHO ON" if state else "OA ECHO OFF"
        self._send_command(cmd)

    def set_response(self, state: bool):
        """Configure if commands should report success."""
        cmd = "OA RESP ON" if state else "OA RESP OFF"
        self._send_command(cmd)