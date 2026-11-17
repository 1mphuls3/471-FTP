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
        bytesReceived = 0
        with dataSocket, open(localPath, "wb") as fileObj:
            # The data connection closes when the complete file has arrived
            while True:
                fileData = dataSocket.recv(4096)

                if not fileData:
                    break
                    
                fileObj.write(fileData)
                bytesReceived += len(fileData)

        response = receiveControlMessage(controlSocket)

        if response == "SUCCESS":
            print(f"Downloaded {filename}! ({bytesReceived} bytes)")
        else:
            print(response or "Server closed the connection")

    except (OSError, ValueError, ConnectionError) as error:
        print(f"Download failed: {error}")
    finally:
        dataServer.close()

def putFile(controlSocket, filename):
    clientRoot = os.path.realpath(CLIENT_FILES)
    localPath = os.path.realpath(os.path.join(CLIENT_FILES, filename))

    # Reject paths outside of clientFiles
    if os.path.commonpath((clientRoot, localPath)) != clientRoot:
        print("Upload failed: invalid filename")
        return

    # Make sure the file can be read before involving the server
    try:
        fileObj = open(localPath, "rb")
    except OSError as error:
        print(f"Upload failed: {error}")
        return

    dataServer, port = createDataConnection()
    try:
        with fileObj:
            # Tell the server which port will send the file data to
            sendControlMessage(controlSocket, f"put {filename} {port}")
            response = receiveControlMessage(controlSocket)
            if response != "READY":
                print(response or "Server closed the connection")
                return

            dataSocket, addr = dataServer.accept()
            bytesSent = 0
            with dataSocket:
                # Stream bytes in chunks
                while True:
                    fileData = fileObj.read(4096)

                    if not fileData:
                        break

                    dataSocket.sendall(fileData)
                    bytesSent += len(fileData)
            # Closing the data socket tells the server the file is complete

        response = receiveControlMessage(controlSocket)

        if response == "SUCCESS":
            print(f"Uploaded {filename}! ({bytesSent} bytes)")
        else:
            print(response or "Server closed the connection")

    except (OSError, ValueError, ConnectionError) as error:
        print(f"Upload failed: {error}")
    finally:
        dataServer.close()

def listFiles(controlSocket):
    dataServer, port = createDataConnection()
    try:
        # Tell the server which port will accept the listing
        sendControlMessage(controlSocket, f"ls {port}")
        response = receiveControlMessage(controlSocket)
        if response != "READY":
            print(response or "Server closed the connection")
            return

        dataSocket, addr = dataServer.accept()
        listing = bytearray()
        with dataSocket:
            # The data connection closes when the whole listing has arrived
            while True:
                chunk = dataSocket.recv(4096)

                if not chunk:
                    break

                listing.extend(chunk)

        response = receiveControlMessage(controlSocket)

        if response == "SUCCESS":
            text = listing.decode("utf-8", errors="replace")
            if text:
                print(text)
        else:
            print(response or "Server closed the connection")

    except (OSError, ValueError, ConnectionError) as error:
        print(f"Listing failed: {error}")
    finally:
        dataServer.close()

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