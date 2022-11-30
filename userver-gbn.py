from socket import *

serverPort = 12000

serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', serverPort))

print('The server is ready to receive')

rcv_base = 0  # next sequence number we wait for

while True:
    message, clientAddress = serverSocket.recvfrom(2048)
    
    # extract sequence number
    seq_n = int(message.decode())
    print(seq_n)

    # in order delivery
    if seq_n == rcv_base:
        rcv_base = seq_n + 1 
    
    serverSocket.sendto(str(rcv_base-1).encode(), clientAddress) # send cumulative ack
    
    # break loop on last packet
    if seq_n == 99:
        break

serverSocket.close()



