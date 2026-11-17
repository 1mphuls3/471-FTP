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

def handlePutFile(controlSocket, filename):
    pass

def handleListFiles(controlSocket):
    pass

def handleQuit(controlSocket):
    sendControlMessage(controlSocket, "BYE")

def handleCommand(controlSocket, commandLine):
    # Separate the command verb from its optional arguments
    commandParts = commandLine.strip().split(maxsplit=1)
    if not commandParts:
        return False

    command = commandParts[0].lower()
    if command == "get":
        arguments = commandParts[1]
        try:
            filename, portText = arguments.rsplit(maxsplit=1)
            port = int(portText)
        except ValueError:
            sendControlMessage(controlSocket, "ERROR INVALID_ARGUMENT")
        else:
            handleGetFile(controlSocket, filename, port)

    elif command == "put":
        arguments = commandParts[1]
        if arguments:
            handlePutFile(controlSocket, arguments)
        else:
            sendControlMessage(controlSocket, "ERROR INVALID_ARGUMENT")

    elif command == "ls":
        handleListFiles(controlSocket)
        
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
