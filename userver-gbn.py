from socket import *

serverPort = 12000

serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', serverPort))

print('The server is ready to receive')

rcv_base = 0  # next sequence number we wait for
dup_count = 0

while True:
    message, clientAddress = serverSocket.recvfrom(2048)
    seq_n = int(message.decode()) # extract sequence number
    print(seq_n)
    if seq_n == rcv_base: # in order delivery
        rcv_base = seq_n + 1 
    else:
        dup_count += 1
    
    if dup_count >= 3:
        serverSocket.sendto(str(-1).encode(), clientAddress)
        dup_count = 0
    else:    
        serverSocket.sendto(str(rcv_base-1).encode(), clientAddress) # send cumulative ack
    if seq_n == 999:
        break;

serverSocket.close()



