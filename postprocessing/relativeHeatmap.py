import cv2
import json
import numpy as np
import time
import csv
import os
import sys
from datetime import datetime
import datetime as dt
import matplotlib.pyplot as plt
import configparser

#read config params
config = configparser.ConfigParser()
config.read('../config.ini')
screenHeightPX = int(config['DEFAULT']['screenHeightPX'])
screenWidthPX = int(config['DEFAULT']['screenWidthPX'])

#default arguments
start = -1
end = -1
eventType = None

#read arguments
if len(sys.argv) < 2 or len(sys.argv) > 5:
    print("Please provide arguments in the form: <directory> <start time> <end time> <event type>")
    print("Start, end time (both given in seconds) and event type are optional")
    print("Event types: Scroll, SingleTapConfirmed, DoubleTap, Down, ShowPress, SingleTapUp, LongPress and Fling")
    sys.exit(0)
elif len(sys.argv) == 2:
    data = sys.argv[1]
elif len(sys.argv) == 4:
    data = sys.argv[1]
    start = sys.argv[2]
    end = sys.argv[3]
elif len(sys.argv) == 5:
    data = sys.argv[1]
    start = sys.argv[2]
    end = sys.argv[3]
    eventType = sys.argv[4]

if int(start) > int(end):
    print ("The start argument should be bigger than the end.")
    sys.exit(0)

#safe gesture data to array
#csv needs to be created beforehand
touchData = []
with open(data + '/out/gesture.csv', mode='r') as csvinputtouch:
    touch_reader = csv.reader(csvinputtouch, delimiter=',')

    header = True
    for row in touch_reader:
        if header == True:
            header = False
            continue

        touchData.append(row)

differencesX = np.array([])
differencesY = np.array([])

touchTs = datetime.strptime(touchData[0][0], "%Y-%m-%d %H:%M:%S.%f")
totalCount = 0

xCoordinates = np.array([])
yCoordinates = np.array([])
startTs = 0
i = 0

#iterate through every line in eyetracking.csv
#in each iteration: check each touch event which took place in between last and current eyetracking timestamp
#append difffernce of touch and gaze coordinates to array
with open(data + '/out/eyetracking.csv', mode='r') as csvinputgaze:
    gaze_reader = csv.reader(csvinputgaze, delimiter=',')

    header = True
    for gazeRow in gaze_reader:
        if header == True:
            header = False
            continue

        gazeX = int(float(gazeRow[1]))
        gazeY = int(float(gazeRow[2]))

        try: #milliseconds are missing for a few timestamps
            gazeTs = datetime.strptime(gazeRow[0], "%Y-%m-%d %H:%M:%S.%f")
        except:
            gazeTs = datetime.strptime(gazeRow[0], "%Y-%m-%d %H:%M:%S")

        if startTs == 0:
            startTs = gazeTs

        currentTimePosition = gazeTs - startTs
        if int(start) != -1 and int(end) != -1:
            if currentTimePosition < dt.timedelta(0,int(start)) or currentTimePosition > dt.timedelta(0,int(end)):
                continue

        while touchTs < gazeTs:
            try:
                currentEventType = touchData[i][1]
                touchX = int(float(touchData[i][5]))
                touchY = int(float(touchData[i][6]))
            except:
                break

            try: #milliseconds are missing for a few timestamps
                touchTs = datetime.strptime(touchData[i][0], "%Y-%m-%d %H:%M:%S.%f")
            except:
                touchTs = datetime.strptime(touchData[i][0], "%Y-%m-%d %H:%M:%S")

            i += 1
            totalCount += 1

            #only consider the chosen event type
            if eventType != None and not eventType.lower() in currentEventType.lower():
                continue

            differenceX = gazeX - touchX
            differenceY = gazeY - touchY

            #only consider events which took place on the screen
            if differenceX <= screenWidthPX and differenceX >= -screenWidthPX and differenceY <= screenHeightPX and differenceY >= -screenHeightPX:
                differencesX = np.append(differencesX, differenceX)
                differencesY = np.append(differencesY, differenceY)

#prepare and save heatmap plot
heatmap, xedges, yedges = np.histogram2d(differencesX, differencesY, bins=(100,200))
extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]

plt.clf()

if int(start) >= 0 and int(end) >= 0:
    plt.title('Relative Touch Heatmap [' + start + 's,' + end + 's]')
else:
    plt.title('Relative Touch Heatmap')

plt.imshow(heatmap.T, extent=extent, origin='lower', interpolation='nearest')
plt.set_cmap('BuPu')
plt.colorbar()
plt.savefig(data + '/out/relativeTouchHeatmap.pdf')
