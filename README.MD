To connect your driver to this simulator, you need a virtual serial port pair (a "null-modem" emulator) so that the simulator can plug into one end, and your driver can plug into the other.

Linux/macOS: You can easily create a pair using socat in your terminal:

Bash
socat -d -d pty,raw,echo=0 pty,raw,echo=0
(This will print two linked ports, e.g., /dev/pts/1 and /dev/pts/2. Run the simulator on pts/1 and the driver on pts/2)

Windows: You can use a free tool like com0com to create a linked pair (e.g., COM3 linked to COM4).

The OpenCPC Simulator (opencpc_simulator.py)