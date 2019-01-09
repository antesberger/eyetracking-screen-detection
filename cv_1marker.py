import cv2
import time
import threading
import Queue
import numpy
from numpy import array
import sys
import datetime
import json

dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
frames = Queue.Queue()
timestamps = Queue.Queue()
trackingupdate = Queue.Queue()
frame_width = 0
frame_height = 0
recording_flag = True
quality = 2 # size of the input video. 1 == 1920*1080
outputQuality = 2 # size of the cropped output avi file. 1 == nexus5 screen size (1080*1920), 2 == 1/2 ... 

class ImageGrabber(threading.Thread):
    def __init__(self, ID):
        threading.Thread.__init__(self)
        self.ID=ID
        self.stream = cv2.VideoCapture("config.sdp")
        #self.stream = cv2.VideoCapture("./markers/test18.mp4")

    def run(self):
        global frames
        global frame_width
        global frame_height
        global recording_flag 
        global quality
        
        frame_width = int(self.stream.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(self.stream.get(cv2.CAP_PROP_FRAME_HEIGHT))

        while True:
            try:
                ret,frame = self.stream.read()
                if ret == True:
                    frame = cv2.resize(frame, (frame_width/quality,frame_height/quality))
                    frames.put(frame)
                    timestamps.put(self.stream.get(cv2.CAP_PROP_POS_MSEC) * 1000000)
            except:
                recording_flag = False
                self.stream.release()
                print('Stream ended')
                break

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
        global timestamps
        global frame_width
        global frame_height
        global trackingupdate
        global quality
        global outputQuality # of the cropped video

        self.processed_frames = 0
        self.success_frames = 0
        self.error_frames = 0

        self.marker_size = 66 #rectangular (mm)
        self.secondary_marker_size = 20
        self.screen_height = 130 #mm
        self.screen_width = 66 #mm
        self.screen_pixel_height = 2880
        self.screen_pixel_width = 1440
        
        self.dist = numpy.array([[0.05357947, -0.22872005, -0.00118557, -0.00126952, 0.2067489 ]])
        self.cameraMatrix = numpy.array([[1.12585498e+03, 0.00000000e+00, 9.34478069e+02], [0.00000000e+00, 1.10135217e+03, 5.84380561e+02], [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]])
        self.mtx = numpy.array([[1.12825274e+03, 0.00000000e+00, 9.35684715e+02], [0.00000000e+00, 1.10801151e+03, 5.86151765e+02], [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]])
        self.corner_refine_criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

        directory = './out/{0}/'.format(datetime.datetime.now().strftime("%Y-%m-%d-%H-%M"))
        #directory = './out/2018-11-15-12-38/'
        videoFilename_processed = 'gaze_video_processed.avi'
        videoFilename_raw = 'gaze_video_raw.avi'
        fourcc = cv2.VideoWriter_fourcc('M','J','P','G')
        firstFrame = frames.get()
        inputHeight, inputWidth, c = firstFrame.shape
        out_processed = cv2.VideoWriter(directory + videoFilename_processed,fourcc, 25, (self.screen_pixel_width/outputQuality,self.screen_pixel_height/outputQuality))
        out_raw = cv2.VideoWriter(directory + videoFilename_raw,fourcc, 25, (inputWidth,inputHeight))
        cv2.useOptimized()

        while not (frames.qsize() == 0 and recording_flag == False):
            if(not frames.empty()):
                self.current_frame = frames.get()
                self.current_timestamp = timestamps.get()

                out_raw.write(self.current_frame)
                self.current_frame = cv2.undistort(self.current_frame, self.mtx, self.dist, None, self.cameraMatrix)
                frame_gray = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2GRAY) # aruco.detectMarkers() requires gray image
                markers = cv2.aruco.detectMarkers(frame_gray,dictionary)

                self.processed_frames += 1
                if len(markers[0]) > 0:

                    # array order of corners is clockwise
                    corners, ids, rejectedImgPoints = markers

                    # get index of marker with id == 0
                    # bottom left == id1, bottom right = id3
                    try:
                        id0 = ids.tolist().index([0])
                    except:
                        # No marker with id == 0 detected
                        self.error_frames += 1
                        print('markers detected but the main one is not amongst them.')
                        print(str(self.success_frames) + ' / ' + str(self.processed_frames) + ' -> ' + str(self.error_frames) + ' errors' + ' (' + str((float(self.error_frames) / float(self.processed_frames)) * float(100)) + '%), (' + str(frames.qsize()) + ' buffered)')
                        #cv2.imshow('frame',self.current_frame)
                        #cv2.waitKey(100)
                        continue

                    term = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_COUNT, 30, 0.1)
                    corners_id0 = cv2.cornerSubPix(frame_gray, corners[id0], (5, 5), (-1, -1), term)
                    rvec, tvec, objPoints = cv2.aruco.estimatePoseSingleMarkers(corners_id0, self.marker_size, self.cameraMatrix, self.dist) #tvec is the translation vector of the markers center

                    screenCorners = numpy.float32([
                        [-self.marker_size/2, -self.marker_size/2 - 1, 0],
                        [self.marker_size/2, -self.marker_size/2 - 1, 0],
                        [-self.marker_size/2,-self.marker_size/2 - (self.screen_height + 20) - 1,0], #todo
                        [self.marker_size/2,-self.marker_size/2 - (self.screen_height + 20) - 1,0] #tofdo
                    ]).reshape(-1,3)
                    imgpts, jac = cv2.projectPoints(screenCorners, rvec, tvec, self.mtx, self.dist) #world coordinates to camera coordinates
                    self.current_frame = cv2.aruco.drawAxis(self.current_frame, self.cameraMatrix, self.dist, rvec, tvec, 100)

                    screen_top_left = imgpts[0][0]
                    screen_top_right = imgpts[1][0]
                    screen_bottom_left = imgpts[2][0]
                    screen_bottom_right = imgpts[3][0]

                    id1 = None
                    id3 = None
                    
                    try:
                        id1 = ids.tolist().index([1])
                        secondary_id = id1
                    except:
                        pass

                    try:
                        id3 = ids.tolist().index([3])
                        secondary_id = id3
                    except:
                        pass
                    
                    if id1 or id3 is not None:
                        corners_secondary = cv2.cornerSubPix(frame_gray, corners[secondary_id], (5, 5), (-1, -1), term)
                        rvec, tvec, objPoints = cv2.aruco.estimatePoseSingleMarkers(corners_secondary, self.secondary_marker_size, self.cameraMatrix, self.dist)

                        screenCorners = numpy.float32([ # bottom markers are upsidedown
                            [self.secondary_marker_size/2, -self.secondary_marker_size/2 - 1, 0],
                            [-self.secondary_marker_size/2, -self.secondary_marker_size/2 - 1, 0]
                        ]).reshape(-1,3) 
                        imgpts, jac = cv2.projectPoints(screenCorners, rvec, tvec, self.mtx, self.dist) #world coordinates to camera coordinates

                        secondary_marker_top_left = imgpts[0][0]
                        secondary_marker_top_right = imgpts[1][0]

                        if id3 is not None:
                            screen_bottom_left = secondary_marker_top_left
                            screen_bottom_right = self.intersection(corners_id0[0][1],corners_id0[0][2],secondary_marker_top_left,secondary_marker_top_right) 
                        else:
                            screen_bottom_right = secondary_marker_top_right
                            screen_bottom_left = self.intersection(corners_id0[0][0],corners_id0[0][3],secondary_marker_top_right,secondary_marker_top_left) 
                                    
                        self.current_frame = cv2.aruco.drawAxis(self.current_frame, self.cameraMatrix, self.dist, rvec, tvec, 100)

                    # self.drawCircle(self.current_frame, screen_top_left[0], screen_top_left[1])
                    # self.drawCircle(self.current_frame, screen_top_right[0], screen_top_right[1])
                    # self.drawCircle(self.current_frame, screen_bottom_left[0], screen_bottom_left[1])
                    # self.drawCircle(self.current_frame, screen_bottom_right[0], screen_bottom_right[1])

                    #Transform perspective according to QR code corner coordinates
                    pts1 = numpy.float32([screen_top_left, screen_top_right, screen_bottom_left, screen_bottom_right])
                    pts2 = numpy.float32([[0,0],[self.screen_pixel_width/outputQuality,0],[0,self.screen_pixel_height/outputQuality],[self.screen_pixel_width/outputQuality,self.screen_pixel_height/outputQuality]])

                    M = cv2.getPerspectiveTransform(pts1,pts2)
                    self.current_frame = cv2.warpPerspective(self.current_frame,M,(self.screen_pixel_width/outputQuality,self.screen_pixel_height/outputQuality))
                    
                    trackingupdate.put((self.current_timestamp, M))
                    out_processed.write(self.current_frame)
                    frames.task_done()
                    timestamps.task_done()

                    self.success_frames += 1

                else:
                    #log frames without detected marker
                    errorlog = open(directory + 'log.txt', 'a+')
                    errorlog.write('no markers detected at ts: ' + str(self.current_timestamp) + '\n')
                    errorlog.close()

                    #command line feedback for success rate
                    self.error_frames +=1 
                    
                print(str(self.success_frames) + ' / ' + str(self.processed_frames) + ' -> ' + str(self.error_frames) + ' errors' + ' (' + str((float(self.error_frames) / float(self.processed_frames)) * float(100)) + '%), (' + str(frames.qsize()) + ' buffered)')
                #cv2.imshow('frame',self.current_frame)
                #cv2.waitKey(100)

        out_processed.release()
        out_raw.release()
        cv2.destroyAllWindows()
        sys.exit(0)

