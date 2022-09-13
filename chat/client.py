import socket
from threading import Thread
from time import sleep
from .utils import receive_protocol, send_protocol
from queue import Queue

HEADER = 64
PORT = 5050
# Localhost server
SERVER = socket.gethostbyname(socket.gethostname())
# Local network server
# SERVER = '192.168.0.108'
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = '!disconnect'


class SocketException(Exception):
    pass


class Client:
    def __init__(self, name) -> None:
        self.name = name
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.q = Queue()
        self.messages = []
        self.chatroom = None
        self.exc = False

    def __str__(self) -> str:
        connected = 'disconnected' if not self.client else 'connected'
        return f'Client {self.name} from chatroom {self.chatroom}. Currently {connected}.'

    def send(self, msg):
        try:
            send_protocol(msg, self.client)
        except OSError as exc:
            print('Exception from send: ', exc)
            raise SocketException('Unable to reconnect to server.')
        if msg == DISCONNECT_MESSAGE:
            sleep(2)
            self.client.close()

    def receive(self, client):
        while True:
            try:
                msg = receive_protocol(client)
                if msg:
                    print('[SERVER]:', msg)
                    self.q.put(self.parse_name(msg))
                else:
                    break
            except OSError as osexc:
                print("Exception from receive", osexc)
                self.exc = True
                break

    def start_client(self):
        try:
            self.client.connect(ADDR)
        except OSError as exc:
            if exc.args[0] == 10061:
                print('Server not ready, ', exc)
                raise SocketException('Server is offline.')
            else:
                print('Exception from connecting: ', exc)
        self.send(self.name)
        self.send(str(self.chatroom))
        receiver = Thread(target=self.receive, args=(self.client,))
        receiver.start()
        # while True and client.fileno() != -1:

    def parse_name(self, msg):
        sep_sender = msg.find('::name::')
        if sep_sender == -1:
            sender = 'SERVER'
            chat = None
            conn_msg = msg.find('CONN::')
            if conn_msg != -1:
                active_members = msg[conn_msg+len('CONN::'):]
                return (sender, 'conn', active_members)
        else:
            sender = msg[:sep_sender]
            msg = msg[sep_sender+len('::name::'):]
            sep_chat = msg.find('::chat::')
            chat = msg[:sep_chat]
            msg = msg[sep_chat+len('::chat::'):]
        return (sender, chat, msg)

    @property
    def get_messages(self):
        print('getting msg')
        if self.exc:
            raise SocketException('Server has disconnected.')
        self.messages = []
        while not self.q.empty():
            item = self.q.get()
            print(item)
            self.messages.append(item)
        return self.messages

