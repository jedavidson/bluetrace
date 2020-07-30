# bluetrace_protocol.py: A specification of constants used in BlueTrace communications
# by James Davidson for COMP3331, 20T2

''' General '''

# The format string of all timestamps used in BlueTrace record.
TIMESTAMP_FORMAT = '%d/%m/%Y %H:%M:%S'

''' Authentication '''

# Protocol messages sent by the server when authenticating the client.
INITIATING_AUTH = 'BT_AUTH_INIT'.encode()
READY_TO_AUTH = 'BT_AUTH_READY'.encode()
EXPECTING_USERNAME = 'BT_AUTH_UN'.encode()
EXPECTING_PASSWORD = 'BT_AUTH_PW'.encode()

# Informative messages to relay to the client during authentication.
AUTHENTICATION_SUCCESS = 'Welcome to the BlueTrace simulator!'.encode()
INVALID_CREDENTIALS = 'Invalid password. Please try again.'.encode()
ACCOUNT_NOW_BLOCKED = 'Invalid password. Your account has been blocked. ' \
                      'Please try again later.'.encode()
ACCOUNT_IS_BLOCKED = 'Your account is blocked due to multiple login failures. ' \
                     'Please try again later.'.encode()

# The protocol message sent by the client when logging out.
LOGOUT_CLIENT = 'BT_AUTH_LOGOUT'.encode()

''' Temp IDs '''

# The size of the temp ID, in bytes.
TEMP_ID_SIZE = 20

# The time-to-live (TTL) of a temp ID in minutes.
TEMP_ID_TTL = 15

# The protocol message sent when a client is downloading a temp ID.
DOWNLOAD_TEMP_ID = 'BT_DOWN_TEMP_ID'.encode()

''' Uploading contact logs '''

# The size of each contact log entry, in bytes.
# [temp ID, 20] + [space, 1] + [start, 19] + [space, 1] + [expiry, 19]
LOG_ENTRY_SIZE = 20 + 1 + 19 + 1 + 19

# The protocol message sent when a client sends a contact log.
UPLOAD_CONTACT_LOG = 'BT_UPLOAD_CONTACT_LOG'.encode()
FINISHED_CONTACT_LOG = 'BT_FINISHED_CONTACT_LOG_UPLOAD'.encode()

# The protocol message sent by the server after it is prepared to receive logs.
READY_FOR_LOG_UPLOAD = 'BT_READY_FOR_CONTACT_LOG_UPLOAD'.encode()

''' Peer-to-peer beaconing '''

# The BlueTrace protocol version number.
PROTOCOL_VERSION = 1

# The length of each beacon packet in bytes.
# [temp ID, 20] + [space, 1] + [start, 19] + [space, 1] + [expiry, 19]
#                                          + [space, 1] + [protocol version, 1]
BEACON_SIZE = 20 + 1 + 19 + 1 + 19 + 1 + 1

# The protocol message sent when a peripheral client is sending a beacon to
# a central client.
SENDING_BEACON = 'BT_SENDING_P2P_BEACON'.encode()

# The protocol message sent in response to a peripheral client's beacon request
# by the central client, acknowledging they're ready to receive the beacon.
READY_FOR_BEACON = 'BT_READY_FOR_P2P_BEACON'.encode()
