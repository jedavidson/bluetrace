# server.py: Server program for the BlueTrace protocol simulator
# Usage: python3 server.py [server port] [block duration]

import sys
from bluetrace import BlueTraceServer

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python3 server.py [server port] [block duration]')
        sys.exit(1)

    try:
        port = int(sys.argv[1])
        block_duration = int(sys.argv[2])
    except ValueError:
        print('Invalid server port or block duration')
        sys.exit(1)

    server = BlueTraceServer(port, block_duration)
    server.start()
