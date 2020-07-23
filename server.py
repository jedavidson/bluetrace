# server.py: Server program for the BlueTrace protocol simulator.
# Usage: python3 server.py [server port] [block duration]
# by James Davidson for COMP3331, 20T2
# Note: This server was tested on CSE with Python 3.7.3.

import sys
import threading
import time
from datetime import datetime, timedelta
from random import choice
from socket import *
from string import digits

import bluetrace_protocol

''' Global state variables '''

# The duration clients should be blocked for when failing to authenticate.
block_duration = 0

# A mapping from blocked client names to their unblock times.
blocked_users = {}

# Various thread locks to regulate concurrent resource access.
blocked_users_lock = threading.Lock()
credentials_lock = threading.Lock()
temp_ids_lock = threading.Lock()

''' Helper functionality '''


def initiate_authentication(client):
    ''' Waits for the client to respond to the authentication request. '''

    client.send(bluetrace_protocol.INITIATING_AUTH)
    response = client.recv(1024)
    while response != bluetrace_protocol.READY_TO_AUTH:
        client.send(bluetrace_protocol.INITIATING_AUTH)
        response = client.recv(1024)


def is_blocked(username):
    ''' Determines if a user is blocked or not. '''

    blocked = True

    with blocked_users_lock:
        block_time = blocked_users.get(username, None)
        if block_time is None or block_time <= int(time.time()):
            blocked_users.pop(username, None)
            blocked = False

    return blocked


def get_password(client_username):
    ''' Retrieves a client's password from the credentials file. '''

    client_password = None

    with credentials_lock:
        with open('credentials.txt', 'r') as credentials:
            line = credentials.readline().strip('\n')
            while line and client_password is None:
                username, password = line.split()
                if username == client_username:
                    client_password = password
                else:
                    line = credentials.readline().strip('\n')

    return client_password


def verify_password(client, username, password):
    '''
    Verifies the client's entered password, prompting them to re-enter it
    as many times as is necessary.
    
    The number of attempts used by the client is returned, and they are cut
    off from making further attempts after incorrectly guessing three times. 
    '''

    expected_password = get_password(username)
    attempts = 1
    while password != expected_password and attempts < 3:
        client.send(bluetrace_protocol.INVALID_CREDENTIALS)
        password = client.recv(1024).decode()
        attempts += 1

    return attempts


def block(client, username):
    ''' Blocks a user for block_duration seconds. '''

    with blocked_users_lock:
        blocked_users[username] = int(time.time()) + block_duration

    client.send(bluetrace_protocol.ACCOUNT_NOW_BLOCKED)


def generate_timestamp(dt, offset=0):
    '''
    Returns a timestamp in the format DD/MM/YY HH:MM:SS for the given datetime
    with a certain offset (in minutes).

    If no offset is given, the offset is taken to be 0.
    '''

    return (dt + timedelta(minutes=offset)).strftime('%d/%m/%y %H:%M:%S')


''' Main functionality '''


def authenticate(client):
    '''
    Authenticates an incoming connection.

    The result of the authentication process is returned along with the
    client's username.
    
    If authentication fails, the username returned is None.
    '''

    # Initiate authentication with the connecting client.
    initiate_authentication(client)

    # After the client has acknowledged the above, ask for their
    # username and password.
    client.send(bluetrace_protocol.EXPECTING_USERNAME)
    username = client.recv(1024).decode()
    client.send(bluetrace_protocol.EXPECTING_PASSWORD)
    password = client.recv(1024).decode()

    # If the client is blocked, tell them and end authentication.
    if is_blocked(username):
        client.send(bluetrace_protocol.ACCOUNT_IS_BLOCKED)
        return False, None

    # Verify the given password, and block them if they take too many attempts.
    attempts = verify_password(client, username, password)
    if attempts == 3:
        block(client, username)
        return False, None

    # Otherwise, send a success message and end authentication.
    client.send(bluetrace_protocol.AUTHENTICATION_SUCCESS)
    return True, username


def generate_temp_id(username):
    '''
    Returns a new temp ID for a user, valid for 15 minutes.
    
    An appropriate entry in the temp IDs file is written, and if this file
    does not already exist beforehand, it will be created.
    '''

    temp_id = ''.join(choice(digits) for _ in range(20))

    with temp_ids_lock:
        with open('tempIDs.txt', 'a+') as temp_ids:
            start = generate_timestamp(datetime.now())
            end = generate_timestamp(datetime.now(), offset=15)
            temp_ids.write(f'{username} {temp_id} {start} {end}')

    print(f'Temp ID {temp_id} generated for {username}.')
    return temp_id


def handle_request(client, username, request):
    ''' Handles a request issued by the client. '''

    if request == bluetrace_protocol.DOWNLOAD_TEMP_ID:
        temp_id = generate_temp_id(username)
        client.send(temp_id.encode())
    elif request == bluetrace_protocol.UPLOAD_CONTACT_LOG:
        # TODO: Handle uploading contact logs.
        pass


def handle_connection(client):
    ''' Handles an incoming connection. '''

    # Authenticate the incoming connection first.
    authenticated, username = authenticate(client)
    if not authenticated:
        return

    # Receive requests from the client until they initiate the logout phase.
    request = client.recv(1024)
    while request != bluetrace_protocol.LOGOUT_CLIENT:
        handle_request(client, username, request)
        request = client.recv(1024)


def server(port):
    ''' Starts this BlueTrace server. '''

    # Start a new welcoming socket for incoming connections.
    with socket(AF_INET, SOCK_STREAM) as server:
        server.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        server.bind(('localhost', port))
        server.listen(1)

        while True:
            client, _ = server.accept()

            # Delegate new connections to a new thread. Each thread is run in
            # a try/catch block so that thread exceptions are suppressed.
            client_thread = threading.Thread(target=handle_connection,
                                             args=(client,),
                                             daemon=True)

            try:
                client_thread.start()
            except:
                pass


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

    server(port)
