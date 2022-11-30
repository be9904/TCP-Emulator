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
tdupack_flag = 0 # 3 dup ack trigger
timeout_flag = 0 # timeout trigger

tri_dup_mode = True
timeout_mode = True

sent_time = [0 for i in range(2000)]
dup_count = 0

clientSocket = socket(AF_INET, SOCK_DGRAM)
clientSocket.bind(('', clientPort))
clientSocket.setblocking(0)

lost_pkts_td = []
lost_pkts_to = []

latency_sum = 0

# thread for receiving and handling acks
def handling_ack():
    print("thread")
    global clientSocket
    global send_base
    global timeout_flag
    global sent_time
    global latency_sum

    # constants
    alpha = 0.125
    beta = 0.25

    # timeout interval
    timeout_interval = 10
    
    # dup count
    global dup_count
    global tdupack_flag
    prev_ack = 0

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
        if pkt_delay > timeout_interval and timeout_flag == 0 and timeout_mode:
            # always timeout on first packet??
            print("timeout detected:", str(send_base), flush=True)
            print("timeout interval:", str(timeout_interval), flush=True)
            print('-------------------------------------')
            lost_pkts_to.append(send_base)
            timeout_flag = 1

        # receive msg from server
        try:
            ack, serverAddress = clientSocket.recvfrom(2048)
            ack_n = int(ack.decode())
            print('received', ack_n, 'from server', flush=True)
            print('-------------------------------------')
            
            # does rtt update on 3 dup acks? -> no, ignore retransmissions
            # implement condition for updating dup_count
            if prev_ack == ack_n:
                dup_count += 1
            prev_ack = ack_n

            # check 3 dup acks
            if dup_count > 3 and tri_dup_mode:
                print('***3 dup acks detected***', flush=True)
                print('-------------------------------------')
                dup_count = 0
                tdupack_flag = 1
                lost_pkts_td.append(ack_n+1)
                continue
                # retransmit
            
            latency_sum += pkt_delay

            # print('before computation timeout_interval:', str(timeout_interval)) 
            # estimated rtt based on init rtt
            if init_rtt_flag == 1:
                estimated_rtt = pkt_delay
                print('estimated rtt:', estimated_rtt)
                print('-------------------------------------')
                init_rtt_flag = 0
            else:
                estimated_rtt = (1-alpha)*estimated_rtt + alpha*pkt_delay
                dev_rtt = (1-beta)*dev_rtt + beta*abs(pkt_delay-estimated_rtt)
            timeout_interval = estimated_rtt + 4*dev_rtt      
            # print(send_base, ":", timeout_interval)
            # print('computed timeout_interval:', str(timeout_interval))      
            # print("timeout interval:", str(timeout_interval), flush=True)

            
        except BlockingIOError:
            continue
            
        # window is moved upon receiving a new ack
        # window stays for cumulative ack
        send_base = ack_n + 1
        
        # break loop on last packet
        if ack_n == no_pkt-1:
            print('break')
            break

# main

# running a thread for receiving and handling acks
th_handling_ack = Thread(target = handling_ack, args = ())
th_handling_ack.start()

# 
while seq < no_pkt:
    # send packets within window
    while seq < send_base + win and seq < no_pkt:
        # emulate packet loss
        if random.random() < 1 - loss_rate:
            print('send', str(seq), 'to server') 
            print('-------------------------------------')
            clientSocket.sendto(str(seq).encode(), (serverIP, serverPort)) 
        # update sent time
        sent_time[seq] = time.time()
        # increment seq number
        seq = seq + 1

        # 3 dup acks
        if tdupack_flag == 1 and tri_dup_mode:
            # update seq number
            seq = send_base 
            
            # retransmit
            clientSocket.sendto(str(seq).encode(), (serverIP, serverPort))
            
            # update sent time
            sent_time[seq] = time.time()
            
            # log seq number
            print("retransmission(3 dup acks):", str(seq), flush=True)
            print('-------------------------------------')
            
            # update seq number and reset timeout flag
            seq = seq + 1
            tdupack_flag = 0

        # wait
        time.sleep(0.02)

    # retransmission
    if timeout_flag == 1 and timeout_mode:
        # update seq number
        seq = send_base 
        
        # retransmit
        clientSocket.sendto(str(seq).encode(), (serverIP, serverPort))
        
        # update sent time
        sent_time[seq] = time.time()
        
        # log seq number
        print("retransmission(timeout):", str(seq), flush=True)
        print('-------------------------------------')
        
        # update seq number and reset timeout flag
        seq = seq + 1
        timeout_flag = 0
        
# terminating thread
th_handling_ack.join()

print('3 dup loss:', lost_pkts_td)
print('timeout loss:', lost_pkts_to)
print('average latency:', latency_sum/no_pkt)
print('throughput:', no_pkt/latency_sum)
print ("done")
print('-------------------------------------')

# close client
clientSocket.close()


