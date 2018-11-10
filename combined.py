import cv2
import time
import threading
import Queue
import numpy
from numpy import array
import sys
import datetime
import random

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
        
        filename = './out/{0}/video.avi'.format(datetime.datetime.now().strftime("%Y-%m-%d-%M"))
        out = cv2.VideoWriter(filename,cv2.VideoWriter_fourcc('M','J','P','G'), 25, (620,1100))

        cv2.useOptimized()

        while not (frames.qsize() == 0 and recording_flag == False):
            if(not frames.empty()):
                self.current_frame = frames.get()
                frame_gray = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2GRAY) # aruco.detectMarkers() requires gray image
                frame_preprocessed = cv2.bilateralFilter(frame_gray, 11, 11, 17)
                frame_preprocessed = cv2.Canny(frame_preprocessed, 5, 200)
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
                    term = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_COUNT, 0, 0.1)
                    corners[id0] = cv2.cornerSubPix(frame_gray, corners[id0], (5, 5), (-1, -1), term)

                    marker_top_left_x = int(corners[id0][0][0][0])
                    marker_top_left_y = int(corners[id0][0][0][1])
                    marker_top_right_x = int(corners[id0][0][1][0])
                    marker_top_right_y = int(corners[id0][0][1][1])
                    marker_bottom_left_x = int(corners[id0][0][3][0])
                    marker_bottom_left_y = int(corners[id0][0][3][1])
                    marker_bottom_right_x = int(corners[id0][0][2][0])
                    marker_bottom_right_y = int(corners[id0][0][2][1])

                    #self.drawCircle(self.current_frame, marker_bottom_left_x, marker_bottom_left_y)
                    #self.drawCircle(self.current_frame, marker_bottom_right_x, marker_bottom_right_y)

                    _, contours, _= cv2.findContours(frame_preprocessed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    contours = [cnt for cnt in contours if len(cnt) >= 4]
                    contours = sorted(contours, key = cv2.contourArea, reverse = True)[:10]
                    cnt_candidates = []
                    screenCnt = None
                
                    for c in contours:
                        # approximate the contour
                        peri = cv2.arcLength(c, True)
                        approx = cv2.approxPolyDP(c, 0.002 * peri, True)
                        #print(approx)
                        tolerance = 10
                        contains_fist_corner = False
                        contains_second_corner = False

                        for corner in c:
                            if corner[0][0] > marker_bottom_left_x - tolerance and corner[0][0] < marker_bottom_left_x + tolerance and corner[0][0] > marker_bottom_left_y - tolerance and corner[0][1] < marker_bottom_left_y + tolerance:
                                contains_first_corner = True
                                break

                        if contains_first_corner:
                            for corner in c:
                                if corner[0][0] > marker_bottom_right_x - tolerance and corner[0][0] < marker_bottom_right_x + tolerance and corner[0][0] > marker_bottom_right_y - tolerance and corner[0][1] < marker_bottom_right_y + tolerance:
                                    print('candidate found')
                                    contains_second_corner = True
                                    break
                        
                        if contains_first_corner and contains_second_corner:
                            screenCnt = approx
                            cv2.drawContours(self.current_frame, [screenCnt], -1, (random.randint(0,255), random.randint(0,255), random.randint(0,255)), 3)
                            break


                    # cnt_candidates = [c for corner in c if corner[0][0] > marker_bottom_left_x - tolerance and corner[0][0] < marker_bottom_left_x + tolerance and corner[0][0] > marker_bottom_left_y - tolerance and corner[0][1] < marker_bottom_left_y + tolerance]
                    #print(len(cnt_candidates))
                    #if [marker_bottom_left_x, marker_bottom_left_y] in approx:
                    #    print('test')
                    #for corner in approx:
                        #if corner[0][0] > marker_bottom_left_x - tolerance and corner[0][0] < marker_bottom_left_x + tolerance and corner[0][0] > marker_bottom_left_y - tolerance and corner[0][1] < marker_bottom_left_y + tolerance:
                        #[[[527  43]] [[528  43]]]
                            #print(corner[0][0])
                                # screenCnt = approx
                                # cv2.drawContours(self.current_frame, [screenCnt], -1, (random.randint(0,255), random.randint(0,255), random.randint(0,255)), 3)
                                # break

                cv2.imshow("Screen", self.current_frame)
                
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
