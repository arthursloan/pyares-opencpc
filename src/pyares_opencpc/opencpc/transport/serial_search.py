import subprocess, sys, time, os
import serial.tools.list_ports
from dataclasses import dataclass
from .serial_legacy import LegacySerialTransport
from ..datamodel import OpenCPC

def win_get_pnp_property(pnpid, prop):
    p = subprocess.Popen('powershell.exe -ExecutionPolicy RemoteSigned -Command "Get-PnpDeviceProperty -InstanceId \''+pnpid+'\' -KeyName '+prop+'" | Select-Object -ExpandProperty Data', stdout=subprocess.PIPE)
    return p.communicate()[0].decode('ascii').strip()

def win_get_port_bus_names():
    p = subprocess.Popen('powershell.exe -ExecutionPolicy RemoteSigned -Command "Get-CimInstance -Class Win32_SerialPort | Select-Object DeviceID, PNPDeviceID"', stdout=subprocess.PIPE)
    ports = [x.strip().split() for x in p.communicate()[0].decode('ascii').split('\n')[3:] if x.strip()]
    results = {}
    for portname, pnpid in ports:
        parent = win_get_pnp_property(pnpid, 'DEVPKEY_Device_Parent')
        dev_desc = win_get_pnp_property(parent, 'DEVPKEY_Device_BusReportedDeviceDesc')
        port_desc = win_get_pnp_property(pnpid, 'DEVPKEY_Device_BusReportedDeviceDesc')
        results[portname] = (parent, dev_desc, port_desc)
    return results

def linux_get_port_bus_names():
    return {port.device: (port.usb_device_path, port.product, port.interface) for port in serial.tools.list_ports.comports()}

def get_port_bus_names():
    if sys.platform in ('win32', 'cygwin'):
        return win_get_port_bus_names()
    else:
        return linux_get_port_bus_names()

class OpenCPCSerialConnectionOption: pass

@dataclass
class OpenCPCLegacySerialConnectionOption(OpenCPCSerialConnectionOption):
    port_path: str

    def open(self, quiet=False, **k):
        port = serial.Serial(self.port_path, baudrate=115200)
        return OpenCPC(LegacySerialTransport(port, self.port_path), quiet=quiet, **k)

@dataclass
class OpenCPCV2SerialConnectionOption(OpenCPCSerialConnectionOption):
    diag_port_path: str = None
    binary_port_path: str = None

    def open(self):
        return f'v2 serial transport not implemented. would be from {self}'

def list_serial_devs():
    legacy_devices = []
    v2_devices = {}

    for port, (usb_path, devname, ifacename) in get_port_bus_names().items():
        # if devname == "OpenCPC":
        #     dev = v2_devices.get(usb_path) or OpenCPCV2SerialConnectionOption()

        #     if ifacename == "Programmatic Data Link":
        #         dev.binary_port_path = port
        #     elif ifacename == "Diagnostic Communications":
        #         dev.diag_port_path = port
        #     else:
        #         print(f"WARN: Unknown interface {repr(ifacename)} on OpenCPCV2-like port")

        #     v2_devices[usb_path] = dev

        # elif devname == "Control Processor" and ifacename == "Board CDC":

        if devname == "OpenCPC" or devname == "Control Processor" or devname == os.environ.get("OPENCPC_ALT_USBD_PRODUCT"):
            legacy_devices.append(OpenCPCLegacySerialConnectionOption(port))

    devices = legacy_devices + list(v2_devices.values())

    return devices

def open_serial_dev(retry=3, **k):
    for _ in range(retry or 1):
        devs = list_serial_devs()

        while devs:
            d = devs.pop()
            try:
                return d.open(**k)
            except IOError as e:
                print(f"Failed to open {d}: {e}")

        print("No device found; Retrying...")
        time.sleep(1)

    raise IOError("No OpenCPC found")
