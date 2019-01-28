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
    def __init__(self):
        threading.Thread.__init__(self)
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
                    timestamps.put((self.stream.get(cv2.CAP_PROP_POS_MSEC) * 10000000, str(datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f"))))
            except:
                recording_flag = False
                self.stream.release()
                print('Stream ended')
                break

class Main(threading.Thread):
    def __init__(self, participant):
        threading.Thread.__init__(self)
        self.participant = participant

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

        # variables for syncing between threads
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

        # phone and screen constants
        self.marker_size = 66 #rectangular (mm)
        self.secondary_marker_size = 20
        self.screen_height = 130 #mm
        self.screen_width = 66 #mm
        self.screen_pixel_height = 2880
        self.screen_pixel_width = 1440
        
        # precomputed calibration constants for the eyetracker
        self.dist = numpy.array([[0.05357947, -0.22872005, -0.00118557, -0.00126952, 0.2067489 ]])
        self.cameraMatrix = numpy.array([[1.12585498e+03, 0.00000000e+00, 9.34478069e+02], [0.00000000e+00, 1.10135217e+03, 5.84380561e+02], [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]])
        self.mtx = numpy.array([[1.12825274e+03, 0.00000000e+00, 9.35684715e+02], [0.00000000e+00, 1.10801151e+03, 5.86151765e+02], [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]])
        self.corner_refine_criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

        directory = './out/{0}-{1}/'.format(self.participant, datetime.datetime.now().strftime("%Y-%m-%d"))
        #directory = './out/2018-11-15-12-38/'
        videoFilename_processed = 'gaze_video_processed.avi'
        videoFilename_raw = 'gaze_video_raw.avi'
        fourcc = cv2.VideoWriter_fourcc('M','J','P','G')
        firstFrame = frames.get()
        inputHeight, inputWidth, c = firstFrame.shape
        out_processed = cv2.VideoWriter(directory + videoFilename_processed,fourcc, 25, (self.screen_pixel_width/outputQuality,self.screen_pixel_height/outputQuality))
        out_raw = cv2.VideoWriter(directory + videoFilename_raw,fourcc, 25, (inputWidth,inputHeight))
        cv2.useOptimized()

        # open log files
        computedFrames = open(directory + "/computed_frames.txt", "a+")
        log = open(directory + 'log.txt', 'a+')

        self.counter = 0 # used to execute functions only for every xth frame
        self.logcounter = 0
        while not (frames.qsize() == 0 and recording_flag == False):
            if(not frames.empty()):
                self.current_frame = frames.get()

                # tobii format,         yyyy-mm-dd-hh-mm-ss-ffffff
                self.current_timestamp, self.current_absolute_timestamp = timestamps.get()

                self.raw_frame = self.current_frame
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
                        # print('markers detected but the main one is not amongst them.')
                        logstr = str(self.current_absolute_timestamp) + "; " + str(self.success_frames) + ' / ' + str(self.processed_frames) + '; ' + str(self.error_frames) + ' errors' + '; ' + str((float(self.error_frames) / float(self.processed_frames)) * float(100)) + '%; (' + str(frames.qsize()) + ' buffered'
                        self.logcounter += 1
                        if self.logcounter > 20:
                            log.write(logstr)
                            self.logcounter = 0
                        print(logstr)

                        self.counter += 1
                        if self.counter > 200:
                            self.counter = 0
                            cv2.imshow('frame',self.raw_frame)
                            cv2.waitKey(100)
                        continue

                    term = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_COUNT, 30, 0.1)
                    corners_id0 = cv2.cornerSubPix(frame_gray, corners[id0], (5, 5), (-1, -1), term)
                    rvec, tvec, objPoints = cv2.aruco.estimatePoseSingleMarkers(corners_id0, self.marker_size, self.cameraMatrix, self.dist) #tvec is the translation vector of the markers center

                    # corner estimation based on single big marker on the top of the screen
                    screenCorners = numpy.float32([
                        [-self.marker_size/2, -self.marker_size/2 - 1, 0],
                        [self.marker_size/2, -self.marker_size/2 - 1, 0],
                        [-self.marker_size/2,-self.marker_size/2 - (self.screen_height + 15) - 1,0],
                        [self.marker_size/2,-self.marker_size/2 - (self.screen_height + 15) - 1,0]
                    ]).reshape(-1,3)
                    imgpts, jac = cv2.projectPoints(screenCorners, rvec, tvec, self.mtx, self.dist) #world coordinates to camera coordinates
                    #self.current_frame = cv2.aruco.drawAxis(self.current_frame, self.cameraMatrix, self.dist, rvec, tvec, 100)

                    screen_top_left = imgpts[0][0]
                    screen_top_right = imgpts[1][0]
                    screen_bottom_left = imgpts[2][0]
                    screen_bottom_right = imgpts[3][0]

                    id1 = None
                    id3 = None
                    
                    # check if secondary markers were detected
                    try:
                        id1 = ids.tolist().index([1])
                        secondary_id = id1
                    except:
                        logstr = str(self.current_absolute_timestamp) + "; marker 1 not detected"
                        log.write(logstr)
                        pass

                    try:
                        id3 = ids.tolist().index([3])
                        secondary_id = id3
                    except:
                        logstr = str(self.current_absolute_timestamp) + "; marker 3 not detected"
                        log.write(logstr)
                        pass
                    
                    # if one of them is detected: compute vector intersection
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

    	                # use coordinates themselves if all markers were detected
                        if id3 is not None:
                            screen_bottom_left = secondary_marker_top_left
                            screen_bottom_right = self.intersection(corners_id0[0][1],corners_id0[0][2],secondary_marker_top_left,secondary_marker_top_right) 
                        else:
                            screen_bottom_right = secondary_marker_top_right
                            screen_bottom_left = self.intersection(corners_id0[0][0],corners_id0[0][3],secondary_marker_top_right,secondary_marker_top_left) 
                                    
                        #self.current_frame = cv2.aruco.drawAxis(self.current_frame, self.cameraMatrix, self.dist, rvec, tvec, 100)

                    # self.drawCircle(self.current_frame, screen_top_left[0], screen_top_left[1])
                    # self.drawCircle(self.current_frame, screen_top_right[0], screen_top_right[1])
                    # self.drawCircle(self.current_frame, screen_bottom_left[0], screen_bottom_left[1])
                    # self.drawCircle(self.current_frame, screen_bottom_right[0], screen_bottom_right[1])

                    #Transform perspective according to QR code corner coordinates
                    pts1 = numpy.float32([screen_top_left, screen_top_right, screen_bottom_left, screen_bottom_right])
                    pts2 = numpy.float32([[0,0],[self.screen_pixel_width/outputQuality,0],[0,self.screen_pixel_height/outputQuality],[self.screen_pixel_width/outputQuality,self.screen_pixel_height/outputQuality]])
                    
                    M = cv2.getPerspectiveTransform(pts1,pts2)
                    self.current_frame = cv2.warpPerspective(
                        self.current_frame,
                        M,
                        (self.screen_pixel_width/outputQuality,
                        self.screen_pixel_height/outputQuality)
                    )
                    
                    trackingupdate.put((self.current_timestamp, self.current_absolute_timestamp, M))

                    computedFrames.write(
                        str(self.current_timestamp) + "; " + 
                        self.current_absolute_timestamp + "; " + 
                        str(screen_top_left) +  '; ' + 
                        str(screen_top_right) + '; ' + 
                        str(screen_bottom_right) +  '; ' + 
                        str(screen_bottom_left) + '; ' +
                        str(M) + "\n"
                    )

                    out_processed.write(self.current_frame)

                    frames.task_done()
                    timestamps.task_done()
                    trackingupdate.task_done()

                    self.success_frames += 1

                else:
                    #log frames without detected marker
                    log.write(str(self.current_absolute_timestamp) + "; no markers detected; " + str(self.current_timestamp) + '\n')

                    #command line feedback for success rate
                    self.error_frames +=1 
                
                out_raw.write(self.raw_frame)
                logstr = str(self.current_absolute_timestamp) + "; " + str(self.success_frames) + ' / ' + str(self.processed_frames) + '; ' + str(self.error_frames) + ' errors' + '; ' + str((float(self.error_frames) / float(self.processed_frames)) * float(100)) + '%; (' + str(frames.qsize()) + ' buffered'
                print(logstr)

                self.logcounter += 1
                if self.logcounter > 20:
                    log.write(logstr)
                    self.logcounter = 0
                                
                self.counter += 1
                if self.counter > 200:
                    self.counter = 0
                    cv2.imshow('frame', self.raw_frame)
                    cv2.waitKey(100)

        computedFrames.close()
        log.close()

        out_processed.release()
        out_raw.release()
        cv2.destroyAllWindows()
        sys.exit(0)

class trackingprocessor(threading.Thread):
    def __init__(self, participant):
        threading.Thread.__init__(self)
        self.participant = participant

    def run(self):
        global trackingupdate
        self.initial_timestamp = 0
        self.mtx_timestamp = 0
        self.mtx_absolute_timestamp = 0

        directory = './out/{0}-{1}/'.format(self.participant, datetime.datetime.now().strftime("%Y-%m-%d"))
        self.trackingdata = open(directory + '/eyetracking_data_raw.txt', 'r')
        self.mtx_timestamp, self.mtx_absolute_timestamp, self.gazeShiftMtx = trackingupdate.get()

        processeddata = open(directory + "/eyetracking_data_processed.txt", "a+")

        while True:
            try:
                line = self.trackingdata.readline()
                line = json.loads(line, strict=False)
                
                # skip the first data points which were recorded before the processing started
                if self.initial_timestamp == 0:
                    line = self.trackingdata.readline()
                    line = json.loads(line, strict=False)

                    rhour = int(line['ats'][11:13])
                    rmin = int(line['ats'][14:16])
                    rsec = int(line['ats'][17:19])
                    rmsec = int(line['ats'][20:-3])
                    rtotal = rmsec + (rsec * 1000) + (rmin * 1000 * 60) + (rhour * 60 * 60 * 1000)

                    phour = int(self.mtx_absolute_timestamp[11:13])
                    pmin = int(self.mtx_absolute_timestamp[14:16])
                    psec = int(self.mtx_absolute_timestamp[17:19])
                    pmsec = int(self.mtx_absolute_timestamp[20:-3])
                    ptotal = pmsec + (psec * 1000) + (pmin * 1000 * 60) + (phour * 60 * 60 * 1000)

                    if rtotal >= ptotal:
                        self.initial_timestamp = line['ts']

                    #print "syncing"
            
                else:
                    line['tts'] = line['ts']
                    line['ts'] = line['ts'] - self.initial_timestamp

                    if 'gp' in line:
                        while line['ts'] > self.mtx_timestamp:
                            self.mtx_timestamp, self.mtx_absolute_timestamp, self.gazeShiftMtx = trackingupdate.get()
                        
                        rawX = line['gp'][0]
                        rawY = line['gp'][1]

                        rawXpx = rawX * 960
                        rawYpx = rawY * 540

                        gp = numpy.array([[[rawXpx, rawYpx]]], dtype = "float32")
                        new_gp = cv2.perspectiveTransform(gp, self.gazeShiftMtx)
                        line['gp'][0] = int(new_gp[0][0][0])
                        line['gp'][1] = int(new_gp[0][0][1])

                        processeddata.write(json.dumps(line) + '\n')
            except:
                pass
              
try:
    participant = sys.argv[1]
except:
    print 'please provide the participants identification as an argument.'
    sys.exit(0)

grabber = ImageGrabber()
main = Main(participant)
# trackingprocessor = trackingprocessor(participant)

grabber.start()
main.start()
# trackingprocessor.start()

grabber.join()
main.join()
# trackingprocessor.join()
