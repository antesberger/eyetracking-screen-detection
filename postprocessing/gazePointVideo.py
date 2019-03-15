import cv2
import json
import numpy as np
import time
import csv
import os
import sys
import math
from datetime import datetime
import configparser
import matplotlib.pyplot as plt

dist = np.array([[0.05357947, -0.22872005, -0.00118557, -0.00126952, 0.2067489 ]])
cameraMatrix = np.array([[1.12585498e+03, 0.00000000e+00, 9.34478069e+02], [0.00000000e+00, 1.10135217e+03, 5.84380561e+02], [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]])
mtx = np.array([[1.12825274e+03, 0.00000000e+00, 9.35684715e+02], [0.00000000e+00, 1.10801151e+03, 5.86151765e+02], [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]])

if len(sys.argv) != 2:
    print "Please provide the directory name as an argument"
else:
    data = sys.argv[1]

#read config params
config = configparser.ConfigParser()
config.read('../config.ini')
screenHeightMM = int(config['DEFAULT']['screenHeightMM'])
screenWidthMM = int(config['DEFAULT']['screenWidthMM'])
screenHeightPX = int(config['DEFAULT']['screenHeightPX'])
screenWidthPX = int(config['DEFAULT']['screenWidthPX'])
saccadeThreshold = int(config['DEFAULT']['saccadeThreshold'])
eyetrackerResHeight = int(config['DEFAULT']['eyetrackerResHeight'])
eyetrackerResWidth = int(config['DEFAULT']['eyetrackerResWidth'])
eyetrackerVideoQuality = int(config['DEFAULT']['eyetrackerVideoQuality'])
outVideoQuality = int(config['DEFAULT']['outVideoQuality'])

#initialize files for readining
cap = cv2.VideoCapture(data + '/gaze_video_processed.mov')
rawTrackingData = open(data + '/eyetracking_data_raw.txt', 'r')
computedFrames = open(data + '/computed_frames.txt', 'r')
dataLine = json.loads(rawTrackingData.readline())
frameLine = (computedFrames.readline() + computedFrames.readline() + computedFrames.readline()).split(';')

if not os.path.exists(data + '/out/'):
    os.makedirs(data + '/out/')

with open(data + '/out/eyetracking.csv', mode='w') as eyetracking:
    eyetracking_writer = csv.writer(eyetracking, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    eyetracking_writer.writerow(['Timestamp', 'x (px)', 'y (px)', 'z (mm)', 'change (px)', 'change (mm)', 'change (deg)', 'velocity (deg/s)', 'saccade/fixation'])

#read first frame
ret, frame = cap.read()
cv2.imshow('frame',frame)

#initialize video output
fourcc = cv2.VideoWriter_fourcc('M','J','P','G')
inputWidth, inputHeight, c = frame.shape
out = cv2.VideoWriter(data + '/out/gazeVideo.avi',fourcc, 25, (inputHeight,inputWidth))

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
processcount = 0
lastprocess = 0
linesofdata = sum(1 for line in open(data + '/eyetracking_data_raw.txt'))
currentZ = 0
gazeChangeVelocities = np.array([])
while cap.isOpened():
    processcount += 1

    dataLine = rawTrackingData.readline()
    dataLine = json.loads(dataLine)

    if 'gp3' in dataLine:
        currentZ = dataLine['gp3'][2]

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

        rawXpx = rawX * (eyetrackerResWidth/eyetrackerVideoQuality)
        rawYpx = rawY * (eyetrackerResHeight/eyetrackerVideoQuality)

        gp = np.array([[[rawXpx, rawYpx]]], dtype = "float32")

        newtransformedGp = cv2.perspectiveTransform(gp, frameMtx)[0][0]

        #set change to 0 in first iteration
        try:
            transformedGp
        except:
            transformedGp = [0,0]

        #get gaze change compared to last frame
        gazeChangeXpx = math.sqrt((transformedGp[0] - newtransformedGp[0]) ** 2)
        gazeChangeYpx = math.sqrt((transformedGp[1] - newtransformedGp[1]) ** 2)
        gazeChangePx = math.sqrt((gazeChangeXpx ** 2) + (gazeChangeYpx ** 2))

        gazeChangeXmm = float(screenWidthMM) * (float(gazeChangeXpx)/float(screenWidthPX))
        gazeChangeYmm = float(screenHeightMM) * (float(gazeChangeYpx)/float(screenHeightPX))
        gazeChangeMM = math.sqrt((gazeChangeXmm ** 2) + (gazeChangeYmm ** 2))

        #deviation angle: tan(a) = gegenkathete/ankathete
        if currentZ != 0:
            tanA = gazeChangeMM/currentZ
            gazeChangeDeg =  math.degrees(math.atan(tanA))
        else:
            gazeChangeDeg = 0

        #classify saccade (>300 deg/sec) and fixations (<100 deg/sec)
        try:
            lastDataTs
        except:
            lastDataTs = dataTs

        timeDifference = dataTs - lastDataTs
        timeDifferenceMs = float(timeDifference.microseconds) / 10000000.0

        try:
            normalizationFactor = 1 / timeDifferenceMs
        except:
            normalizationFactor = 1

        degPerSec = gazeChangeDeg * normalizationFactor
        gazeChangeVelocities = np.append(gazeChangeVelocities, int(round(degPerSec)))

        classification = ''
        if degPerSec < saccadeThreshold:
            classification = 'fixation'
        else:
            classification = 'saccade'

        #update last recorded coordinates for next iteration
        transformedGp = newtransformedGp
        lastDataTs = dataTs

        cv2.circle(frame, (transformedGp[0],transformedGp[1]), 5, (0,0,255), -1)

        with open(data + '/out/eyetracking.csv', mode='a') as eyetracking:
            eyetracking_writer = csv.writer(eyetracking, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            eyetracking_writer.writerow([dataTs,transformedGp[0] * 2,transformedGp[1] * 2, currentZ, gazeChangePx, gazeChangeMM, gazeChangeDeg, degPerSec, classification])

        # Display the resulting frame
        out.write(frame)

    if  processcount - lastprocess >= 1000:
        lastprocess = processcount
        print('process: ' + str(int((float(processcount)/float(linesofdata)) * 100)) + '%')

# When everything done, release the capture
print("skipped the rest as no marker was detected for these frames")
out.release()
cap.release()
cv2.destroyAllWindows()

#prepare and save gazeChange plot
gazeChangeVelocities = gazeChangeVelocities.astype(int)
gazeChangesValueCount = np.bincount(gazeChangeVelocities)
gazeChangeVelocityDistribution = np.nonzero(gazeChangesValueCount)[0]
zipped = zip(gazeChangeVelocityDistribution,gazeChangesValueCount[gazeChangeVelocityDistribution])

values = np.array([])
counts = np.array([])
rest = np.array([])
for item in zipped:
    if item[0] < 100: #filter outliers
        values = np.append(values, item[0])
        counts = np.append(counts, item[1])

x_pos = np.arange(len(values))[0::10]

plt.bar(values, counts, align='center')
plt.xticks(x_pos, rotation=90)
plt.title('Velocity distribution < 100 deg/s ')
plt.ylabel('count')
plt.ylabel('deg/s')
plt.savefig(data + '/out/gazeChangeVelocity.pdf')
