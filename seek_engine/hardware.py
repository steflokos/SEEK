import serial
import serial.tools.list_ports
import threading
import time

class SerialManager:
    def __init__(self, log_callback):
        self.port = None
        self.is_connected = False
        self.log_callback = log_callback

    def get_ports(self):
        return [p.device for p in serial.tools.list_ports.comports()]

    def connect(self, port_name, baud_rate):
        self.port = serial.Serial(port_name, int(baud_rate), timeout=0.1)
        self.is_connected = True
        threading.Thread(target=self._read_loop, daemon=True).start()

    def disconnect(self):
        self.is_connected = False
        if self.port:
            self.port.close()

    def write(self, data):
        if self.is_connected and self.port and self.port.is_open:
            self.port.write(data)

    def _read_loop(self):
        while self.is_connected and self.port and self.port.is_open:
            try:
                if self.port.in_waiting:
                    text = self.port.read(self.port.in_waiting).decode('ascii', errors='replace')
                    self.log_callback(" [SEM] " + text.replace('\n', ''))
            except Exception:
                break
            time.sleep(0.05)