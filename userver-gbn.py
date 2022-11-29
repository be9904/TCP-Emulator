from socket import *

serverPort = 12000

serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', serverPort))

print('The server is ready to receive')

rcv_base = 0  # next sequence number we wait for
dup_count = 0

while True:
    message, clientAddress = serverSocket.recvfrom(2048)
    
    # extract sequence number
    seq_n = int(message.decode())
    print(seq_n)

    # in order delivery
    if seq_n == rcv_base:
        rcv_base = seq_n + 1 
    else:
        dup_count += 1
    
    # check dup
    if dup_count >= 3:
        # serverSocket.sendto(str(-1).encode(), clientAddress)
        print('dup_count:', dup_count)
        dup_count = 0
    else:    
        serverSocket.sendto(str(rcv_base-1).encode(), clientAddress) # send cumulative ack
    
    # break loop on last packet
    if seq_n == 99:
        break

serverSocket.close()



