import cv2
import time
import threading
import Queue
import numpy
from numpy import array
import sys
import datetime

#gst-launch udpsrc caps="application/x-rtp,payload=127" port=5000 ! rtph264depay ! capsfilter caps="video/x-h264,width=1920,height=1080" ! ffdec_h264 ! autovideosink
#gst-launch udpsrc caps="application/x-rtp,payload=127" port=5000 ! rtph264depay ! ffdec_h264 ! autovideosink
#"udpsrc caps=application/x-rtp,payload=127 port=5000 ! rtph264depay ! ffdec_h264 ! appsink name=opencvsink"

dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
frames = Queue.Queue()
frame_width = 0
frame_height = 0
recording_flag = True

class ImageGrabber(threading.Thread):
    def __init__(self, ID):
        threading.Thread.__init__(self)
        self.ID=ID
        #self.stream = cv2.VideoCapture("config.sdp")
        self.stream = cv2.VideoCapture("./markers/test14.mp4")

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
            print(self.stream.get(cv2.CAP_PROP_POS_MSEC))
            if ret == True:
                frame = cv2.resize(frame, (frame_width/4,frame_height/4))
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

    def drawCircle(self,img,(x,y)):
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
    
    # origin o to desitnation d
    def intersection(self, p1, p2, p3, p4):
        a1 = array([p1[0], p1[1]])
        a2 = array([p2[0], p2[1]])
        b1 = array([p3[0], p3[1]])
        b2 = array([p4[0], p4[1]])

        da = a2-a1
        db = b2-b1
        dp = a1-b1

        dap = array( [0.0, 0.0] )
        dap[0] = -da[1]
        dap[1] = da[0]

        denom = numpy.dot( dap, db)
        num = numpy.dot( dap, dp )
        return (num / denom.astype(float))*db + b1

    def run(self):
        global frames
        global frame_width
        global frame_height
        global recording_flag

        self.marker_size = 62 #rectangular (mm)
        self.screen_height = 110 #mm
        self.screen_width = 62 #mm
        
        self.corner_refine_criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)


        filename = './out/output_{0}.avi'.format(datetime.datetime.now().strftime("%Y-%m-%d-%M"))
        out = cv2.VideoWriter(filename,cv2.VideoWriter_fourcc('M','J','P','G'), 25, (620,1100))

        cv2.useOptimized()

        while not (frames.qsize() == 0 and recording_flag == False):
            if(not frames.empty()):
                self.current_frame = frames.get()
                #print(cv2.CAP_PROP_POS_MSEC)
                #print(frames.qsize())
                frame_gray = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2GRAY) # aruco.detectMarkers() requires gray image
                markers = cv2.aruco.detectMarkers(frame_gray,dictionary)

                if len(markers[0]) > 0:

                    # array order of corners is clockwise
                    corners, ids, rejectedImgPoints = markers

                    #get index of marker with id == 0
                    try:
                        id0 = ids.tolist().index([0])
                        id1 = ids.tolist().index([1])
                    except:
                        print("Could not detect both makers")
                        continue

                    #corners = array(corners)
                    term = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_COUNT, 30, 0.1)
                    corners[id0] = cv2.cornerSubPix(frame_gray, corners[id0], (5, 5), (-1, -1), term)
                    corners[id1] = cv2.cornerSubPix(frame_gray, corners[id1], (5, 5), (-1, -1), term)

                    marker0_top_left = (int(corners[id0][0][0][0]),int(corners[id0][0][0][1]))
                    marker0_top_right = (int(corners[id0][0][1][0]), int(corners[id0][0][1][1]))
                    marker0_bottom_left = (int(corners[id0][0][3][0]),int(corners[id0][0][3][1]))
                    marker0_bottom_right = (int(corners[id0][0][2][0]),int(corners[id0][0][2][1]))

                    marker1 = [
                        (int(corners[id1][0][0][0]),int(corners[id1][0][0][1])),
                        (int(corners[id1][0][1][0]),int(corners[id1][0][1][1])),
                        (int(corners[id1][0][3][0]),int(corners[id1][0][3][1])),
                        (int(corners[id1][0][2][0]),int(corners[id1][0][2][1]))
                    ]
                    
                    # cover left/right handed case -> marker positioned left/right of phone + rotation
                    if marker1[0][1] > marker1[3][1]:
                        marker1_top_left = marker1[3]
                        marker1_top_right = marker1[2]
                        marker1_bottom_left = marker1[0]
                        marker1_bottom_right = marker1[1]
                    else:
                        marker1_top_left = marker1[0]
                        marker1_top_right = marker1[1]
                        marker1_bottom_left = marker1[2]
                        marker1_bottom_right = marker1[3]
                    
                    #estimate 1mm = ?px
                    marker0_height = numpy.sqrt(numpy.power(marker0_bottom_left[1] - marker0_top_left[1], 2))
                    mm2px_height = marker0_height / float(self.marker_size)

                    #screen coordinates
                    intersection = self.intersection(marker0_top_right,marker0_bottom_right,marker1_top_left,marker1_top_right)

                    # TODO: mm2px_height computation is not accurate
                    # TODO: compute mm2px_height separately for bottom marker
                    screen_top_left = (int(marker0_bottom_left[0] + (1 * mm2px_height)), int((marker0_bottom_left[1] + (1 * mm2px_height))))
                    screen_top_right = (int(marker0_bottom_right[0] + (1 * mm2px_height)), int((marker0_bottom_right[1] + (1 * mm2px_height))))
                    screen_bottom_left = (int(marker1_top_right[0] + (1 * mm2px_height)), int(marker1_top_right[1] - (1 * mm2px_height)))
                    screen_bottom_right = (int(intersection[0]), (int(intersection[1])))

                    self.drawCircle(self.current_frame, marker0_bottom_right)
                    self.drawCircle(self.current_frame, marker0_top_right)
                    self.drawCircle(self.current_frame, marker1_top_left)
                    self.drawCircle(self.current_frame, marker1_top_right)
                    
                    self.drawCircle(self.current_frame, (int(intersection[0]),int(intersection[1])))

                    #Transform perspective according to QR code corner coordinates
                    pts1 = numpy.float32([
                        [screen_top_left[0],screen_top_left[1]],
                        [screen_top_right[0],screen_top_right[1]],
                        [screen_bottom_left[0],screen_bottom_left[1]],
                        [screen_bottom_right[0],screen_bottom_right[1]]
                    ])

                    pts2 = numpy.float32([[0,0],[self.screen_width*3,0],[0,self.screen_height*3],[self.screen_width*3,self.screen_height*3]])

                    M = cv2.getPerspectiveTransform(pts1,pts2)
                    self.current_frame = cv2.warpPerspective(self.current_frame,M,(self.screen_width*3,self.screen_height*3))
                    
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
