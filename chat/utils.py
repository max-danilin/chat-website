HEADER = 64
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = '!disconnect'


def receive_protocol(conn):
    msg_length = conn.recv(HEADER).decode(FORMAT)
    # print('[Receiving length]:', msg_length, type(msg_length))
    if msg_length:
        msg_length = int(msg_length)
        msg = conn.recv(msg_length).decode(FORMAT)
        # print('[Receiving msg]:', msg, type(msg))       
        return msg

def send_protocol(msg, client):
    message = msg.encode(FORMAT)
    msg_length = len(msg)
    send_length = str(msg_length).encode(FORMAT)
    send_length = send_length + b' ' * (HEADER-len(send_length))
    # print('[Sending length]:', send_length, type(send_length))
    client.send(send_length)
    # print('[Sending msg]:', message, type(message))
    client.send(message)