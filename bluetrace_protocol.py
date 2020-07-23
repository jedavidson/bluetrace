# bluetrace_protocol.py: A specification of constants used in BlueTrace communications
# by James Davidson for COMP3331, 20T2

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

# The protocol message sent when a client is downloading a temp ID.
DOWNLOAD_TEMP_ID = 'BT_DOWN_TEMP_ID'.encode()

''' Uploading contact logs '''

# The protocol message sent when a client is uploading a contact log.
UPLOAD_CONTACT_LOG = 'BT_UPLOAD_CONTACT_LOG'.encode()
