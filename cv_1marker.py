import cv2
import time
import threading
import Queue
import numpy
from numpy import array
import sys

#gst-launch udpsrc caps="application/x-rtp,payload=127" port=5000 ! rtph264depay ! capsfilter caps="video/x-h264,width=1920,height=1080" ! ffdec_h264 ! autovideosink
#gst-launch udpsrc caps="application/x-rtp,payload=127" port=5000 ! rtph264depay ! ffdec_h264 ! autovideosink
#"udpsrc caps=application/x-rtp,payload=127 port=5000 ! rtph264depay ! ffdec_h264 ! appsink name=opencvsink"

dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
frames = Queue.Queue()
frame_width = 0
frame_height = 0
recording_flag = True

dist = [[ -2.49084216e-02, 2.80228077e-01, -8.09293716e-06, 2.88316526e-04, -6.39280807e-01]]
cameraMatrix = [[ 734.71252441, 0., 806.11233199][0., 686.70733643, 377.31751302][0.,0.,1.,]]

class ImageGrabber(threading.Thread):
    def __init__(self, ID):
        threading.Thread.__init__(self)
        self.ID=ID
        #self.stream = cv2.VideoCapture(config.sdp")
        self.stream = cv2.VideoCapture("./markers/test13.mp4")

    def run(self):
        global frames
        global frame_width
        global frame_height
        global recording_flag 
        
        frame_width = int(self.stream.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(self.stream.get(cv2.CAP_PROP_FRAME_HEIGHT))

        while True:
            # TODO: Skip frame for which decoding errors were thrown
            ret,frame = self.stream.read()

            if ret == True:
                frame = cv2.resize(frame, (frame_width/2,frame_height/2))
                frames.put(frame)
            else:
                recording_flag = False
                self.stream.release()
                print("couldn't capture frame")
                break

            #time.sleep(0.025)

class Main(threading.Thread):
    def __init(self):
        threading.Thread.__init(self)

    def drawCircle(self,img,x,y):
        #draw screen estimates
        cv2.circle(
            img,
            (x,y), #center
            5, #radius
            (255,0,0), 
            thickness=1, 
            lineType=8, 
            shift=0
        )

    def run(self):
        global frames
        global frame_width
        global frame_height
        global recording_flag

        self.marker_size = 62 #rectangular (mm)
        self.screen_height = 110 #mm
        self.screen_width = 62 #mm
        
        self.corner_refine_criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

        out = cv2.VideoWriter('outpy.avi',cv2.VideoWriter_fourcc('M','J','P','G'), 25, (620,1100))

        cv2.useOptimized()

        while not (frames.qsize() == 0 and recording_flag == False):
            if(not frames.empty()):
                self.current_frame = frames.get()
                #print(frames.qsize())
                frame_gray = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2GRAY) # aruco.detectMarkers() requires gray image
                markers = cv2.aruco.detectMarkers(frame_gray,dictionary)

                if len(markers[0]) > 0:

                    # array order of corners is clockwise
                    corners, ids, rejectedImgPoints = markers

                    #get index of marker with id == 0
                    try:
                        id0 = ids.tolist().index([0])
                    except:
                        print("No marker with id == 0 detected")
                        continue

                    #corners = array(corners)
                    term = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_COUNT, 30, 0.1)
                    corners[id0] = cv2.cornerSubPix(frame_gray, corners[id0], (5, 5), (-1, -1), term)

                    marker_top_left_x = int(corners[id0][0][0][0])
                    marker_top_left_y = int(corners[id0][0][0][1])
                    marker_top_right_x = int(corners[id0][0][1][0])
                    marker_top_right_y = int(corners[id0][0][1][1])
                    marker_bottom_left_x = int(corners[id0][0][3][0])
                    marker_bottom_left_y = int(corners[id0][0][3][1])
                    marker_bottom_right_x = int(corners[id0][0][2][0])
                    marker_bottom_right_y = int(corners[id0][0][2][1])

                    self.drawCircle(self.current_frame, marker_top_left_x, marker_top_left_y)
                    self.drawCircle(self.current_frame, marker_top_right_x, marker_top_right_y)
                    self.drawCircle(self.current_frame, marker_bottom_right_x, marker_bottom_right_y)
                    self.drawCircle(self.current_frame, marker_bottom_left_x, marker_bottom_left_y)

                    #estimate 1mm = ?px
                    marker_height = numpy.sqrt(numpy.power(marker_bottom_left_y - marker_top_left_y, 2))
                    mm2px_height = marker_height / float(self.marker_size)
                    marker_width = numpy.sqrt(numpy.power(marker_top_right_x - marker_top_left_x,2))
                    mm2px_width = marker_width / float(self.marker_size)

                    #Transform perspective according to QR code corner coordinates
                    pts1 = numpy.float32([
                        [marker_top_left_x,marker_top_left_y],
                        [marker_top_right_x,marker_top_right_y],
                        [marker_bottom_left_x,marker_bottom_left_y],
                        [marker_bottom_right_x,marker_bottom_right_y]
                    ])

                    pts2 = numpy.float32([[0,0],[marker_width,0],[0,marker_height],[marker_width,marker_height]])

                    M = cv2.getPerspectiveTransform(pts1,pts2)
                    self.current_frame = cv2.warpPerspective(self.current_frame,M,(frame_width/2,frame_height/2))


                    px_screen_height = (1 * mm2px_height) + (self.screen_height * (marker_width / self.screen_width))
                    
                    #cropping
                    pts3 = numpy.float32([
                        [0, marker_width + (1 * mm2px_height)], # marker has 1mm padding bottom
                        [marker_width,marker_height + (1 * mm2px_height)],
                        [0, marker_height + px_screen_height],
                        [marker_width,  marker_height + px_screen_height]
                    ])
 
                    pts4 = numpy.float32([[0,0],[marker_width,0],[0,self.screen_height * mm2px_height],[marker_width,self.screen_height * mm2px_height]])

                    M = cv2.getPerspectiveTransform(pts3,pts4)
                    self.current_frame = cv2.warpPerspective(self.current_frame,M,(int(marker_width),int(px_screen_height)))

                    # make frames uniform in size and undo initial resizing
                    #self.current_frame = cv2.resize(self.current_frame, (int(marker_width)*2, int(px_screen_height)*2))

                    out.write(self.current_frame)

                cv2.imshow('frame',self.current_frame)

                cv2.waitKey(100)

        out.release()
        cv2.destroyAllWindows()
        sys.exit(0)

grabber = ImageGrabber(0)
main = Main()
main2 = Main()
main3 = Main()

grabber.start()
main.start()
main2.start()
main3.start()

grabber.join()
main.join()
main2.join()
main3.join()