class trackingprocessor(threading.Thread):
    def __init(self):
        threading.Thread.__init(self)
    def run(self):
        global trackingupdate
        self.initial_timestamp = 0
        self.currentNewTs = 0
        self.currentNewTs_relative = 0

        directory = './out/{0}'.format(datetime.datetime.now().strftime("%Y-%m-%d-%H-%M"))
        open(directory + '/eyetracking_data_raw.txt', 'a').close() #initialize file because this would normally be created later by eyetracking.py
        self.trackingdata = open(directory + '/eyetracking_data_raw.txt', 'r+')
        self.processeddata = open(directory + "/eyetracking_data_processed.txt", "a+")
        while not (trackingupdate.empty() and recording_flag == False):
            current_timestamp, gazeShiftMtx = trackingupdate.get()

            while self.initial_timestamp == 0 or line['ts'] <= current_timestamp:
                line = self.trackingdata.readline()
                line = json.loads(line)

                if self.initial_timestamp == 0:
                    self.initial_timestamp = line['ts']

                line['ts'] = line['ts'] - self.initial_timestamp
                #print(str(line['ts']) + ' < ' + str(current_timestamp))

                if 'gp' in line:
                    gp = numpy.array([[line['gp']]], dtype = "float32")
                    new_gp = cv2.perspectiveTransform(gp, gazeShiftMtx)
                    line['ts'] = self.currentNewTs_relative

                self.processeddata.write(json.dumps(line) + '\n')

grabber = ImageGrabber(0)
main = Main()
#main2 = Main()
trackingprocessor = trackingprocessor()

grabber.start()
main.start()
#main2.start()
trackingprocessor.start()

grabber.join()
main.join()
#main2.join()
trackingprocessor.join()
