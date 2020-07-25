# bluetrace.py: A module containing the entities in the BlueTrace protocol
# by James Davidson for COMP3331, 20T2

import sys
import threading
import time

from datetime import datetime, timedelta
from random import choice
from socket import *
from string import digits

import bluetrace_protocol


class BlueTraceServerThread(threading.Thread):
    ''' A thread running under a BlueTrace server. '''

    def __init__(self, server, client_socket):
        super().__init__()
        self.daemon = True
        self._server = server
        self._socket = client_socket
        self._username = None
        self._temp_id = None

    ''' Main methods and server thread entry point '''

    def _verify_password(self, username, password):
        '''
        Verifies the client's entered password, prompting them to re-enter it
        as many times as is necessary.
        
        The number of attempts used by the client is returned, and they are cut
        off from making further attempts after incorrectly guessing three times. 
        '''

        expected_password = self._server._get_password(username)
        attempts = 1
        while password != expected_password and attempts < 3:
            self._socket.send(bluetrace_protocol.INVALID_CREDENTIALS)
            password = self._socket.recv(1024).decode()
            attempts += 1

        return attempts

    def _authenticate(self):
        '''
        Authenticates an incoming connection.

        The result of the authentication process is returned.
        '''

        # Initiate authentication with the connecting client.
        self._socket.send(bluetrace_protocol.INITIATING_AUTH)
        response = self._socket.recv(1024)
        while response != bluetrace_protocol.READY_TO_AUTH:
            self._socket.send(bluetrace_protocol.INITIATING_AUTH)
            response = self._socket.recv(1024)

        # After the client has acknowledged, ask for a username and password.
        self._socket.send(bluetrace_protocol.EXPECTING_USERNAME)
        username = self._socket.recv(1024).decode()
        self._socket.send(bluetrace_protocol.EXPECTING_PASSWORD)
        password = self._socket.recv(1024).decode()

        # If the client is blocked, tell them and end authentication.
        if self._server._is_blocked(username):
            self._socket.send(bluetrace_protocol.ACCOUNT_IS_BLOCKED)
            return False

        # Verify the password, and block them if they take too many attempts.
        attempts = self._verify_password(username, password)
        if attempts == 3:
            self._server._block(username)
            self._socket.send(bluetrace_protocol.ACCOUNT_NOW_BLOCKED)
            return False

        # Otherwise, send a success message and end authentication.
        self._username = username
        self._socket.send(bluetrace_protocol.AUTHENTICATION_SUCCESS)
        return True

    def _handle_request(self, request):
        ''' Handles a request issued by the client. '''

        if request == bluetrace_protocol.DOWNLOAD_TEMP_ID:
            temp_id = self._server._generate_temp_id(self._username)
            self._temp_id = temp_id
            self._socket.send(temp_id.encode())
        elif request == bluetrace_protocol.UPLOAD_CONTACT_LOG:
            # TODO: Handle uploading contact logs.
            pass

    def run(self):
        '''
        Runs this thread to handle an incoming connection.

        This method overrides the threading.Thread superclass method.
        '''

        # Authenticate the incoming connection first.
        if not self._authenticate():
            return

        # Receive requests from the client until they try to log out.
        request = self._socket.recv(1024)
        while request != bluetrace_protocol.LOGOUT_CLIENT:
            self._handle_request(request)
            request = self._socket.recv(1024)


class BlueTraceServer():
    ''' A server in the BlueTrace protocol. '''

    def __init__(self, port, block_duration):
        self._port = port
        self._block_duration = block_duration
        self._server_socket = None
        self._blocked_users = {}
        self._resource_locks = {
            'blocked_users': threading.Lock(),
            'credentials': threading.Lock(),
            'temp_ids': threading.Lock()
        }

    ''' Getter and setter methods '''

    # TODO.

    ''' Helper methods '''

    def _generate_timestamp(self, dt, offset=0):
        '''
        Returns a timestamp in the format DD/MM/YY HH:MM:SS for the given datetime
        with a certain offset (in minutes).

        If no offset is given, the offset is taken to be 0.
        '''

        return (dt + timedelta(minutes=offset)).strftime('%d/%m/%y %H:%M:%S')

    ''' Main server methods and entry point '''

    def _is_blocked(self, username):
        ''' Determines if a user is blocked or not. '''

        blocked = True

        with self._resource_locks['blocked_users']:
            block_time = self._blocked_users.get(username, None)
            if block_time is None or block_time <= int(time.time()):
                self._blocked_users.pop(username, None)
                blocked = False

        return blocked

    def _block(self, username):
        ''' Blocks a user for block_duration seconds. '''

        with self._resource_locks['blocked_users']:
            self._blocked_users[username] = int(time.time()) \
                                          + self._block_duration

    def _get_password(self, client_username):
        ''' Retrieves a user's password from the credentials file. '''

        client_password = None

        with self._resource_locks['credentials']:
            with open('credentials.txt', 'r') as credentials:
                line = credentials.readline().strip('\n')
                while line and client_password is None:
                    username, password = line.split()
                    if username == client_username:
                        client_password = password
                    else:
                        line = credentials.readline().strip('\n')

        return client_password

    def _generate_temp_id(self, username):
        '''
        Returns a new temp ID for a user, valid for 15 minutes.
        
        An appropriate entry in the temp IDs file is written, and if this file
        does not already exist beforehand, it will be created.
        '''

        temp_id = ''.join(choice(digits) for _ in range(20))

        with self._resource_locks['temp_ids']:
            with open('tempIDs.txt', 'a+') as temp_ids:
                start = self._generate_timestamp(datetime.now())
                end = self._generate_timestamp(datetime.now(), offset=15)
                temp_ids.write(f'{username} {temp_id} {start} {end}\n')

        print(f'Temp ID {temp_id} generated for {username}.')
        return temp_id

    def start(self):
        ''' Starts this BlueTrace server. '''

        # Start a new welcoming socket for incoming connections.
        with socket(AF_INET, SOCK_STREAM) as server_socket:
            self._server_socket = server_socket
            server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            server_socket.bind(('localhost', self._port))
            server_socket.listen(1)

            while True:
                client_socket, _ = server_socket.accept()
                client_thread = BlueTraceServerThread(self, client_socket)
                client_thread.start()


class BlueTraceClient():
    ''' A client in the BlueTrace protocol. '''

    def __init__(self, server_ip, server_port, client_port):
        self._server_ip = server_ip
        self._server_port = server_port
        self._client_port = client_port
        self._client_socket = None
        self._username = None
        self._temp_id = None

    ''' Helper client methods '''

    def _verify_password(self, username):
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
            response = self._client_socket.recv(1024)

        return response

    ''' Main client methods and entry point '''

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
        response = self._verify_password(username)
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
