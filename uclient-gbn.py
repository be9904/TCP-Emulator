from socket import *
from threading import Thread
import random
import time

serverIP = '127.0.0.1' # special IP for local host
serverPort = 12000
clientPort = 12001

win = 10      # window size
no_pkt = 100 # the total number of packets to send
send_base = 0 # oldest packet sent
loss_rate = 0.01 # loss rate
seq = 0        # initial sequence number
timeout_flag = 0 # timeout trigger

sent_time = [0 for i in range(2000)]


clientSocket = socket(AF_INET, SOCK_DGRAM)
clientSocket.bind(('', clientPort))
clientSocket.setblocking(0)

# thread for receiving and handling acks
def handling_ack():
    print("thread")
    global clientSocket
    global send_base
    global timeout_flag
    global sent_time

    # constants
    alpha = 0.125
    beta = 0.25

    # timeout interval
    timeout_interval = 10
    
    # pkt delay time
    pkt_delay = 0

    # rtt
    dev_rtt = 0
    init_rtt_flag = 1
    
    # receive loop
    while True:
        # update pkt delay time
        if sent_time[send_base] != 0: 
            pkt_delay = time.time() - sent_time[send_base]
        
        # timeout detected
        if pkt_delay > timeout_interval and timeout_flag == 0:
            print("timeout detected:", str(send_base), flush=True)
            print("timeout interval:", str(timeout_interval), flush=True)
            timeout_flag = 1

        # receive msg from server
        try:
            ack, serverAddress = clientSocket.recvfrom(2048)
            ack_n = int(ack.decode())
            print(ack_n, flush=True)
            
            # estimated rtt based on init rtt
            if init_rtt_flag == 1:
                estimated_rtt = pkt_delay
                init_rtt_flag = 0
            else:
                estimated_rtt = (1-alpha)*estimated_rtt + alpha*pkt_delay
                dev_rtt = (1-beta)*dev_rtt + beta*abs(pkt_delay-estimated_rtt)
            timeout_interval = estimated_rtt + 4*dev_rtt
            
            # 3 dup acks
            if ack_n == -1:
                # retransmit
                pass
            #print("timeout interval:", str(timeout_interval), flush=True)

            
        except BlockingIOError:
            continue
            
        # window is moved upon receiving a new ack
        # window stays for cumulative ack
        send_base = ack_n + 1
        
        # break loop on last packet
        if ack_n == no_pkt-1:
            break

# main

# running a thread for receiving and handling acks
th_handling_ack = Thread(target = handling_ack, args = ())
th_handling_ack.start()

# 
while seq < no_pkt:
    # send packets within window
    while seq < send_base + win:
        # emulate packet loss
        if random.random() < 1 - loss_rate:
            clientSocket.sendto(str(seq).encode(), (serverIP, serverPort))  
        # update sent time
        sent_time[seq] = time.time()    
        # increment seq number
        seq = seq + 1

        # wait
        time.sleep(0.1)
        print('seq:', seq,", send_base:", send_base)
        
    # retransmission
    if timeout_flag == 1:
        # update seq number
        seq = send_base 
        
        # retransmit
        clientSocket.sendto(str(seq).encode(), (serverIP, serverPort))
        
        # update sent time
        sent_time[seq] = time.time()
        
        # log seq number
        print("retransmission:", str(seq), flush=True)
        
        # update seq number and reset timeout flag
        seq = seq + 1
        timeout_flag = 0
        
        
# terminating thread
th_handling_ack.join()

print ("done")

# close client
clientSocket.close()


