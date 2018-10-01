import socket
import struct
import threading
import time
import cv2
import pygtk
import pygst
import sys

pygst.require('0.10')
import gst

multicast_address = 'ff02::1'  # ipv6: all nodes on the local network segment
bind_port = 13007
multicast_port = 13006
data_port = 49152
timeout = 1.0
connection_init = False
stream_init = False
running = True
timeout = 1.0
count = 0

KA_DATA_MSG = "{\"type\": \"live.data.unicast\", \"key\": \"ab305939-5a40-46c0-b08b-15b901adc6b1\", \"op\": \"start\"}"
KA_VIDEO_MSG = "{\"type\": \"live.video.unicast\", \"key\": \"a178c5e8-e683-411a-9c4c-fcc630ac642e\", \"op\": \"start\"}"

# closefd: avoid socket closing when setting the element to ready
# demux MPEG2 transport stream
# A bus forwards messages from the streaming threads to an application in its own thread context
#"autovideosink name=video"
#"udpsink host=127.0.0.1 port=5000"
PIPEDEF =   "udpsrc name=src !" \
            "mpegtsdemux !" \
            "queue !" \
            "ffdec_h264 !" \
            "autovideosink name=video"

def mksock(peer):
    iptype = socket.AF_INET
    if ':' in peer[0]:
        iptype = socket.AF_INET6
    return socket.socket(iptype, socket.SOCK_DGRAM)

def send_keepalive_msg(socket,msg,peer):
    #print("keeping alive")
    socket.sendto(msg, peer)

def bus_callback():
    print('new message on pipeline')

def stop_sending_msg():
    print("STOPPING")
    global running
    running = False

if __name__ == '__main__':
        
    # setup video and data socket
    multicast_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    multicast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    multicast_socket.bind(('::', bind_port))
    multicast_socket.sendto('{"type":"discover"}', (multicast_address, multicast_port))

    #td = threading.Timer(0, send_keepalive_msg(data_socket,KA_DATA_MSG,peer)).start()
    #td = threading.Timer(0, send_keepalive_msg(video_socket,KA_VIDEO_MSG,peer)).start()
    while running == True:

        # setup when getting multicast response
        if connection_init == False:
            connection_init = True
            data, address = multicast_socket.recvfrom(1024)
            
            # Create socket which will send a keep alive message for the live data stream
            peer = (address[0], data_port)
            data_socket = mksock(peer)
            video_socket = mksock(peer)
            
            threading.Timer(0, send_keepalive_msg, [data_socket,KA_DATA_MSG,peer]).start()
            threading.Timer(0, send_keepalive_msg, [video_socket,KA_VIDEO_MSG,peer]).start()

            pipeline = None
            try:
                print('SETTING UP PIPELINE')
                pipeline = gst.parse_launch(PIPEDEF)
            except Exception, e:
                print("PIPELINE EXCEPTION:" + e)
                stop_sending_msg()
                sys.exit(0)

            print("PIPELINE CREATED")
            src = pipeline.get_by_name("src")
            src.set_property("sockfd", video_socket.fileno()) # bind pipeline to correct socket
            pipeline.set_state(gst.STATE_PLAYING)

        else:
            threading.Timer(0, send_keepalive_msg, [data_socket,KA_DATA_MSG,peer]).start()
            threading.Timer(0, send_keepalive_msg, [video_socket,KA_VIDEO_MSG,peer]).start()
            
            # receiving the data (not the video)
            data, address = data_socket.recvfrom(1024)
            print (data)

        # listen for pipeline status changes
        state_change_return, state, pending_state = pipeline.get_state(0)
        if gst.STATE_CHANGE_FAILURE == state_change_return:
           print("STATE CHANGE")
           stop_sending_msg()
           
    else:
        print("RUNNING IS SET TO FALSE")
