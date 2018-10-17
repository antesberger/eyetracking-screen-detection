import cv2
import time
import threading
import Queue

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
        self.stream = cv2.VideoCapture("123.sdp")

    def run(self):
        global frames
        while True:
            # TODO: Skip frame for which decoding errors were thrown
            ret,frame = self.stream.read()
            
            if ret == True:
                frame = cv2.resize(frame, (960,540))
                frames.put(frame)
            else:
                print("couldn't capture frame")

            #time.sleep(0.025)

class Main(threading.Thread):
    def __init(self):
        threading.Thread.__init(self)

    def run(self):
        global frames
        cv2.useOptimized()
        while True:
            if(not frames.empty()):
                self.current_frame = frames.get()
                print(frames.qsize())
                self.last_processed_frame = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2GRAY) # aruco.detectMarkers() requires gray image
                markers = cv2.aruco.detectMarkers(self.last_processed_frame,dictionary)
                if len(markers[0]) > 0: 
                    self.last_processed_frame = cv2.aruco.drawDetectedMarkers(self.last_processed_frame,markers[0],markers[1])
                
                cv2.imshow('frame',self.last_processed_frame)

                if( cv2.waitKey(100) == 27 ):
                    break
                        
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


