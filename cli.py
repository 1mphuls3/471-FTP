import sys
import socket

def getFile(controlSocket, filename):
    pass

def putFile(controlSocket, filename):
    pass

def listFiles(controlSocket):
    pass

def quit(controlSocket):
    pass

def main():
    # Get server info from command line
    serverName = sys.argv[1]
    serverPort = int(sys.argv[2])

    controlSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

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
        
if __name__ == "__main__":
    main()