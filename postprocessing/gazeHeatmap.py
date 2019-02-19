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

#read arguments
if len(sys.argv) < 2 or len(sys.argv) > 4:
    print("Please provide arguments in the form: <directory> <start time> <end time>")
    print("Start and end time (both given in seconds) are optional")
    sys.exit(0)
elif len(sys.argv) == 2:
    data = sys.argv[1]
elif len(sys.argv) == 4:
    data = sys.argv[1]
    start = sys.argv[2]
    end = sys.argv[3]

if int(start) > int(end):
    print ("The start argument should be bigger than the end.")
    sys.exit(0)

xCoordinates = np.array([])
yCoordinates = np.array([])
startTs = 0

#loop through gaze coordinates
with open('./out/' + data + '/eyetracking.csv', mode='r') as csvinput:
    csv_reader = csv.reader(csvinput, delimiter=',')

    #ignore first row only containing header info
    header = True
    for row in csv_reader:
        if header == True:
            header = False
            continue

        gazeTs = row[0]
        gazeX = int(float(row[1]))
        gazeY = int(float(row[2]))

        try: #milliseconds are missing for a few eyetracking timestamps
            gazeTs = datetime.strptime(gazeTs, "%Y-%m-%d %H:%M:%S.%f")
        except:
            gazeTs = datetime.strptime(gazeTs, "%Y-%m-%d %H:%M:%S")

        if startTs == 0:
            startTs = gazeTs

        currentTimePosition = gazeTs - startTs

        #filter for chosen timeframe
        if start != -1 and end != -1:
            if currentTimePosition < dt.timedelta(0,int(start)) or currentTimePosition > dt.timedelta(0,int(end)):
                continue

        #only consider gaze events which take place on the screen
        if gazeX >= 0 and gazeX <= screenWidthPX and gazeY >= 0 and gazeY <= screenHeightPX:
            xCoordinates = np.append(xCoordinates, gazeX)
            yCoordinates = np.append(yCoordinates, gazeY)

#prepare and save heatmap plot
heatmap, xedges, yedges = np.histogram2d(xCoordinates, yCoordinates, bins=(45,90))
extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]

plt.clf()

if int(start) >= 0 and int(end) >= 0:
    plt.title('Gaze Heatmap [' + start + 's,' + end + 's]')
else:
    plt.title('Gaze Heatmap')

plt.imshow(heatmap.T, extent=extent, origin='lower', interpolation='nearest')
plt.set_cmap('BuPu')
plt.colorbar()
plt.savefig('./out/' + data + '/gazeHeatmap.pdf')
