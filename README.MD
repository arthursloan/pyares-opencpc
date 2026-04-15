# PyAres OpenCPC Driver

**pyares_opencpc** is the official Python device driver and PyAres compatibility layer for the [OpenAeros OpenCPC](https://www.openaeros.com) Condensation Particle Counter. 

This package provides a robust, native Python interface to communicate with the physical OpenCPC hardware over serial, alongside a pre-configured `AresDeviceService` wrapper. This allows the OpenCPC to seamlessly integrate into an ARES (Autonomous REsearch System) self-driving laboratory environment.

## Features
* **Native Python Driver (`OpenCPC`)**: Complete implementation of the OpenCPC serial protocol, supporting all basic and advanced hardware commands (e.g., fetching concentrations, setting averaging times, reading diagnostics).
* **ARES Integration (`OpenCPCAresWrapper`)**: A fully operational PyAres device service that exposes the OpenCPC's capabilities to ARES as easily consumable network commands.
* **Continuous State Monitoring**: Periodically logs hardware states (flow rates, temperatures, dewpoints) back to the ARES framework.
* **Hardware Simulator (`sim_opencpc.py`)**: A mock serial device for testing and development when physical hardware is unavailable.

## Installation & Environment Setup

This project requires **Python >=3.10**. A dedicated environment is highly recommended to keep module dependences for differnt PyAres services from causing issues.

### Option A: Using Anaconda / Miniconda / Miniforge (Recommended)

1.  **Create the environment:**
    ```bash
    conda create -n pyares_opencpc python=3.10 pip pyserial
    ```
2.  **Activate the environment:**
    ```bash
    conda activate pyares_opencpc
    ```
3.  **Install the package:**
    Navigate to the project root directory and run:
    ```bash
    pip install .
    ```
    *Note: This will automatically install dependencies listed in `pyproject.toml`.*

### Option B: Using Python venv

1.  **Ensure you have Python >=3.10 installed:**
    Check your version:
    ```bash
    python3 --version
    ```
2.  **Create the virtual environment:**
    ```bash
    python3 -m venv pyares_opencpc_venv
    ```
3.  **Activate the environment:**
    * **Windows:**
        ```powershell
        .\pyares_opencpc_venv\Scripts\activate
        ```
    * **Linux/macOS:**
        ```bash
        source pyares_opencpc_venv/bin/activate
        ```
4.  **Install the package:**
    ```bash
    pip install .
    ```

## Usage: ARES Device Service

The easiest way to connect your OpenCPC to your ARES network is by running the included device service script. 

1. Connect your OpenCPC to your computer via the provided USB-C cable.
2. Identify the serial port assigned to the device (e.g., `COM3` on Windows, or `/dev/ttyUSB0` on Linux).
3. Open `start_device_opencpc.py` and update the `serial_port` variable:
   ```python
   serial_port = 'COM3' # Update this to match your system
   ```
4. Start the service:
   ```bash
   python start_device_opencpc.py
   ```

The device will boot up, establish a connection, and begin listening for ARES commands on port `7101` by default, but this can be changed by editing the port in `start_device_opencpc.py`.

### Exposed ARES Commands
Once connected, the following commands are automatically registered with the ARES system:
* **Get Concentration**: Returns the current particle concentration ($p/cm^3$).
* **Set Time Averaging**: Adjusts the moving time window (0.2s - 120s) over which concentration counts are averaged.
* **Get Diagnostics**: Retrieves core metrics (flow rate, saturator temperature, condenser temperature, TCR).
* **Get Status**: Returns active hardware warnings or errors.
* **Get Flow Rate / Temperatures / Dewpoint / TCR**: Individual commands to pull specific physical metrics.
* **Set Echo / Set Response**: Configures terminal character readbacks.

## Usage: Standalone Python Driver

If you want to write your own custom scripts outside of the ARES ecosystem, you can use the underlying `OpenCPC` driver directly.

```python
from pyares_opencpc import OpenCPC
import time

# Connect to the device
cpc = OpenCPC(port='COM3')

try:
    print("Waiting for warmup...")
    time.sleep(2)

    # Read basic diagnostics
    status = cpc.get_status()
    print(f"Status: {status}")

    # Read particle concentration
    conc = cpc.get_concentration()
    print(f"Current Concentration: {conc} p/cm^3")

    # Change settings
    cpc.set_time_averaging(5.0)

finally:
    # Always safely close the serial connection
    cpc.close()
```

## Testing & Device Simulation

If you are developing for ARES OS but do not have access to the physical OpenCPC hardware, you can use the included hardware simulator (`tests/sim_opencpc.py`). The simulator mimics the serial behavior of the CPC using time-varying sine waves and random Gaussian noise.

### Setting up a Virtual Serial Port
To connect the simulator to the driver, you must create a linked "null-modem" virtual serial port pair.

* **Linux / macOS (using `socat`)**:
  ```bash
  socat -d -d pty,raw,echo=0 pty,raw,echo=0
  ```
  *This will output two linked ports (e.g., `/dev/pts/1` and `/dev/pts/2`).*

* **Windows**: 
  Use a free emulator tool like [com0com](https://com0com.sourceforge.net/) to create a linked pair (e.g., `COM3` linked to `COM4`).

### Running the Simulator
1. Start the simulator on the first port:
   ```bash
   python tests/sim_opencpc.py /dev/pts/1
   ```
2. Point your ARES service (`start_device_opencpc.py`) or test script (`tests/test_device.py`) to the *second* port:
   ```python
   serial_port = '/dev/pts/2'
   ```
3. Run your script. The driver will interface with the simulator seamlessly.
