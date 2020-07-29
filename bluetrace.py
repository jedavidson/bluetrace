# bluetrace.py: A module for the BlueTrace protocol
# by James Davidson for COMP3331, 20T2

from threading import Thread, Lock
from time import time
from datetime import datetime, timedelta
from random import choice
from string import digits
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, \
                   SO_REUSEADDR, SOCK_DGRAM

import bluetrace_protocol

''' Common helper functions '''


def generate_timestamp(dt, offset=0):
    '''
    Returns a timestamp in the format DD/MM/YY HH:MM:SS for the given datetime
    with a certain offset (in minutes).

    If no offset is given, the offset is taken to be 0.
    '''

    return (dt + timedelta(minutes=offset)).strftime('%d/%m/%y %H:%M:%S')


''' Server classes '''


class BlueTraceServerThread(Thread):
    ''' A thread running on a BlueTrace server. '''

    def __init__(self, server, client_socket):
        super().__init__()
        self.daemon = True
        self._server = server
        self._socket = client_socket
        self._username = None
        self._temp_id = None

    ''' Helper server thread methods '''

    def _verify_password(self, username, password):
        '''
        Verifies the client's entered password, prompting them to re-enter it
        as many times as is necessary.

        The number of attempts used by the client is returned, and they are cut
        off from making further attempts after incorrectly guessing three times.
        '''

        expected_password = self._server.get_password(username)
        attempts = 1
        while password != expected_password and attempts < 3:
            self._socket.send(bluetrace_protocol.INVALID_CREDENTIALS)
            password = self._socket.recv(1024).decode()
            attempts += 1

        return attempts

    ''' Main server thread methods and entry point '''

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
        if self._server.is_blocked(username):
            self._socket.send(bluetrace_protocol.ACCOUNT_IS_BLOCKED)
            return False

        # Verify the password, and block them if they take too many attempts.
        attempts = self._verify_password(username, password)
        if attempts == 3:
            self._server.block(username)
            self._socket.send(bluetrace_protocol.ACCOUNT_NOW_BLOCKED)
            return False

        # Otherwise, send a success message and end authentication.
        self._username = username
        self._socket.send(bluetrace_protocol.AUTHENTICATION_SUCCESS)
        return True

    def _receive_contact_log(self):
        ''' Receives a contact log from the user. '''

        # Inform the client that we're ready to receive the contact log.
        self._socket.send(bluetrace_protocol.READY_FOR_LOG_UPLOAD)

        print(f'Received contact log from {self._username}')

        # Read the log's lines into a list while there's lines left.
        contact_log = []
        response = self._socket.recv(bluetrace_protocol.LOG_ENTRY_SIZE)
        while response != bluetrace_protocol.FINISHED_CONTACT_LOG:
            line = response.decode()
            contact_log.append(line)
            temp_id, start_date, start_time, end_date, end_time = line.split()
            start = f'{start_date} {start_time}'
            end = f'{end_date} {end_time}'
            print(f'{temp_id}, {start}, {end};')
            response = self._socket.recv(bluetrace_protocol.LOG_ENTRY_SIZE)

        # Pass the log to the server to check.
        self._server.check_contact_log(contact_log)

    def _handle_request(self, request):
        ''' Handles a request issued by the client. '''

        if request == bluetrace_protocol.DOWNLOAD_TEMP_ID:
            temp_id = self._server.generate_temp_id(self._username)
            self._temp_id = temp_id
            self._socket.send(temp_id.encode())
        elif request == bluetrace_protocol.UPLOAD_CONTACT_LOG:
            self._receive_contact_log()

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

        print(f'User {self._username} has logged out.')


class BlueTraceServer():
    ''' A server in the BlueTrace protocol. '''

    def __init__(self, port, block_duration):
        self._port = port
        self._block_duration = block_duration
        self._server_socket = None
        self._blocked_users = {}
        self._resource_locks = {
            'blocked_users': Lock(),
            'credentials': Lock(),
            'temp_ids': Lock()
        }

    ''' Helper server methods '''

    def get_password(self, client_username):
        ''' Retrieves a user's password from the credentials file. '''

        client_password = None

        with self._resource_locks['credentials']:
            with open('credentials.txt', 'r') as credentials:
                line = credentials.readline().strip()
                while line and client_password is None:
                    username, password = line.split()
                    if username == client_username:
                        client_password = password
                    else:
                        line = credentials.readline().strip()

        return client_password

    def _get_username_from_temp_id(self, client_temp_id):
        ''' Gets the usernamne associated with the given temp ID. '''

        client_username = None

        with self._resource_locks['temp_ids']:
            with open('tempIDs.txt', 'r') as temp_ids:
                line = temp_ids.readline()
                while line and client_username is None:
                    username, temp_id, *_ = line.split()
                    if temp_id == client_temp_id:
                        client_username = username
                    else:
                        line = temp_ids.readline()

        return client_username

    ''' Main server methods and entry point '''

    def is_blocked(self, username):
        ''' Determines if a user is blocked or not. '''

        blocked = True

        with self._resource_locks['blocked_users']:
            block_time = self._blocked_users.get(username, None)
            if block_time is None or block_time <= int(time()):
                self._blocked_users.pop(username, None)
                blocked = False

        return blocked

    def block(self, username):
        ''' Blocks a user for block_duration seconds. '''

        with self._resource_locks['blocked_users']:
            self._blocked_users[username] = int(time()) \
                                          + self._block_duration

    def generate_temp_id(self, username):
        '''
        Returns a new temp ID for a user, valid for 15 minutes.

        An appropriate entry in the temp IDs file is written, and if this file
        does not already exist beforehand, it will be created.
        '''

        temp_id = ''.join(choice(digits) \
                          for _ in range(bluetrace_protocol.TEMP_ID_SIZE))

        with self._resource_locks['temp_ids']:
            with open('tempIDs.txt', 'a+') as temp_ids:
                start = generate_timestamp(datetime.now())
                end = generate_timestamp(datetime.now(),
                                         offset=bluetrace_protocol.TEMP_ID_TTL)
                temp_ids.write(f'{username} {temp_id} {start} {end}\n')

        print(f'Temp ID {temp_id} generated for {username}.')
        return temp_id

    def check_contact_log(self, contact_log):
        '''
        Checks the contents of a received contact log, mapping the temp IDs
        of the encounters back to their true usernames.

        The processed contents are displayed on the server's end.
        '''

        print(f'Checking contact log')

        for line in contact_log:
            temp_id, start_date, start_time, *_ = line.split()
            username = self._get_username_from_temp_id(temp_id)
            encounter_time = ' '.join((start_date, start_time))
            print(f'{username}, {encounter_time}, {temp_id};')

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


