import socket
import threading
from queue import Queue
from utils import receive_protocol, send_protocol

HEADER = 64
PORT = 5050
# Localhost server
SERVER = socket.gethostbyname(socket.gethostname())
# Local network server
# SERVER = '' 
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = '!disconnect'


class Chatroom:
    def __init__(self, token) -> None:
        self.members = []
        self.token = token

    def __eq__(self, other) -> bool:
        if self.token == other.token:
            return True
        return False
    
    def __str__(self) -> str:
        return f'Chatroom with token {self.token} and {len(self.members)} members.'


class Server:
    def __init__(self) -> None:
        self.bound = False
        self.messages = []
        self.clients = {}
        self.chatrooms: Chatroom = []
        self.clients_addr = {}
        self.q = Queue()

    def bind_server(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(ADDR)
        self.bound = True
        print(f'[STARTING] server on {SERVER}:{PORT} is starting...')
        print(self.server.getsockname())

    def handle_client(self, conn, addr, q):
        print(f'[NEW CONNECTION] {addr} connected.')
        send_protocol('Welcome to our friendly chat!', conn)
        connected = True

        name = receive_protocol(conn) 
        self.clients[addr] = name
        send_protocol(f'Hi {name}!', conn)

        chatroom = receive_protocol(conn)
        if self.get_chatroom_by_token(chatroom):
            chat = self.get_chatroom_by_token(chatroom)
        else:
            chat = Chatroom(chatroom)
            self.chatrooms.append(chat)
        chat.members.append(name)

        send_protocol(f'CONN::{len(chat.members)}', conn)
        print(f'[ACTIBE CONNECTIONS AFTER CONNECT]: {len(self.clients_addr)}')
        print(self.chatrooms)

        while connected:
            try:
                msg = receive_protocol(conn)
                print(f'[{name.upper()}]: {msg}')
                self.broadcast(msg, name, chat.token)
                q.put((name, msg))
                if msg == DISCONNECT_MESSAGE:
                    print('Disconnect message sent')
                    send_protocol(f'Bye {name}!', conn)
                    connected = False 
                elif msg == 'bb':
                    send_protocol(f'Yo {name}!', conn)
            except ConnectionResetError as ex:
                print(ex)
                break  

        conn.close()
        del self.clients[addr]
        del self.clients_addr[addr]
        self.delete_member_from_chatroom(name, chat)
        self.delete_chatroom_if_empty(chat)


        send_protocol(f'CONN::{len(chat.members)}', conn)
        print(f'[ACTIBE CONNECTIONS AFTER DELETE]: {len(self.clients_addr)}')
        print('DELETEd ', self.chatrooms)

    def start(self):
        if not self.bound:
            self.bind_server()
            self.bound = True
        self.server.listen()
        while True:
            conn, addr = self.server.accept()
            thread = threading.Thread(target=self.handle_client, args=(conn, addr, self.q))
            thread.start()
            self.clients_addr[addr] = conn
            print(f'[ACTIBE CONNECTIONS]: {len(self.clients_addr)}')

    def broadcast(self, msg, name='', chatroom=''):
        clients = self.get_client_sock_from_chat(chatroom)
        print('FRM BRD ', clients, chatroom)
        for sock in clients:
            print('BROADCASTING')
            send_protocol(name+'::name::'+chatroom+'::chat::'+msg, sock)

    @property
    def get_messages(self):
        print('getting msg')
        while not self.q.empty():
            item = self.q.get()
            self.messages.append(item)
        return self.messages

    def get_chatroom_by_token(self, token):
        match = [chat for chat in self.chatrooms if chat.token == token]
        print('CHAT BY TOKEN ', token, match)
        return match[0] if match else None

    def get_client_sock_from_name(self, name):
        address = [addr for addr in list(self.clients.keys()) if self.clients[addr] == name][0]
        print('NAME ADDR ', name, address)
        return self.clients_addr[address]

    def get_client_sock_from_chat(self, chatroom):
        chat = self.get_chatroom_by_token(chatroom)
        print('GET SOCK ',chat)
        if not chat:
            return None
        conns = []
        for member in chat.members:
            conns.append(self.get_client_sock_from_name(member))
        print('CONNS', conns)
        return conns

    @staticmethod
    def delete_member_from_chatroom(name, chat):
        member = [memb for memb in chat.members if memb == name][0]
        if member:
            chat.members.remove(member)

    def delete_chatroom_if_empty(self, chat):
        if chat.members == []:
            self.chatrooms.remove(chat)
            del chat


if __name__ == '__main__':
    chat_server = Server()
    chat_server.start()
