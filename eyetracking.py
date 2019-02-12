import socket
import threading
import time
import cv2
import pygtk
import glib
import pygst
import sys
import ast
import datetime
import os
import urllib2
import json
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
recording_id = ''

if len(sys.argv) < 2:
    print "\nexpected participant id but no argument was given."
    sys.exit(1)
else:
    participant_global_identification = sys.argv[1]

KA_DATA_MSG = "{\"type\": \"live.data.unicast\", \"key\": \"ab305939-5a40-46c0-b08b-15b901adc6b1\", \"op\": \"start\"}"
KA_VIDEO_MSG = "{\"type\": \"live.video.unicast\", \"key\": \"a178c5e8-e683-411a-9c4c-fcc630ac642e\", \"op\": \"start\"}"

#demux -> media stream to mpeg transpor stream
#h264parse -> parse h264 stream
#rtph264 -> payload-encode h264 video into rtp packets
#udpsink -> rtp is sent over udp
PIPEDEF_UDP =   "udpsrc name=src !" \
            "mpegtsdemux !" \
            "queue !" \
            "h264parse !" \
            "rtph264pay !" \
            "udpsink name=sink host=127.0.0.1 port=5000"

def mksock(peer):
    iptype = socket.AF_INET
    if ':' in peer[0]:
        iptype = socket.AF_INET6
    new_socket = socket.socket(iptype, socket.SOCK_DGRAM)
    new_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    new_socket.settimeout(3.0)

    return new_socket

def send_keepalive_msg(socket,msg,peer):
    #print("keeping alive")
    socket.sendto(msg, peer)

def stop_sending_msg():
    print("STOPPING")
    global running
    running = False

def create_project(address):
    json_data = post_request(address, '/api/projects')
    return json_data['pr_id']

def create_participant(address,project_id):
    data = {'pa_project': project_id}
    json_data = post_request(address, '/api/participants', data)
    return json_data['pa_id']

def create_calibration(address, project_id, participant_id):
    data = {'ca_project': project_id, 'ca_type': 'default', 'ca_participant': participant_id}
    json_data = post_request(address, '/api/calibrations', data)
    return json_data['ca_id']

def create_recording(address, participant_id):
    data = {'rec_participant': participant_id}
    json_data = post_request(address, '/api/recordings', data)
    return json_data['rec_id']

def start_recording(address, recording_id):
    post_request(address, '/api/recordings/' + recording_id + '/start')

def stop_recording(address, recording_id):
    post_request(address, '/api/recordings/' + recording_id + '/stop')

def start_calibration(address, calibration_id):
    post_request(address, '/api/calibrations/' + calibration_id + '/start')

def post_request(url, api_action, data=None):
    req = urllib2.Request(url + api_action)
    req.add_header('Content-Type', 'application/json')
    data = json.dumps(data)
    response = urllib2.urlopen(req, data)
    data = response.read()
    json_data = json.loads(data)
    return json_data

def wait_for_status(url, api_action, key, values, calibration_id, participant_id):
    waiting = True
    while waiting:
        req = urllib2.Request(url + api_action)
        req.add_header('Content-Type', 'application/json')
        response = urllib2.urlopen(req, None)
        data = response.read()
        json_data = json.loads(data)

        if json_data['ca_state'] == 'calibrated':
            waiting = False
            print '\ncalibration successfull'
            time.sleep(0.5)

        elif json_data['ca_state'] == 'failed':
            yes = {'yes','y', 'ye', ''}
            no = {'no','n'}

            print '\ncalibration failed'
            time.sleep(0.5)
            choice = raw_input("type 'yes' to retry or 'no' to use the default calibration >>\n").lower()
            if choice in yes:
                setup(url)
                break
            elif choice in no:
                waiting = False
                print '\nusing default calibration'
            else:
                choice = raw_input("type 'yes' to retry or 'no' to use the default calibration >>\n").lower()

        time.sleep(1)

    #recording_id = create_recording(api_address, participant_id)
    #print recording_id
    #start_recording(url, recording_id)
    #print ('\nstarted recording ...')

