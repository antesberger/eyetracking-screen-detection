import socket
import struct
import threading
import time
import cv2

multicast_address = 'ff02::1'  # ipv6: all nodes on the local network segment
bind_port = 13007
multicast_port = 13006
data_port = 49152
timeout = 1.0
init = False
running = True
address = 'ff02::1'

KA_DATA_MSG = "{\"type\": \"live.data.unicast\", \"key\": \"ab305939-5a40-46c0-b08b-15b901adc6b1\", \"op\": \"start\"}"
KA_VIDEO_MSG = "{\"type\": \"live.video.unicast\", \"key\": \"a178c5e8-e683-411a-9c4c-fcc630ac642e\", \"op\": \"start\"}"

def send_keepalive_msg(socket, msg, peer):
    print("Sending " + msg + " to target " + peer[0] + " socket no: " + str(socket.fileno()) + "\n")
    socket.sendto(msg, peer)
    time.sleep(1000)

if __name__ == '__main__':
    data_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    data_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    data_socket.bind(('::', bind_port))
    data_socket.sendto('{"type":"discover"}', (multicast_address, multicast_port))

    video_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    video_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    video_socket.bind(('::', bind_port))



    while True:
        print('RECEIVING NEW DATA')
        data, address = data_socket.recvfrom(10024)
        if init == False:
            init = True
            
            td = threading.Timer(0, send_keepalive_msg, [data_socket, KA_DATA_MSG, (address[0], data_port)])
            td.start()

            td = threading.Timer(0, send_keepalive_msg, [video_socket, KA_VIDEO_MSG, (address[0], data_port)])
            td.start()
        else:
            print(type(data))
            #sp.call(['ffplay', '-'], stdin = data, universal_newlines = False)
            #cv2.imshow('frame',data)

        print (" From: " + address[0] + " " + data)
