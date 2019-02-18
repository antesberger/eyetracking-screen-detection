import cv2
import json
import numpy as np
import time
import csv
import os
import sys
from datetime import datetime

if len(sys.argv) != 2:
    print "Please provide the folder name as an argument"
else:
    data = sys.argv[1]

task = ''
if data[:3].lower() == 'acc':
    task = 'accuracy'
elif data[:3].lower() == 'cha':
    task = 'chat'
elif data[:3].lower() == 'gal':
    task = 'gallery'
elif data[:3].lower() == 'map':
    task = 'map'

gesture = open('./data/phone/' + task + '/' + data + '/gesture.txt', 'r')
gestureLine = gesture.readline()

with open('./out/' + data + '/gesture.csv', mode='a') as csvoutput:
    csv_writer = csv.writer(csvoutput, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    csv_writer.writerow(['timestamp', 'type', 'action', 'actionButton', 'id[0]', 'x[0]', 'y[0]', 'toolType[0]', 'buttonState', 'metaState', 'flags', 'edgeFlags', 'point^C0]', 'toolType[0]', 'buttonState', 'metaState', 'flags', 'edgeFlags', 'pointerCount', 'historySize', 'eventTime', 'downTime', 'deviceId', 'source'])

    while gestureLine != '':
        ts = datetime.strptime(gestureLine.split("; ")[0], "%Y-%m-%d %H:%M:%S.%f")
        gestureType = gestureLine.split("; ")[1].split(": ")[0]

        rawcontent = gestureLine.split("MotionEvent { ")[1][:-4].split(", ")
        content = [i.split("=")[1] for i in rawcontent]

        content.insert(0,gestureType)
        content.insert(0,str(ts))

        print content
        csv_writer.writerow(content)
        gestureLine = gesture.readline()
