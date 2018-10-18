import cv2
import time
import threading
import Queue
import numpy

#gst-launch udpsrc caps="application/x-rtp,payload=127" port=5000 ! rtph264depay ! capsfilter caps="video/x-h264,width=1920,height=1080" ! ffdec_h264 ! autovideosink
#gst-launch udpsrc caps="application/x-rtp,payload=127" port=5000 ! rtph264depay ! ffdec_h264 ! autovideosink
#"udpsrc caps=application/x-rtp,payload=127 port=5000 ! rtph264depay ! ffdec_h264 ! appsink name=opencvsink"

dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
frames = Queue.Queue()
# last_processed_frame = None

# if(cap.isOpened()==False):
#     print "false"
# else:
#     print "open"

# def processFrame(frame):
#     frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) # aruco.detectMarkers() requires gray image
#     markers = cv2.aruco.detectMarkers(frame_gray,dictionary)
#     # corners, ids, rejectedImgPoints = markers
#     # #cv2.aruco.refineDetectedMarkers(frame_gray, board, corners, ids, rejectedImgPoints)

#     if len(markers[0]) > 0:
#         print("marker detected")
#         marker_image = cv2.aruco.drawDetectedMarkers(frame_gray,markers[0],markers[1])
#     else:
#         print("no markers in frame")

#     last_processed_frame = frame_gray
#     return frame_gray

class ImageGrabber(threading.Thread):
    def __init__(self, ID):
        threading.Thread.__init__(self)
        self.ID=ID
        # self.stream = cv2.VideoCapture("123.sdp")
        self.stream = cv2.VideoCapture("./markers/test12.mp4")

    def run(self):
        global frames
        while True:
            # TODO: Skip frame for which decoding errors were thrown
            try:
                ret,frame = self.stream.read()
            except:
                print('error readind frame')

            if ret == True:
                frame = cv2.resize(frame, (int(self.stream.get(cv2.CAP_PROP_FRAME_WIDTH)/2),int(self.stream.get(cv2.CAP_PROP_FRAME_HEIGHT)/2)))
                frames.put(frame)
            else:
                print("couldn't capture frame")
                return

            #time.sleep(0.025)

