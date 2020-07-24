# bluetrace.py: A module containing the entities in the BlueTrace protocol
# by James Davidson for COMP3331, 20T2

import sys
import time
from socket import *

import bluetrace_protocol


class BlueTraceServerConnection():
    # TODO: Convert server connection to class.
    pass

class BlueTraceServer():
    # TODO: Convert server to class.
    pass

class BlueTraceClient():
    ''' A client in the BlueTrace protocol. '''

    def __init__(self, server_ip, server_port, client_port):
        self._server_ip = server_ip
        self._server_port = server_port
        self._client_port = client_port
        self._client_socket = None
        self._username = None
        self._temp_id = None

    ''' Helper methods '''

    def _verify_password(self):
        '''
        Verifies a user's entered password with the server until the server
        provides a definitive response.
        
        The definitive response given is returned.
        '''

        password = input('> Password: ')
        self._client_socket.send(password.encode())
        response = self._client_socket.recv(1024)

        # Keep prompting the user to enter their password as required.
        while response == bluetrace_protocol.INVALID_CREDENTIALS:
            print(response.decode())
            password = input('> Password: ')
            self._client_socket.send(password.encode())
            response = client.recv(1024)

        return response

    ''' Main methods and client entry point '''

    def _download_temp_id(self):
        ''' Downloads a temp ID from the server for this client. '''

        self._client_socket.send(bluetrace_protocol.DOWNLOAD_TEMP_ID)
        self._temp_id = self._client_socket.recv(1024).decode()

        print(f'Your temp ID is {self._temp_id}.')

    def _authenticate(self):
        '''
        Handles the client's end of the authentication process.
        The result of the authentication process is returned.
        '''

        # Acknowledge that the client is ready to begin authentication.
        self._client_socket.send(bluetrace_protocol.READY_TO_AUTH)

        # The server will first ask for the username, so prompt the user to
        # enter their username and then send it.
        response = self._client_socket.recv(1024)
        while response != bluetrace_protocol.EXPECTING_USERNAME:
            response = self._client_socket.recv(1024)

        username = input('> Username: ')
        self._client_socket.send(username.encode())

        # The server will next ask for a password, so prompt the user again.
        response = self._client_socket.recv(1024)
        while response != bluetrace_protocol.EXPECTING_PASSWORD:
            response = self._client_socket.recv(1024)

        # Relay whatever the server sent back to the user after verification,
        # and update any internal client state upon success.
        response = self._verify_password()
        print(response.decode())
        if response == bluetrace_protocol.AUTHENTICATION_SUCCESS:
            self._username = username

        return response == bluetrace_protocol.AUTHENTICATION_SUCCESS

    def _logout(self):
        ''' Logs out this client. '''

        self._client_socket.send(bluetrace_protocol.LOGOUT_CLIENT)
        self._username = None
        self._temp_id = None

    def _process_command(self, command):
        ''' Processes a command issued from the user and return the result. '''

        if command == 'download_tempid':
            self._download_temp_id()
        elif command == 'upload_contact_log':
            # TODO: Implement uploading of contact logs.
            pass
        elif command.startswith('beacon'):
            # TODO: Implement P2P beaconing.
            pass
        else:
            # If the command is unknown, give a generic response.
            print('Invalid command.')

    def run(self):
        ''' Runs this BlueTrace client. '''

        with socket(AF_INET, SOCK_STREAM) as client_socket:
            self._client_socket = client_socket
            client_socket.connect((self._server_ip, self._server_port))

            # BlueTrace servers will initiate authentication upon connection,
            # so the client should reciprocate.
            response = client_socket.recv(1024)
            while response != bluetrace_protocol.INITIATING_AUTH:
                response = client_socket.recv(1024)

            if not self._authenticate():
                sys.exit(1)

            # Now that the client is authenticated, allow them to enter commands.
            command = input('> ').lower()
            while command != 'logout':
                self._process_command(command)
                command = input('> ').lower()

            # Initiate the logout phase.
            self._logout()

        self._client_socket = None