''' Client classes '''


class BlueTraceClientCentralThread(Thread):
    ''' A central client thread for peer-to-peer beaconing. '''

    def __init__(self, client, port):
        super().__init__()
        self.daemon = True
        self._client = client
        self._port = port
        self._socket = None

    ''' Main central thread methods and entry point '''

    def run(self):
        '''
        Runs this thread to handle receiving beacons from other peers.

        This method overrides the threading.Thread superclass method.
        '''

        with socket(AF_INET, SOCK_DGRAM) as central_socket:
            self._socket = central_socket
            # TODO: Implement central socket functionality


class BlueTraceClientPeripheralThread(Thread):
    ''' A peripheral client thread for peer-to-peer beaconing. '''

    def __init__(self, client, client_port, dest_ip, dest_port):
        super().__init__()
        self.daemon = True
        self._client = client
        self._port = client_port
        self._dest_ip = dest_ip
        self._dest_port = int(dest_port)
        self._socket = None

    ''' Main peripheral thread methods and entry point '''

    def run(self):
        '''
        Runs this thread to handle sending beacons to peers.

        This method overrides the threading.Thread superclass method.
        '''

        with socket(AF_INET, SOCK_DGRAM) as peripheral_socket:
            self._socket = peripheral_socket
            # TODO: Implement peripheral thread functionality


class BlueTraceClient():
    ''' A client in the BlueTrace protocol. '''

    def __init__(self, server_ip, server_port, client_port):
        self._server_ip = server_ip
        self._server_port = server_port
        self._client_port = client_port
        self._client_socket = None
        self._central_socket = None
        self._peripheral_socket = None
        self._username = None
        self._temp_id = None
        self._contact_log_lock = Lock()

    ''' Getter methods '''

    def get_temp_id(self):
        ''' Returns this client's temp ID object. '''

        return self._temp_id

    def get_contact_log_lock(self):
        ''' Get the client's contact log mutex. '''

        return self._contact_log_lock

    ''' Helper client methods '''

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
            response = self._client_socket.recv(1024)

        return response

    ''' Main client methods and entry point '''

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

    def _download_temp_id(self):
        ''' Downloads a temp ID from the server for this client. '''

        self._client_socket.send(bluetrace_protocol.DOWNLOAD_TEMP_ID)
        temp_id = self._client_socket \
                            .recv(bluetrace_protocol.TEMP_ID_SIZE) \
                            .decode()
        self._temp_id = {
            'temp_id': temp_id,
            'generated': int(time())
        }

        print(f'Your temp ID is {temp_id}.')

    def _upload_contact_log(self):
        ''' Uploads the client's contact log to the server. '''

        # Inform the server we're about to start sending the contact log,
        # then wait until they're ready to start receiving.
        self._client_socket.send(bluetrace_protocol.UPLOAD_CONTACT_LOG)

        response = self._client_socket.recv(1024)
        while response != bluetrace_protocol.READY_FOR_LOG_UPLOAD:
            response = self._client_socket.recv(1024)

        # Send the contact log line-by-line.
        with self._contact_log_lock:
            with open(f'{self._username}-contactlog.txt', 'r') as contact_log:
                for line in contact_log:
                    line = line.strip()
                    temp_id, start_date, start_time, end_date, end_time = line.split()
                    start = f'{start_date} {start_time}'
                    end = f'{end_date} {end_time}'
                    print(f'{temp_id}, {start}, {end};')
                    self._client_socket.send(line.encode())

            # Inform the server that the client has finished sending the log.
            self._client_socket.send(bluetrace_protocol.FINISHED_CONTACT_LOG)

    def _send_beacon(self, dest_ip, dest_port):
        ''' Sends a beacon to another client at the specified IP and port. '''

        # Open up a peripheral socket thread to send this beacon.
        self._peripheral_socket = \
            BlueTraceClientPeripheralThread(self, self._client_port,
                                            dest_ip, dest_port)
        self._peripheral_socket.start()

    def _process_command(self, command):
        ''' Processes a command issued from the user and return the result. '''

        if command == 'download_tempid':
            self._download_temp_id()
        elif command == 'upload_contact_log':
            self._upload_contact_log()
        elif command.startswith('beacon'):
            _, dest_ip, dest_port = command.split()
            self._send_beacon(dest_ip, dest_port)
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

            if self._authenticate():
                # Now that the client is authenticated, receive commands and
                # start up a central beaconing thread for receiving beacons.
                self._central_socket \
                    = BlueTraceClientCentralThread(self, self._client_port)
                self._central_socket.start()
                command = input('> ').lower()
                while command != 'logout':
                    self._process_command(command)
                    command = input('> ').lower()

                # Initiate the logout phase.
                self._logout()
