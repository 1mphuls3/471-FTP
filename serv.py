import os
import socket
import sys

from common import receiveControlMessage, sendControlMessage

# The absolute directory of serverFiles
SERVER_FILES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "serverFiles")

def connectClient(clientIP, port):
    dataSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Connect back to the client's temporary data listener.
    dataSocket.connect((clientIP, port))
    return dataSocket

def handleGetFile(controlSocket, filename, port):
    filePath = os.path.realpath(os.path.join(SERVER_FILES, filename))

    # Reject paths outside of serverFiles
    if os.path.commonpath((SERVER_FILES, filePath)) != SERVER_FILES:
        sendControlMessage(controlSocket, "ERROR INVALID_FILENAME")
        return

    # ERROR response if given file cannot be found or problem with opening it
    try:
        fileObj = open(filePath, "rb")
    except FileNotFoundError:
        sendControlMessage(controlSocket, "ERROR FILE_NOT_FOUND")
        return
    except OSError:
        sendControlMessage(controlSocket, "ERROR FILE_ACCESS")
        return

    dataSocket = None
    try:
        # The client accepts the data connection after receiving READY
        sendControlMessage(controlSocket, "READY")
        dataSocket = connectClient(controlSocket.getpeername()[0], port)
    
        # Stream bytes in chunks
        while True:
            fileData = fileObj.read(4096)
            
            if not fileData:
                break
            
            dataSocket.sendall(fileData)

        sendControlMessage(controlSocket, "SUCCESS")
        
    except OSError:
        sendControlMessage(controlSocket, "ERROR TRANSFER_FAILED")
    finally:
        # Release both resources
        fileObj.close()
        dataSocket.close()

def handlePutFile(controlSocket, filename, port):
    filePath = os.path.realpath(os.path.join(SERVER_FILES, filename))

    # Reject paths outside of serverFiles
    if os.path.commonpath((SERVER_FILES, filePath)) != SERVER_FILES:
        sendControlMessage(controlSocket, "ERROR INVALID_FILENAME")
        print(f"put {filename}: FAILURE (invalid filename)")
        return

    # ERROR response if the destination file cannot be created
    try:
        fileObj = open(filePath, "wb")
    except OSError:
        sendControlMessage(controlSocket, "ERROR FILE_ACCESS")
        print(f"put {filename}: FAILURE (file access)")
        return

    dataSocket = None
    bytesReceived = 0
    succeeded = False
    try:
        # The client accepts the data connection after receiving READY
        sendControlMessage(controlSocket, "READY")
        dataSocket = connectClient(controlSocket.getpeername()[0], port)

        # The data connection closes when the complete file has arrived
        while True:
            fileData = dataSocket.recv(4096)

            if not fileData:
                break

            fileObj.write(fileData)
            bytesReceived += len(fileData)

        sendControlMessage(controlSocket, "SUCCESS")
        succeeded = True
        print(f"put {filename}: SUCCESS ({bytesReceived} bytes)")

    except OSError:
        print(f"put {filename}: FAILURE (transfer failed)")
        try:
            sendControlMessage(controlSocket, "ERROR TRANSFER_FAILED")
        except OSError:
            pass
    finally:
        # Release both resources
        fileObj.close()
        if dataSocket:
            dataSocket.close()
        # Don't leave a partial file behind
        if not succeeded:
            try:
                os.remove(filePath)
            except OSError:
                pass

def handleListFiles(controlSocket, port):
    # ERROR response if the directory cannot be read
    try:
        listing = "\n".join(sorted(os.listdir(SERVER_FILES))).encode("utf-8")
    except OSError:
        sendControlMessage(controlSocket, "ERROR LIST_FAILED")
        print("ls: FAILURE (cannot read directory)")
        return

    dataSocket = None
    try:
        # The client accepts the data connection after receiving READY
        sendControlMessage(controlSocket, "READY")
        dataSocket = connectClient(controlSocket.getpeername()[0], port)

        # Closing the data socket tells the client the listing is complete
        dataSocket.sendall(listing)
        dataSocket.close()
        dataSocket = None

        sendControlMessage(controlSocket, "SUCCESS")
        print("ls: SUCCESS")

    except OSError:
        print("ls: FAILURE (transfer failed)")
        try:
            sendControlMessage(controlSocket, "ERROR TRANSFER_FAILED")
        except OSError:
            pass
    finally:
        if dataSocket:
            dataSocket.close()

def handleQuit(controlSocket):
    sendControlMessage(controlSocket, "BYE")

def handleCommand(controlSocket, commandLine):
    # Separate the command verb from its optional arguments
    commandParts = commandLine.strip().split(maxsplit=1)
    if not commandParts:
        return False

    command = commandParts[0].lower()
    arguments = commandParts[1] if len(commandParts) > 1 else ""

    if command == "get":
        try:
            filename, portText = arguments.rsplit(maxsplit=1)
            port = int(portText)
        except ValueError:
            sendControlMessage(controlSocket, "ERROR INVALID_ARGUMENT")
        else:
            handleGetFile(controlSocket, filename, port)

    elif command == "put":
        try:
            filename, portText = arguments.rsplit(maxsplit=1)
            port = int(portText)
        except ValueError:
            sendControlMessage(controlSocket, "ERROR INVALID_ARGUMENT")
        else:
            handlePutFile(controlSocket, filename, port)

    elif command == "ls":
        try:
            port = int(arguments)
        except ValueError:
            sendControlMessage(controlSocket, "ERROR INVALID_ARGUMENT")
        else:
            handleListFiles(controlSocket, port)

    elif command == "quit":
        handleQuit(controlSocket)
        return True
    else:
        sendControlMessage(controlSocket, "ERROR INVALID_COMMAND")
    return False


# Accept clients and process commands until each session ends
def main():
    serverPort = int(sys.argv[1])

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serverSocket:
        serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serverSocket.bind(("", serverPort))
        serverSocket.listen()

        while True:
            connectionSocket, clientAddress = serverSocket.accept()
            print("Client connected:", clientAddress)

            with connectionSocket:
                while True:
                    try:
                        # Each receive returns one complete framed command
                        commandLine = receiveControlMessage(connectionSocket)
                        if commandLine is None:
                            break
                        if handleCommand(connectionSocket, commandLine):
                            break
                    except (ConnectionError, OSError):
                        break
                    except ValueError:
                        sendControlMessage(connectionSocket, "ERROR INVALID_MESSAGE")
                        break

if __name__ == "__main__":
    main()
