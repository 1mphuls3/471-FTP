import sys
import socket

def main():
    serverPort = int(sys.argv[1])

    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind(('', serverPort))

    serverSocket.listen(1)

    while True:
        connectionSocket, clientAddress = serverSocket.accept()

        print("Client connected:", clientAddress)

        connectionSocket.close()
if __name__ == "__main__":
    main()