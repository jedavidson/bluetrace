# client.py: Client program for the BlueTrace protocol simulator
# Usage: python3 client.py [server IP] [server port] [client UDP port]
# by James Davidson for COMP3331's Term 2, 2020 offering

# Version note: This client was tested on CSE with Python 3.7.3.


import sys
import socket


def retrieve_temp_id():
    raise NotImplementedError


def authenticate():
    raise NotImplementedError


def client(server_ip, server_port, client_port):
    raise NotImplementedError


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print('Usage: python3 client.py [server IP] [server port] [client UDP port]')
        sys.exit(1)

    try:
        server_ip = sys.argv[1]
        server_port = int(sys.argv[2])
        client_port = int(sys.argv[3])
    except ValueError:
        print('Invalid server or client port')
        sys.exit(1)

    client(server_ip, server_port, client_port)
