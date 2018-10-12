import cv2
import time
import threading

#gst-launch udpsrc caps="application/x-rtp,payload=127" port=5000 ! rtph264depay ! capsfilter caps="video/x-h264,width=1920,height=1080" ! ffdec_h264 ! autovideosink
#gst-launch udpsrc caps="application/x-rtp,payload=127" port=5000 ! rtph264depay ! ffdec_h264 ! autovideosink
#"udpsrc caps=application/x-rtp,payload=127 port=5000 ! rtph264depay ! ffdec_h264 ! appsink name=opencvsink"
cap = cv2.VideoCapture("123.sdp")

dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
frame_buffer = []
last_processed_frame = None

if(cap.isOpened()==False):
    print "false"
else:
    print "open"

def processFrame(frame):
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) # aruco.detectMarkers() requires gray image
    markers = cv2.aruco.detectMarkers(frame_gray,dictionary)
    # corners, ids, rejectedImgPoints = markers
    # #cv2.aruco.refineDetectedMarkers(frame_gray, board, corners, ids, rejectedImgPoints)

    if len(markers[0]) > 0:
        print("marker detected")
        marker_image = cv2.aruco.drawDetectedMarkers(frame_gray,markers[0],markers[1])
    else:
        print("no markers in frame")

    last_processed_frame = frame_gray
    return frame_gray

i = 0
while(True):
    
    if i < 100:
        i = i + 1
        print i
        ret, frame = cap.read()
        frame_buffer.insert(len(frame_buffer),frame)

    else:
        # if thread count < x
        print(len(frame_buffer))
        last_processed_frame = processFrame(frame_buffer[0])
        frame_buffer.pop(0)
        
        cv2.imshow('frame',last_processed_frame)

        if( cv2.waitKey(100) == 27 ):
            break


