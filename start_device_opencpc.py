#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /start_device_opencpc.py
# Project: pyares-opencpc
# Created Date: Tuesday, April 14th 2026, 4:45:28 pm
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

from PyAres import DeviceSchemaEntry, AresDataType, AresDeviceService, DeviceCommandDescriptor
from pyares_opencpc import OpenCPCAresWrapper

# Settings
device_name = "OpenCPC"
device_description = "OpenAeros OpenCPC Condensation Particle Counter"
serial_port = '/dev/ttys008'
network_port = 7101

if __name__ == "__main__":
    # Initialize the Hardware Wrapper
    # Update 'COM3' to the specific USB-Serial port mapped on your OS (e.g., '/dev/ttyUSB0')
    device_wrapper = OpenCPCAresWrapper(port=serial_port)

    # Define the PyAres Device Service
    service = AresDeviceService(
        enter_safe_mode_logic=device_wrapper.safe_mode,
        get_device_state_logic=device_wrapper.get_state,
        device_name=device_name,
        description=device_description,
        version="0.1.0",
        port=network_port
    )

    # Define and Register Command: Get Concentration
    get_conc_struct = {
        'concentration':DeviceSchemaEntry(AresDataType.NUMBER,"Current particle concentration")
                        }
    get_conc_out = {
        "concentration": DeviceSchemaEntry(AresDataType.STRUCT, "Current particle concentration", "p/cm^3",struct_schema=get_conc_struct)
    }
    get_conc_desc = DeviceCommandDescriptor(
        name="Get Concentration",
        description="Reads the current particle concentration from the CPC.",
        input_schema={},
        output_schema=get_conc_out
    )
    service.add_new_command(get_conc_desc, device_wrapper.get_concentration)

    # Define and Register Command: Set Time Averaging
    set_avg_in = {
        "seconds": DeviceSchemaEntry(
            type=AresDataType.NUMBER, 
            description="Moving time window length over which concentrations are averaged.", 
            unit="s",
            constraints=[0.2, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0] # Based on limits in the manual
        )
    }
    set_avg_struct = {
        "averaging_time": DeviceSchemaEntry(AresDataType.NUMBER, "The newly applied time averaging window")
    }
    set_avg_out = {
        "averaging_time": DeviceSchemaEntry(AresDataType.STRUCT, "The newly applied time averaging window", "s")
    }
    set_avg_desc = DeviceCommandDescriptor(
        name="Set Time Averaging",
        description="Sets the moving time window over which concentration counts are averaged.",
        input_schema=set_avg_in,
        output_schema=set_avg_out
    )
    service.add_new_command(set_avg_desc, device_wrapper.set_time_averaging)

    # Define and Register Command: Get Diagnostics
    get_diag_struct = {
        "flow_rate": DeviceSchemaEntry(AresDataType.NUMBER, "Current optics flow rate", "ccm"),
        "saturator_temperature": DeviceSchemaEntry(AresDataType.NUMBER, "Current saturator temperature", "Celsius"),
        "condenser_temperature": DeviceSchemaEntry(AresDataType.NUMBER, "Current condenser temperature", "Celsius"),
        "tcr": DeviceSchemaEntry(AresDataType.NUMBER, "Threshold Count Ratio (TCR)", "Ratio")
    }
    get_diag_out = {
        "diagnostics":DeviceSchemaEntry(AresDataType.STRUCT,"Diagnostic Information")
    }
    get_diag_desc = DeviceCommandDescriptor(
        name="Get Diagnostics",
        description="Retrieves the flow rate, temperatures, and TCR metrics from the CPC.",
        input_schema={},
        output_schema=get_diag_out
    )
    service.add_new_command(get_diag_desc, device_wrapper.get_diagnostics)

    # Define and Register Command: Get Buffer Index
    get_buffer_struct = {
        "buffer_index": DeviceSchemaEntry(AresDataType.NUMBER,"Monotonically increasing count frame index")
    }
    get_buffer_index_out = {
        "buffer_index": DeviceSchemaEntry(AresDataType.STRUCT, "Monotonically increasing count frame index", "",struct_schema=get_buffer_struct)
    }
    get_buffer_index_desc = DeviceCommandDescriptor(
        name="Get Buffer Index",
        description="Reads monotonically increasing count frame index.",
        input_schema={},
        output_schema=get_buffer_index_out
    )
    service.add_new_command(get_buffer_index_desc, device_wrapper.get_buffer_index)

    # Define and Register Command: Get TCR
    get_tcr_struct = {
        "tcr":DeviceSchemaEntry(AresDataType.NUMBER,"Time-averaged Threshold Count Ratio")
    }
    get_tcr_out = {
        "tcr": DeviceSchemaEntry(AresDataType.STRUCT, "Time-averaged Threshold Count Ratio", "Ratio",struct_schema=get_tcr_struct)
    }
    get_tcr_desc = DeviceCommandDescriptor(
        name="Get TCR",
        description="Reads time-averaged Threshold Count Ratio (TCR) value.",
        input_schema={},
        output_schema=get_tcr_out
    )
    service.add_new_command(get_tcr_desc, device_wrapper.get_tcr)

    # Define and Register Command: Get Flow Rate
    get_flow_struct = {
        "flow_rate":DeviceSchemaEntry(AresDataType.NUMBER,"Current time averaged flow")
    }
    get_flow_out = {
        "flow_rate": DeviceSchemaEntry(AresDataType.STRUCT, "Current time averaged flow", "ccm")
    }
    get_flow_desc = DeviceCommandDescriptor(
        name="Get Flow Rate",
        description="Reads current time averaged flow in ccm.",
        input_schema={},
        output_schema=get_flow_out
    )
    service.add_new_command(get_flow_desc, device_wrapper.get_flow)

    # Define and Register Command: Get Saturator Temperature
    get_sat_temp_struct = {
        "saturator_temperature": DeviceSchemaEntry(AresDataType.NUMBER, "Current saturator temperature")
    }
    get_sat_temp_out = {
        "saturator_temperature": DeviceSchemaEntry(AresDataType.STRUCT, "Current saturator temperature", "Celsius",struct_schema=get_sat_temp_struct)
    }
    get_sat_temp_desc = DeviceCommandDescriptor(
        name="Get Saturator Temperature",
        description="Reads saturator temperature and converts from mC to Celsius.",
        input_schema={},
        output_schema=get_sat_temp_out
    )
    service.add_new_command(get_sat_temp_desc, device_wrapper.get_saturator_temp)

    # Define and Register Command: Get Condenser Temperature
    get_cond_temp_struct = {
        "saturator_temperature": DeviceSchemaEntry(AresDataType.NUMBER, "Current condenser temperature")
    }
    get_cond_temp_out = {
        "condenser_temperature": DeviceSchemaEntry(AresDataType.STRUCT, "Current condenser temperature", "Celsius",struct_schema=get_cond_temp_struct)
    }
    get_cond_temp_desc = DeviceCommandDescriptor(
        name="Get Condenser Temperature",
        description="Reads condenser temperature and converts from mC to Celsius.",
        input_schema={},
        output_schema=get_cond_temp_out
    )
    service.add_new_command(get_cond_temp_desc, device_wrapper.get_condenser_temp)

    # Define and Register Command: Get Sample Dewpoint
    get_dewpoint_struct ={
        "sample_dewpoint": DeviceSchemaEntry(AresDataType.NUMBER, "Inlet sample dewpoint")
    }
    get_dewpoint_out = {
        "sample_dewpoint": DeviceSchemaEntry(AresDataType.STRUCT, "Inlet sample dewpoint", "Celsius",struct_schema=get_dewpoint_struct)
    }
    get_dewpoint_desc = DeviceCommandDescriptor(
        name="Get Sample Dewpoint",
        description="Reads inlet sample dewpoint in Celsius.",
        input_schema={},
        output_schema=get_dewpoint_out
    )
    service.add_new_command(get_dewpoint_desc, device_wrapper.get_sample_dewpoint)

    # Define and Register Command: Get Status
    get_status_struct = {
        "status": DeviceSchemaEntry(AresDataType.STRING, "Active warnings/errors from the instrument",)
    }
    get_status_out = {
        "status": DeviceSchemaEntry(AresDataType.STRUCT, "Active warnings/errors from the instrument", "String",struct_schema=get_status_struct)
    }
    get_status_desc = DeviceCommandDescriptor(
        name="Get Status",
        description="Reads the status of the instrument and returns active warnings/errors.",
        input_schema={},
        output_schema=get_status_out
    )
    service.add_new_command(get_status_desc, device_wrapper.get_status)

    # Define and Register Command: Get Time Averaging
    get_time_avg_struct = {
         "averaging_time": DeviceSchemaEntry(AresDataType.NUMBER, "Current time averaging in seconds")
    }
    get_time_avg_out = {
        "averaging_time": DeviceSchemaEntry(AresDataType.STRUCT, "Current time averaging in seconds", "s",struct_schema=get_time_avg_struct)
    }
    get_time_avg_desc = DeviceCommandDescriptor(
        name="Get Time Averaging",
        description="Reads current time averaging in seconds.",
        input_schema={},
        output_schema=get_time_avg_out
    )
    service.add_new_command(get_time_avg_desc, device_wrapper.get_time_averaging)

    # Define and Register Command: Get Header
    get_header_struct = {
        "header": DeviceSchemaEntry(AresDataType.STRING, "Header information for variable list")
    }
    get_header_out = {
        "header": DeviceSchemaEntry(AresDataType.STRUCT, "Header information for variable list", "",struct_schema=get_header_struct)
    }
    get_header_desc = DeviceCommandDescriptor(
        name="Get Header",
        description="Provides header information for variable list of R.ALL.",
        input_schema={},
        output_schema=get_header_out
    )
    service.add_new_command(get_header_desc, device_wrapper.get_header)

    # Define and Register Command: Get All Data
    get_all_data_struct = {
        "all_data": DeviceSchemaEntry(AresDataType.NUMBER_ARRAY, "All data points from R.ALL command")
    }
    get_all_data_out = {
        "all_data": DeviceSchemaEntry(AresDataType.STRUCT, "All data points from R.ALL command", "Float",struct_schema=get_all_data_struct)
    }
    get_all_data_desc = DeviceCommandDescriptor(
        name="Get All Data",
        description="Provides comma-separated response for all data points.",
        input_schema={},
        output_schema=get_all_data_out
    )
    service.add_new_command(get_all_data_desc, device_wrapper.get_all_data)

    # TODO: Need to figure out how ARES OS is going to handle streamed data like this
    # # Define and Register Command: Stream Data
    # stream_data_in = {
    #     "interval_sec": DeviceSchemaEntry(AresDataType.NUMBER, "Interval between data points in seconds", "s")
    # }
    # stream_data_out = {
    #     "streaming": DeviceSchemaEntry(AresDataType.BOOLEAN, "Streaming status", ""),
    #     "interval": DeviceSchemaEntry(AresDataType.NUMBER, "Stream interval", "s")
    # }
    # stream_data_desc = DeviceCommandDescriptor(
    #     name="Stream Data",
    #     description="Starts the data stream at the specified interval.",
    #     input_schema=stream_data_in,
    #     output_schema=stream_data_out
    # )
    # service.add_new_command(stream_data_desc, device_wrapper.stream_data)

    # # Define and Register Command: Stop Stream
    # stop_stream_out = {
    #     "streaming": DeviceSchemaEntry(AresDataType.BOOLEAN, "Streaming status", "")
    # }
    # stop_stream_desc = DeviceCommandDescriptor(
    #     name="Stop Stream",
    #     description="Stops the streaming function.",
    #     input_schema={},
    #     output_schema=stop_stream_out
    # )
    # service.add_new_command(stop_stream_desc, device_wrapper.stop_stream)

    # # Define and Register Command: Read Stream Line
    # read_stream_line_out = {
    #     "stream_line": DeviceSchemaEntry(AresDataType.STRING, "Single line from stream", "")
    # }
    # read_stream_line_desc = DeviceCommandDescriptor(
    #     name="Read Stream Line",
    #     description="Helper method to read a single line while streaming is active.",
    #     input_schema={},
    #     output_schema=read_stream_line_out
    # )
    # service.add_new_command(read_stream_line_desc, device_wrapper.read_stream_line)

    # Define and Register Command: Set Echo
    set_echo_in = {
        "state": DeviceSchemaEntry(AresDataType.BOOLEAN, "Echo state (True/False)", "")
    }
    set_echo_struct = {
        "echo": DeviceSchemaEntry(AresDataType.BOOLEAN,"Echo sate")
    }
    set_echo_out = {
        "echo": DeviceSchemaEntry(AresDataType.STRUCT, "Echo state", "",struct_schema=set_echo_struct)
    }
    set_echo_desc = DeviceCommandDescriptor(
        name="Set Echo",
        description="Configure terminal character readback (Echo).",
        input_schema=set_echo_in,
        output_schema=set_echo_out
    )
    service.add_new_command(set_echo_desc, device_wrapper.set_echo)

    # Define and Register Command: Set Response
    set_response_in = {
        "state": DeviceSchemaEntry(AresDataType.BOOLEAN, "Response state (True/False)", "")
    }
    set_response_struct = {
         "response": DeviceSchemaEntry(AresDataType.BOOLEAN, "Response state")
    }
    set_response_out = {
        "response": DeviceSchemaEntry(AresDataType.STRUCT, "Response state", "",struct_schema=set_response_struct)
    }
    set_response_desc = DeviceCommandDescriptor(
        name="Set Response",
        description="Configure if commands should report success.",
        input_schema=set_response_in,
        output_schema=set_response_out
    )
    service.add_new_command(set_response_desc, device_wrapper.set_response)

    # 6. Start the Service
    print("OpenCPC PyAres Device Service running. Waiting for ARES commands...")
    try:
        service.start()
    except KeyboardInterrupt:
        print("Shutting down service...")
    finally:
        device_wrapper.cpc.close()