def setup(api_address):
    print('\ncreating project and participant at: ' + api_address)

    project_id = create_project(api_address)
    participant_id = create_participant(api_address, project_id)
    calibration_id = create_calibration(api_address, project_id, participant_id)

    print "Project: " + project_id, ", Participant: ", participant_id, ", Calibration: ", calibration_id, " "

    # calibration
    print('\nTo calibrate please hold the calibration card with about 1m distance in front of the participants eyes. \nThe participant then has to focus on the circles center point.')
    input_var = raw_input("\nPress enter to calibrate >>")
    print ('starting calibration ...')

    start_calibration(api_address, calibration_id)
    status = wait_for_status(api_address, '/api/calibrations/' + calibration_id + '/status', 'ca_state', ['failed', 'calibrated'], calibration_id, participant_id)

    print('\nStream is ready to start. Please tell the participant to take his position, explain his task and hand him the smartphone.')
    input_var = raw_input("Press enter to start the task >>")
    print('\nStraming in progess ...')

if __name__ == '__main__':

    # setup video and data socket
    multicast_socket = mksock( (multicast_address, bind_port))
    multicast_socket.bind(('::', bind_port))
    multicast_socket.sendto('{"type":"discover"}', (multicast_address, multicast_port))

    while running == True:

        # setup when getting multicast response
        if connection_init == False:
            connection_init = True

            try:
                data, address = multicast_socket.recvfrom(1024) #fe80::2c20:dcff:fe09:3a01%13
            except socket.error, e:
                print(e)
                multicast_socket.close()
                sys.exit(0)

            print("\n\nReceived From: " + address[0] + " -> Data: " + data)
            multicast_socket.close()

            # Create socket which will send a keep alive message for the live data stream
            peer = (address[0], data_port)
            data_socket = mksock(peer)
            video_socket = mksock(peer)

            threading.Timer(0, send_keepalive_msg, [data_socket,KA_DATA_MSG,peer]).start()
            threading.Timer(0, send_keepalive_msg, [video_socket,KA_VIDEO_MSG,peer]).start()

            pipeline = None
            try:
                pipeline = gst.parse_launch(PIPEDEF_UDP)
            except Exception, e:
                print(e)
                print('Please check your connect to the eyetracking device and restart the script.')
                stop_sending_msg()
                sys.exit(0)

            print("Connection to glasses established")
            src = pipeline.get_by_name("src")
            src.set_property("sockfd", video_socket.fileno()) # bind pipeline to correct socket
            pipeline.set_state(gst.STATE_PLAYING)

            #participant_global_identification = raw_input("Press enter the participants identification >>")

            #api_address = 'http://' + json.loads(data)['ipv4']
            #api_address = 'http://[fe80::76fe:48ff:fe25:2340]'
            api_address = 'http://[' + address[0][:-3] + ']'
            setup(api_address)

            # create directory the eyetracking data gets stored in
            eyetracking_directory = './out/{0}-{1}'.format(participant_global_identification, datetime.datetime.now().strftime("%Y-%m-%d"))
            if not os.path.exists(eyetracking_directory):
                os.makedirs(eyetracking_directory)
            eytracking_file = open(eyetracking_directory + "/eyetracking_data_raw.txt", "a+")

            # start openCV script to receive stream
            os.system('start processing.py ' + participant_global_identification)

        else:
            threading.Timer(0, send_keepalive_msg, [data_socket,KA_DATA_MSG,peer]).start()
            threading.Timer(0, send_keepalive_msg, [video_socket,KA_VIDEO_MSG,peer]).start()

            # receiving the data (not the video)
            try:
                data, address = data_socket.recvfrom(1024)
            except socket.error, e:
                print(e)
                data_socket.close()
                sys.exit(0)

            # write eyetracking data to file
            data = data[:-2] + ',"ats":"' + datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f") + '"}\n'
            eytracking_file.write(data)

        # listen for pipeline status changes
        state_change_return, state, pending_state = pipeline.get_state(0)
        if gst.STATE_CHANGE_FAILURE == state_change_return:
           print("STATE CHANGE")
           stop_sending_msg()

    else:
        print("RUNNING IS SET TO FALSE")
