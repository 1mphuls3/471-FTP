import os
import socket
import sys

from common import receiveControlMessage, sendControlMessage

# The absolute directory of clientFiles
CLIENT_FILES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clientFiles")

def getFile(controlSocket, filename):
    clientRoot = os.path.realpath(CLIENT_FILES)
    localPath = os.path.realpath(os.path.join(CLIENT_FILES, filename))

    dataServer, port = createDataConnection()
    try:
        # Tell the server which port will accept the file data
        sendControlMessage(controlSocket, f"get {filename} {port}")
        response = receiveControlMessage(controlSocket)
        if response != "READY":
            print(response or "Server closed the connection")
            return

        dataSocket, addr = dataServer.accept()
        with dataSocket, open(localPath, "wb") as fileObj:
            # The data connection closes when the complete file has arrived
            while True:
                fileData = dataSocket.recv(4096)

                if not fileData:
                    break
                    
                fileObj.write(fileData)

        response = receiveControlMessage(controlSocket)

        if response == "SUCCESS":
            print(f"Downloaded {filename}!")
        else:
            print(response or "Server closed the connection")

    except (OSError, ValueError, ConnectionError) as error:
        print(f"Download failed: {error}")
    finally:
        dataServer.close()

def putFile(controlSocket, filename):
    dataSocket, port = createDataConnection()
    pass

def listFiles(controlSocket):
    dataSocket, port = createDataConnection()
    pass

def quit(controlSocket):
    sendControlMessage(controlSocket, "quit")
    # Confirm the server has ended the session before closing the control socket
    response = receiveControlMessage(controlSocket)
    if response != "BYE":
        print(response or "Server closed the connection")
    
def main():
    # Get server info from command line
    serverName = sys.argv[1]
    serverPort = int(sys.argv[2])

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as controlSocket:
        controlSocket.connect((serverName, serverPort))

        while True:
            command = input("ftp> ")

            if command.startswith("get "):
                filename = command.split(maxsplit=1)[1]
                getFile(controlSocket, filename)

            elif command.startswith("put "):
                filename = command.split(maxsplit=1)[1]
                putFile(controlSocket, filename)

            elif command == "ls":
                listFiles(controlSocket)

            elif command == "quit":
                quit(controlSocket)
                break

def createDataConnection():
    dataSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM )
    dataSocket.bind(('', 0))

    # Listen on an ephemeral port for incoming data transfer
    port = dataSocket.getsockname()[1]
    dataSocket.listen(1)

    return dataSocket, port

if __name__ == "__main__":
    main()