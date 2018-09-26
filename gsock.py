import socket
import struct
import threading
import time
import cv2
import subprocess as sp
import gi 
gi.require_version('Gst', '1.0')
from gi.repository import Gst, Gio, GLib

multicast_address = 'ff02::1'  # ipv6: all nodes on the local network segment
bind_port = 13007
multicast_port = 13006
data_port = 49152
timeout = 1.0
connection_init = False
stream_init = False
running = True
address = 'ff02::1'

KA_DATA_MSG = "{\"type\": \"live.data.unicast\", \"key\": \"ab305939-5a40-46c0-b08b-15b901adc6b1\", \"op\": \"start\"}"
KA_VIDEO_MSG = "{\"type\": \"live.video.unicast\", \"key\": \"a178c5e8-e683-411a-9c4c-fcc630ac642e\", \"op\": \"start\"}"

def send_keepalive_msg(socket, msg, peer):
    print("Sending " + msg + " to target " + peer[0] + " socket no: " + str(socket.fileno()) + "\n")
    socket.sendto(msg, peer)
    time.sleep(1000)

def bus_callback():
    print('new message on pipeline')

if __name__ == '__main__':
    data_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    data_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    data_socket.bind(('::', bind_port))
    data_socket.sendto('{"type":"discover"}', (multicast_address, multicast_port))

    # video_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    # video_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # video_socket.bind(('::', bind_port))
    # video_socket.sendto('{"type":"discover"}', (multicast_address, multicast_port))

    #reset videostream textfile
    #video_stream = open("./out/stream.h264", "w")
    #video_stream.write('')

    #PIPEDEF=[
    #    'udpsrc name=src blocksize=1316 close-socket=false buffer-size=5600', # UDP video data
    #    "tsparse",                      # parse the incoming stream to MPegTS
    #    "tsdemux emit-stats=True",      # get pts statistics from the MPegTS stream
    #    "queue",                        # build queue for the decoder 
    #    "avdec_h264 max-threads=0",     # decode the incoming stream to frames
    #    "identity name=decoded",        # used to grab video frame to be displayed
    #    "textoverlay name=textovl text=* halignment=position valignment=position xpad=0  ypad=0", # simple text overlay
    #    "autovideosink" # Output on XV video
    #]
    # closefd: avoid socket closing when setting the element to ready
    #Gst.init(None)
    #pipeline = Gst.parse_launch(" ! ".join(PIPEDEF))

    # Add watch to pipeline to get tsdemux messages
    # A bus forwards messages from the streaming threads to an application in its own thread context
    #bus = pipeline.get_bus()
    #bus.connect('message', bus_callback)
    #bus.add_signal_watch()

    # Set socket to get data from out socket
    #src = pipeline.get_by_name("src")
    #src.set_property("socket", video_socket) #don't allocate a new socket but use the provided one
    
    # Catch decoded frames
    #decoded = pipeline.get_by_name("decoded")
    #decoded.connect("handoff", decoded_buffer)
    
    # Store overlay object
    #self._textovl = self._pipeline.get_by_name("textovl")
    
    # Start video streaming
    #self._keepalive = KeepAlive(self._sock, peer, "video")
    
    # Start the video pipeline
    #self._pipeline.set_state(gst.STATE_PLAYING)

    while running == True:
        #print('RECEIVING NEW DATA')
        data, address = data_socket.recvfrom(10024)
        #data, address = video_socket.recvfrom(2048)
        if connection_init == False:
            connection_init = True

            data_socket.close()

            client = Gio.SocketClient()
            video_socket = Gio.InetSocketAddress.new_from_string(address[0], data_port)
            #video_socket = Gio.InetSocketAddress(multicast_address, multicast_port)
            video_conn = client.connect(video_socket, Gio.Cancellable())
            video_stream = conn.get_output_stream()
            stream.write (KA_VIDEO_MSG, Gio.Cancellable())

            istream = Gio.DataInputStream (video_conn.get_input_stream())
            message = istream.read_line()
            print "received status line: " + message

            #td = threading.Timer(0, send_keepalive_msg, [data_socket, KA_DATA_MSG, (address[0], data_port)])
            #td.start()

            #td = threading.Timer(0, send_keepalive_msg, [video_socket, KA_VIDEO_MSG, (address[0], data_port)])
            #td.start()
        #else:
            #pipeline.set_state(gst.STATE_PLAYING)
        print (" From: " + address[0] + " " + data)
