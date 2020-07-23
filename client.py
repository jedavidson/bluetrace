# client.py: Client program for the BlueTrace protocol simulator.
# Usage: python3 client.py [server IP] [server port] [client UDP port]
# by James Davidson for COMP3331, 20T2
# Note: This client was tested on CSE with Python 3.7.3.

import sys
import time
from socket import *

import bluetrace_protocol

''' Helper functionality '''


''' Main functionality '''


def authenticate(client):
    '''
    Handles the client's end of the authentication process.
    The result of the authentication process is returned.
    '''

    # Acknowledge that the client is ready to begin authentication.
    client.send(bluetrace_protocol.READY_TO_AUTH)

    # The server will first ask for the username, so prompt the user to
    # enter their username and then send it.
    response = client.recv(1024)
    while response != bluetrace_protocol.EXPECTING_USERNAME:
        response = client.recv(1024)

    username = input('> Username: ')
    client.send(username.encode())

    # The server will next ask for a password, so prompt the user again.
    response = client.recv(1024)
    while response != bluetrace_protocol.EXPECTING_PASSWORD:
        response = client.recv(1024)

    # Keep prompting the user to enter their password as required.
    password = input('> Password: ')
    client.send(password.encode())
    response = client.recv(1024)
    while response == bluetrace_protocol.INVALID_CREDENTIALS:
        print(response.decode())
        password = input('> Password: ')
        client.send(password.encode())
        response = client.recv(1024)

    # Print whatever the server sends back in response, and return the overall
    # result of the authentication.
    print(response.decode())
    return response == bluetrace_protocol.AUTHENTICATION_SUCCESS


def logout(client):
    ''' Logs out this connected client. '''

    client.send(bluetrace_protocol.LOGOUT_CLIENT)


def download_temp_id(client):
    ''' Downloads a temp ID from the server for this client. '''

    client.send(bluetrace_protocol.DOWNLOAD_TEMP_ID)
    temp_id = client.recv(1024).decode()

    print(f'Your temp ID is {temp_id}.')


def process_command(client, command):
    ''' Processes a command issued from the user and return the result. '''

    if command == 'download_tempid':
        download_temp_id(client)
    elif command == 'upload_contact_log':
        # TODO: Implement uploading of contact logs.
        pass
    elif command.startswith('beacon'):
        # TODO: Implement P2P beaconing.
        pass
    else:
        # If the command is unknown, give a generic response.
        print('Invalid command.')


def client(server_ip, server_port, client_port):
    ''' Starts this BlueTrace client. '''

    with socket(AF_INET, SOCK_STREAM) as client:
        client.connect((server_ip, server_port))

        # BlueTrace servers will initiate authentication upon connection,
        # so the client should reciprocate.
        response = client.recv(1024)
        while response != bluetrace_protocol.INITIATING_AUTH:
            response = client.recv(1024)

        if not authenticate(client):
            sys.exit(1)

        # Now that the client is authenticated, allow them to enter commands.
        command = input('> ').lower()
        while command != 'logout':
            process_command(client,command)
            command = input('> ').lower()

        # Initiate the logout phase.
        logout(client)


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

    client(server_ip, server_port, client_port)
