import cv2
import json
import numpy as np
import time
import csv
import os
import sys
from datetime import datetime

dist = np.array([[0.05357947, -0.22872005, -0.00118557, -0.00126952, 0.2067489 ]])
cameraMatrix = np.array([[1.12585498e+03, 0.00000000e+00, 9.34478069e+02], [0.00000000e+00, 1.10135217e+03, 5.84380561e+02], [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]])
mtx = np.array([[1.12825274e+03, 0.00000000e+00, 9.35684715e+02], [0.00000000e+00, 1.10801151e+03, 5.86151765e+02], [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]])

if len(sys.argv) != 2:
    print "Please provide the directory name as an argument"
else:
    data = sys.argv[1]

#initialize files for readining
cap = cv2.VideoCapture('./data/eyetracking/' + data + '/gaze_video_processed.mov')
rawTrackingData = open('./data/eyetracking/' + data + '/eyetracking_data_raw.txt', 'r')
computedFrames = open('./data/eyetracking/' + data + '/computed_frames.txt', 'r')
dataLine = json.loads(rawTrackingData.readline())
frameLine = (computedFrames.readline() + computedFrames.readline() + computedFrames.readline()).split(';')

if not os.path.exists('./out/' + data):
    os.makedirs('./out/' + data)

with open('./out/' + data + '/eyetracking.csv', mode='w') as eyetracking:
    eyetracking_writer = csv.writer(eyetracking, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    eyetracking_writer.writerow(['Timestamp', 'x', 'y'])

#read first frame
ret, frame = cap.read()
cv2.imshow('frame',frame)

#initialize video output
fourcc = cv2.VideoWriter_fourcc('M','J','P','G')
inputWidth, inputHeight, c = frame.shape
out = cv2.VideoWriter('./out/' + data + '/gazeVideo.avi',fourcc, 25, (inputHeight,inputWidth))

#syncing: Skip first data frames that were recorded before the frist frame was processed
dataTs = datetime.strptime(dataLine['ats'], "%Y-%m-%d-%H-%M-%S-%f")
frameTs = datetime.strptime(frameLine[1], " %Y-%m-%d-%H-%M-%S-%f")
while frameTs > dataTs:
    dataLine = rawTrackingData.readline()
    dataLine = json.loads(dataLine)
    dataTs = datetime.strptime(dataLine['ats'], "%Y-%m-%d-%H-%M-%S-%f")

#initialize first transformation matrix
frameMtx = frameLine[6]
for char in ["[","]","\n","\r"]:
    frameMtx = frameMtx.replace(char,"")

frameMtx = np.asarray(frameMtx.replace("  ", " ").split(" ")[1:], dtype=np.float32)
frameMtx.shape = (3,3)

#loop through all frames
while cap.isOpened():

    dataLine = rawTrackingData.readline()
    dataLine = json.loads(dataLine)

    #print str(frameTs) + " < " + str(dataTs)
    if 'gp' in dataLine:
        dataTs = datetime.strptime(dataLine['ats'], "%Y-%m-%d-%H-%M-%S-%f")
        frameTs = datetime.strptime(frameLine[1], " %Y-%m-%d-%H-%M-%S-%f")

        #there are more data entries than processed frames -> sync their timestamps
        if dataTs > frameTs:

            #preparing mtx (str to np.array)
            frameMtx = frameLine[6]
            for char in ["[","]","\n","\r"]:
                frameMtx = frameMtx.replace(char,"")

            frameMtx = np.asarray(frameMtx.replace("  ", " ").split(" ")[1:], dtype=np.float32)
            frameMtx.shape = (3,3)

            ret, frame = cap.read()

            #break condition
            if not ret:
                break

            frameLine = (computedFrames.readline() + computedFrames.readline() + computedFrames.readline()).split(';')
            frameTs = datetime.strptime(frameLine[1], " %Y-%m-%d-%H-%M-%S-%f")

        #transforming gazepoint
        rawX = dataLine['gp'][0]
        rawY = dataLine['gp'][1]

        rawXpx = rawX * 960
        rawYpx = rawY * 540

        gp = np.array([[[rawXpx, rawYpx]]], dtype = "float32")
        #gpDist = cv2.undistortPoints(gp, cameraMatrix, dist) #needed?
        #gp[0][0][0] -=  gpDist[0][0][0]
        #gp[0][0][1] -=  gpDist[0][0][1]
        transformedGp = cv2.perspectiveTransform(gp, frameMtx)[0][0]

        cv2.circle(frame, (transformedGp[0],transformedGp[1]), 5, (0,0,255), -1)

        with open('./out/' + data + '/eyetracking.csv', mode='a') as eyetracking:
            eyetracking_writer = csv.writer(eyetracking, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            eyetracking_writer.writerow([dataTs,transformedGp[0] * 2,transformedGp[1] * 2])

        # Display the resulting frame
        out.write(frame)
        #cv2.imshow('frame',frame)
        #if cv2.waitKey(1) & 0xFF == ord('q'):
        #    break

# When everything done, release the capture
out.release()
cap.release()
cv2.destroyAllWindows()
