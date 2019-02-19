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
    start = int(sys.argv[2])
    end = int(sys.argv[3])
elif len(sys.argv) == 5:
    data = sys.argv[1]
    start = int(sys.argv[2])
    end = int(sys.argv[3])
    eventType = sys.argv[4]

if int(start) > int(end):
        print ("The start argument should be bigger than the end.")
        sys.exit(0)

xCoordinates = np.array([])
yCoordinates = np.array([])
startTs = 0

#loop through touch events
with open('./out/' + data + '/gesture.csv', mode='r') as csvinput:
    csv_reader = csv.reader(csvinput, delimiter=',')

    #first row is only header info
    header = True
    for row in csv_reader:
        if header == True:
            header = False
            continue

        touchTs = row[0]
        currentEventType = row[1]
        touchX = int(float(row[5]))
        touchY = int(float(row[6]))

        try: #milliseconds are missing for a few eyetracking timestamps
            touchTs = datetime.strptime(touchTs, "%Y-%m-%d %H:%M:%S.%f")
        except:
            touchTs = datetime.strptime(touchTs, "%Y-%m-%d %H:%M:%S")

        #only consider the chosen event type
        if eventType != None and not eventType.lower() in currentEventType.lower():
            continue

        #filter for chosen timeframe
        if startTs == 0:
            startTs = touchTs

        currentTimePosition = touchTs - startTs
        if start != -1 and end != -1:
            if currentTimePosition < dt.timedelta(0,int(start)) or currentTimePosition > dt.timedelta(0,int(end)):
                continue

        if touchX >= 0 and touchX <= screenWidthPX and touchY >= 0 and touchY <= screenHeightPX:
            xCoordinates = np.append(xCoordinates, touchX)
            yCoordinates = np.append(yCoordinates, touchY)

#prepare and save heatmap plot
heatmap, xedges, yedges = np.histogram2d(xCoordinates, yCoordinates, bins=(120,240))
extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]

plt.clf()

if start >= 0 and end >= 0:
    plt.title('Touch Heatmap [' + str(start) + 's,' + str(end) + 's]')
else:
    plt.title('Touch Heatmap')

plt.imshow(heatmap.T, extent=extent, origin='lower', interpolation='nearest')
plt.set_cmap('BuPu')
plt.colorbar()
plt.savefig('./out/' + data + '/touchHeatmap.pdf')