class Main(threading.Thread):
    def __init(self):
        threading.Thread.__init(self)

    def run(self):
        global frames
        self.marker_size = 62 #rectangular (mm)
        self.screen_height = 110 #mm
        self.screen_width = 62 #mm

        cv2.useOptimized()
        while True:
            if(not frames.empty()):
                self.current_frame = frames.get()
                #print(frames.qsize())
                self.last_processed_frame = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2GRAY) # aruco.detectMarkers() requires gray image
                markers = cv2.aruco.detectMarkers(self.last_processed_frame,dictionary)
                
                if len(markers[0]) > 0:
                    corners, ids, rejectedImgPoints = markers

                    #example marker corners
                    # [[ 194.  155.]
                    #  [ 267.  159.]
                    #  [ 265.  234.]
                    #  [ 192.  230.]]

                    #bottom_left corner of marker with id==0
                    id0 = ids.tolist().index([0])
                    marker_top_left_x = int(corners[id0][0][0][0])
                    marker_top_left_y = int(corners[id0][0][0][1])
                    marker_bottom_left_x = int(corners[id0][0][3][0])
                    marker_bottom_left_y = int(corners[id0][0][3][1])
                    marker_bottom_right_x = int(corners[id0][0][2][0])
                    marker_bottom_right_y = int(corners[id0][0][2][1])

                    #estimate 1mm = ?px
                    marker_height = marker_bottom_left_y - marker_top_left_y
                    mm2px_height = float(marker_height) / float(self.marker_size)
                    marker_width = marker_bottom_right_x - marker_bottom_left_x
                    mm2px_width = float(marker_width) / float(self.marker_size)

                    #estimate screens angle along the x/y axis
                    px_screen_height = int(float(self.screen_height) * mm2px_height)
                    angle_y = (float(marker_bottom_left_x) - float(marker_top_left_x)) / float(marker_height)
                    px_screen_width = int(float(self.screen_width) * mm2px_width)
                    angle_x = (float(marker_bottom_right_y) - float(marker_bottom_left_y)) / float(marker_width)

                    #estimate screen corner coordinates
                    screen_top_left_x = marker_bottom_left_x
                    screen_top_left_y = int(float(marker_bottom_left_y) + (1 * mm2px_height)) # marker has 1mm margin bottom
                    screen_bottom_left_y = screen_top_left_y + px_screen_height
                    screen_bottom_left_x = int(screen_top_left_x + (px_screen_height * angle_y))
                    screen_top_right_x = screen_top_left_x + px_screen_width
                    screen_top_right_y = int(screen_top_left_y + (px_screen_width * angle_x))
                    screen_bottom_right_y = screen_bottom_left_y + (screen_top_right_y - screen_top_left_y)
                    screen_bottom_right_x = screen_top_right_x + (screen_bottom_left_x - screen_top_left_x)

                    #draw screen estimates
                    cv2.circle(
                        self.last_processed_frame, 
                        (screen_top_left_x,screen_top_left_y), #center
                        5, #radius
                        (255,0,0), 
                        thickness=1, 
                        lineType=8, 
                        shift=0
                    )

                    cv2.circle(
                        self.last_processed_frame, 
                        (screen_bottom_left_x,screen_bottom_left_y), #center
                        5, #radius
                        (255,0,0), 
                        thickness=1, 
                        lineType=8, 
                        shift=0
                    )

                    cv2.circle(
                        self.last_processed_frame, 
                        (screen_top_right_x,screen_top_right_y), #center
                        5, #radius
                        (255,0,0), 
                        thickness=1, 
                        lineType=8, 
                        shift=0
                    )

                    cv2.circle(
                        self.last_processed_frame, 
                        (screen_bottom_right_x,screen_bottom_right_y), #center
                        5, #radius
                        (255,0,0), 
                        thickness=1, 
                        lineType=8, 
                        shift=0
                    )

                    #Transform perspective and crop image
                    pts1 = numpy.float32([
                        [screen_top_left_x,screen_top_left_y],
                        [screen_top_right_x,screen_top_right_y],
                        [screen_bottom_left_x,screen_bottom_left_y],
                        [screen_bottom_right_x,screen_bottom_right_y]
                    ])

                    pts2 = numpy.float32([[0,0],[px_screen_width * 2,0],[0,px_screen_height * 2],[px_screen_width * 2,px_screen_height * 2]])

                    M = cv2.getPerspectiveTransform(pts1,pts2)
                    self.last_processed_frame = cv2.warpPerspective(self.last_processed_frame,M,(px_screen_width * 2,px_screen_height * 2))
                                    
                cv2.imshow('frame',self.last_processed_frame)
                cv2.waitKey(100)
                # if( cv2.waitKey(100) == 27 ):
                #     breakc
                        
grabber = ImageGrabber(0)
main = Main()
#main2 = Main()
#main3 = Main()

grabber.start()
main.start()
#main2.start()
#main3.start()

grabber.join()
main.join()
#main2.join()
#main3.join()

# i = 0
# while(True):
#     threading.Timer(0, read_stream).start()
#     threading.Timer(0, test).start()

    # if i < 100:
    #     i = i + 1
    #     print i
    #     ret, frame = cap.read()
    #     frame_buffer.insert(len(frame_buffer),frame)

    # else:
    #     # if thread count < x
    #     print(len(frame_buffer))
    #     last_processed_frame = processFrame(frame_buffer[0])
    #     frame_buffer.pop(0)
        
    #     cv2.imshow('frame',last_processed_frame)

    #     if( cv2.waitKey(100) == 27 ):
    #         break


