#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /tests/sim_opencpc.py
# Project: pyares-opencpc
# Created Date: Tuesday, April 14th 2026, 4:56:50 pm
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
import math
import random
import argparse

class SimulatedOpenCPC:
    def __init__(self, port: str):
        # Open the serial port with a short timeout so we can also handle streaming
        self.ser = serial.Serial(port, 115200, timeout=0.1)
        print(f"OpenCPC Simulator listening on {port}...")

        # Device State Variables
        self.buffer_index = 0
        self.echo_on = True
        self.responses_on = True
        self.time_averaging_sec = 5.0
        self.stream_interval: float = None
        self.last_stream_time = 0.0

        # Simulation Physics Constants
        self.period_seconds = 120.0  # 2-minute period for oscillations
        self.omega = (2 * math.pi) / self.period_seconds

    def generate_simulated_state(self) -> dict:
        """
        Samples simulated sensor values using time-varying sine waves (minutes-scale period)
        with added random Gaussian noise.
        """
        t = time.time()
        
        # Base value + Sinusoidal oscillation + Random Noise
        conc = 5000.0 + 2000.0 * math.sin(self.omega * t) + random.gauss(0, 50.0)
        flow = 100.0 + 1.5 * math.sin(self.omega * t + 1.0) + random.gauss(0, 0.2)
        tcr = 1.0 + 0.1 * math.sin(self.omega * t + 2.0) + random.gauss(0, 0.02)
        
        sat_temp = 22.0 + 1.0 * math.sin(self.omega * t + 3.0) + random.gauss(0, 0.05)
        cond_temp = 12.0 + 1.0 * math.sin(self.omega * t + 4.0) + random.gauss(0, 0.05)
        dewpoint = 10.0 + 2.0 * math.sin(self.omega * t + 5.0) + random.gauss(0, 0.1)
        case_temp = 21.5 + 0.5 * math.sin(self.omega * t + 6.0) + random.gauss(0, 0.05)

        return {
            "conc": max(0.0, conc),  # Prevent negative concentrations
            "flow": flow,
            "tcr": tcr,
            "sat_mc": int(sat_temp * 1000),    # milliCelsius
            "cond_mc": int(cond_temp * 1000),  # milliCelsius
            "case_c": case_temp,
            "dewpoint": dewpoint
        }

    def process_command(self, cmd: str):
        """Parses an incoming command and generates the appropriate CPC response."""
        state = self.generate_simulated_state()
        response = ""

        # --- Basic Commands ---
        if cmd == "R.BINDEX":
            response = str(self.buffer_index)
        elif cmd == "R.CONC":
            response = f"{state['conc']:.3f} p/cm^3"
        elif cmd == "R.TCR":
            response = f"{state['tcr']:.3f} X"
        elif cmd == "R.FLOW":
            response = f"{state['flow']:.3f} ccm"
        elif cmd == "R.SAT":
            response = f"{state['sat_mc']} mC"
        elif cmd == "R.COND":
            response = f"{state['cond_mc']} mC"
        elif cmd == "R.SDP":
            response = f"{state['dewpoint']:.3f} C"
        elif cmd == "R.STATUS":
            response = "- Ready\n- No errors"
        elif cmd == "R.FRAVG":
            response = f"{self.time_averaging_sec:.1f} s"
        elif cmd == "R.HEADER":
            response = "Buffer index (frames), Particle Conc., Flow (ccm), TCR, Sat Temp (mC), Cond Temp (mC), Case Temp (C), Sample Dewpoint (C)"
        elif cmd == "R.ALL":
            response = f"{self.buffer_index},{state['conc']:.3f},{state['flow']:.3f},{state['tcr']:.3f},{state['sat_mc']},{state['cond_mc']},{state['case_c']:.3f},{state['dewpoint']:.3f}"

        # --- Advanced Commands ---
        elif cmd.startswith("S.FRAVG "):
            try:
                val = float(cmd.split(" ")[1])
                self.time_averaging_sec = max(0.2, min(120.0, val))
                response = "Write OK"
            except ValueError:
                response = "Error"
        elif cmd == "OA STREAM OFF":
            self.stream_interval = None
            response = "Stream disabled"
        elif cmd.startswith("OA STREAM "):
            try:
                val = float(cmd.split(" ")[2])
                self.stream_interval = val
                self.last_stream_time = time.time()
                response = f"Stream rate set to {val}"
            except ValueError:
                response = "Error"
        elif cmd == "OA ECHO OFF":
            self.echo_on = False
            response = "Echo now OFF"
        elif cmd == "OA ECHO ON":
            self.echo_on = True
            response = "Echo now ON"
        elif cmd == "OA RESP OFF":
            self.responses_on = False
        elif cmd == "OA RESP ON":
            self.responses_on = True
            response = "Responses are now ON"
        else:
            response = "Unknown command"

        self.send_response(cmd, response)
        self.buffer_index += 1

    def send_response(self, cmd: str, response: str):
        """Handles formatting, echo logic, and serial write operations."""
        out = ""
        if self.echo_on:
            out += f"{cmd}\n"
        if self.responses_on and response:
            out += f"{response}\n"
        
        if out:
            self.ser.write(out.encode('ascii'))

    def run(self):
        """Main execution loop for reading commands and managing data streams."""
        try:
            while True:
                # 1. Check for incoming commands
                if self.ser.in_waiting > 0:
                    # The driver uses carriage return '\r' as the terminator
                    raw_data = self.ser.read_until(b'\r')
                    cmd_str = raw_data.decode('ascii').strip()
                    if cmd_str:
                        print(f"Received: {cmd_str}")
                        self.process_command(cmd_str)

                # 2. Check if we need to emit a streaming data point
                if self.stream_interval is not None:
                    now = time.time()
                    if (now - self.last_stream_time) >= self.stream_interval:
                        state = self.generate_simulated_state()
                        stream_line = f"{self.buffer_index},{state['conc']:.3f},{state['flow']:.3f},{state['tcr']:.3f},{state['sat_mc']},{state['cond_mc']},{state['case_c']:.3f},{state['dewpoint']:.3f}\n"
                        self.ser.write(stream_line.encode('ascii'))
                        self.buffer_index += 1
                        self.last_stream_time = now

        except KeyboardInterrupt:
            print("\nShutting down simulator...")
        finally:
            self.ser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Virtual OpenCPC Hardware Simulator")
    parser.add_argument("port", help="The serial port to bind the simulator to (e.g. COM4 or /dev/pts/1)")
    args = parser.parse_args()

    simulator = SimulatedOpenCPC(args.port)
    simulator.run()