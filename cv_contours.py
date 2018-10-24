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
        self.stream = cv2.VideoCapture("./markers/test15.mp4")

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
                #print(frames.qsize())
                frame_preprocessed = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2GRAY) # aruco.detectMarkers() requires gray image
                frame_preprocessed = cv2.bilateralFilter(frame_preprocessed, 11, 11, 17)
                frame_preprocessed = cv2.Canny(frame_preprocessed, 5, 200)
                #cv2.imshow('test', frame_preprocessed)
                
                _, contours, _= cv2.findContours(frame_preprocessed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                contours = [cnt for cnt in contours if len(cnt) >= 4]
                contours = sorted(contours, key = cv2.contourArea, reverse = True)[:10]
                cnt_candidates = []
                screenCnt = None

                for c in contours:
                    # approximate the contour
                    peri = cv2.arcLength(c, True)
                    approx = cv2.approxPolyDP(c, 0.002, True)

                    if True:
                        screenCnt = approx
                        cv2.drawContours(self.current_frame, [screenCnt], -1, (0, 255, 0), 3)
                        break


                # c = contours[0]
                # peri = cv2.arcLength(c, True)
                # approx = cv2.approxPolyDP(c, 0.02 * peri, True)          
                # screenCnt = contours[0]
                # cnt_candidates.append(approx)
                # cv2.drawContours(self.current_frame, [screenCnt], -1, (0, 255, 0), 3)

                print(c[0][0])
                cv2.imshow("Game Boy Screen", self.current_frame)
                
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
