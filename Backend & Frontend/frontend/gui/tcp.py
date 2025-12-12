from PySide6.QtCore import QObject, Signal, QThread
import socket

class TcpClient(QThread):
    data_received = Signal(dict)
    status_received = Signal(dict)
    connection_status = Signal(bool)

    def __init__(self):
        super().__init__()
        self.sock = None
        self.is_connected = False
        self._running = False

    def connect(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self.is_connected = True
        self._running = True
        self.start()
        self.connection_status.emit(True)

    def disconnect(self):
        self._running = False
        if self.sock:
            self.sock.close()
            self.is_connected = False
            self.connection_status.emit(False)

    def run(self):
        buffer = ""
        while self._running and self.sock:
            try:
                data = self.sock.recv(1024)
                if data:
                    buffer += data.decode('utf-8')
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        self.handle_line(line.strip())
            except Exception:
                self.disconnect()
                break

    def handle_line(self, line):
        if line.startswith('DATA:'):
            import json
            try:
                data = json.loads(line[5:])
                self.data_received.emit(data)
            except Exception: pass
        elif line.startswith('STATUS:'):
            import json
            try:
                msg = json.loads(line[7:])
                self.status_received.emit(msg)
            except Exception: pass

    def send_command(self, command):
        if self.sock and self.is_connected:
            self.sock.sendall((command.strip() + '\n').encode('utf-8'))
