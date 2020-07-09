# server.py: Server program for the BlueTrace protocol simulator
# Usage: python3 server.py [server port] [block duration]
# by James Davidson for COMP3331's Term 2, 2020 offering

# Version note: This server was tested on CSE with Python 3.7.3.


import sys
import socket
import threading


def check_contact_log(*args):
    ''' Checks a contact log. '''

    raise NotImplementedError


def generate_temp_id(*args):
    ''' Generates a temp ID for a user. '''

    raise NotImplementedError


def authenticate_user(*args):
    ''' Authenticates a user. '''

    raise NotImplementedError


def server():
    raise NotImplementedError


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python3 client.py [server IP] [server port] [client UDP port]')
        sys.exit(1)

    try:
        server_port = int(sys.argv[1])
        block_duration = int(sys.argv[2])
    except ValueError:
        print('Invalid server port or block duration')
        sys.exit(1)

    server(server_port, block_duration)
