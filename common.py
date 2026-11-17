# Size of the header of control messages in bytes
HEADER_SIZE = 10

# Shared control message for the client and server
def sendControlMessage(controlSocket, message):
    body = message if isinstance(message, bytes) else message.encode("ascii")
    # Prefix with the header of data length
    header = f"{len(body):0{HEADER_SIZE}d}".encode("ascii")
    controlSocket.sendall(header + body)

def receiveBytes(connectionSocket, byteCount):
    data = bytearray()
    # Split the message across multiple recv calls
    while len(data) < byteCount:
        chunk = connectionSocket.recv(byteCount - len(data))
        if not chunk:
            if not data:
                return None
            raise ConnectionError("Connection closed before the message arrived")
        data.extend(chunk)
    return bytes(data)

def receiveControlMessage(controlSocket):
    header = receiveBytes(controlSocket, HEADER_SIZE)
    if header is None:
        return None
    if not header.isdigit():
        raise ValueError("Invalid control message header")

    # Read the body length declared in the header
    body = receiveBytes(controlSocket, int(header))
    if body is None:
        raise ConnectionError("Connection closed before the message body arrived")
    return body.decode("ascii")
