import sys
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtCore import QObject, Signal, QIODevice

class SingleInstance(QObject):
    """
    Manages single instance behavior.
    - server_name: Unique identifier for the local socket.
    """
    message_received = Signal(str)

    def __init__(self, server_name="linsnipper_ipc"):
        super().__init__()
        self.server_name = server_name
        self.server = QLocalServer(self)
        self.server.newConnection.connect(self._handle_new_connection)

    def start(self):
        """
        Starts listening. If a server already exists (crashed?), try to remove it.
        Returns True if successful.
        """
        # Clean up potentially stale socket file
        QLocalServer.removeServer(self.server_name)
        
        if not self.server.listen(self.server_name):
            return False
        return True

    def _handle_new_connection(self):
        socket = self.server.nextPendingConnection()
        socket.readyRead.connect(lambda: self._read_socket(socket))
        socket.disconnected.connect(socket.deleteLater)

    def _read_socket(self, socket):
        # Read available data
        data = socket.readAll().data().decode('utf-8')
        self.message_received.emit(data)

def send_message_to_instance(server_name, message):
    """
    Tries to connect to an existing instance and send a message.
    Returns True if successful (meaning an instance is running), False otherwise.
    """
    socket = QLocalSocket()
    socket.connectToServer(server_name)
    if socket.waitForConnected(1000):
        socket.write(message.encode('utf-8'))
        socket.flush()
        socket.waitForBytesWritten(1000)
        socket.disconnectFromServer()
        return True
    return False
