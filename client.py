# client.py: Client program for the BlueTrace protocol simulator
# Usage: python3 client.py [server IP] [server port] [client UDP port]
# by James Davidson for COMP3331, 20T2
# Note: This client was tested on CSE with Python 3.7.3.

import sys

from bluetrace import BlueTraceClient

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print('Usage: python3 client.py [server IP] [server port] [client UDP port]')
        sys.exit(1)

    try:
        server_ip = str(sys.argv[1])
        server_port = int(sys.argv[2])
        client_port = int(sys.argv[3])
    except ValueError:
        print('Invalid server or client port')
        sys.exit(1)

    client = BlueTraceClient(server_ip, server_port, client_port)
    client.start()
