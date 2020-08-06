## What is this?
`bluetrace` is my Python implementation of a simple BlueTrace/COVIDSafe protocol simulator, developed for an assignment in UNSW's COMP3331.

In 2020, the COVID-19 pandemic precipitated the need for effective contract tracing as one of the conditions for society to return to its normal state. In the real world, these systems take the form of mobile applications installed on people's phones that communicate with one another using Bluetooth Low Energy technology, and to central health authority servers over the internet.

This simulator makes a few simplifications:
- Both the client and server applications are run on the terminal.
- Client-to-server communication occurs via TCP.
- Bluetooth Low Energy communications between clients are simulated using UDP.
- The clearance times for information (contact logs, temporary identifiers, etc.) are reduced to a matter of minutes rather than the days found in the real BlueTrace/COVIDSafe applications.

## How do I use it?
Run the server program by specifying a port number and the duration (in seconds) to block clients for upon repeated authentication failure:
```
python3 server.py [server port] [block duration]
```
Run a client program by specifying a server IP, a server port and a port to use for peer-to-peer UDP communication:
```
python3 client.py [server IP] [server port] [client UDP port]
```

After starting the client program and logging into a running server program, a client can enter the following commands:
| **Command**        | **Arguments** | **Meaning**                                                                      |
|--------------------|---------------|----------------------------------------------------------------------------------|
| download_tempid    | N/A           | Downloads a new temporary identifier, valid for the next 15 minutes.             |
| upload_contact_log | N/A           | Uploads the contents of the client's contact log to the server for checking.     |
| beacon             | `IP`, `Port`      | Sends a contact beacon containing the current temporary ID to a user at `IP:Port`. |

## Want to know more?
Read the included 3 page report (in `report.pdf`) for more information about the design of the program (if you care).
