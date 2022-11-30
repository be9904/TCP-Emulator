from socket import *
from threading import Thread

serverPort = 12000

serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', serverPort))

print('The server is ready to receive')

rcv_base = 0  # next sequence number we wait for
win = 20

class ServerQueue():
    def __init__(self, size):
        self.queue = []
        self.size = size
 
    def enqueue(self, value):
        if len(self.queue) <= self.size:
            self.queue.append(value)
            return True
        return False
 
    def dequeue(self):
        return self.queue.pop(0)

sq = ServerQueue(win)

while True:
    message, clientAddress = serverSocket.recvfrom(2048)
    
    # extract sequence number
    seq_n = int(message.decode())
    print(seq_n)

    # in order delivery
    if seq_n == rcv_base:
        if sq.enqueue(seq_n):
            rcv_base = seq_n + 1
    
    if len(sq.queue) > 0:
        sq.dequeue()

    serverSocket.sendto(str(rcv_base-1).encode(), clientAddress) # send cumulative ack
    
    # break loop on last packet
    if seq_n == 999:
        break

serverSocket.close()



