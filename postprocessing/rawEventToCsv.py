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

rawEvents = open(data + '/rawEvent.txt', 'r')
rawHistoricalEvents = open(data + '/rawHistoricalEvent.txt', 'r')

rawEventLine = rawEvents.readline()
rawHistEventLine = rawHistoricalEvents.readline()

with open(data + '/out/motionEvents.csv', mode='a') as csvoutput:
    csv_writer = csv.writer(csvoutput, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    csv_writer.writerow(['timestamp', 'action', 'actionButton', 'id[0]', 'x[0]', 'y[0]', 'toolType[0]', 'buttonState', 'metaState', 'flags', 'edgeFlags', 'pointerCount', 'historySize', 'eventTime', 'downTime', 'deviceId', 'source'])

    while rawEventLine != '' and rawHistEventLine != '':
        rawEventTs = datetime.strptime(rawEventLine.split("; ")[0], "%Y-%m-%d %H:%M:%S.%f")
        rawHistEventTs = datetime.strptime(rawHistEventLine.split("; ")[0], "%Y-%m-%d %H:%M:%S.%f")

        content = ''
        if rawEventTs < rawHistEventTs and rawEventTs != '':
            content = rawEventLine.split("; ")[1][14:-3].split(", ")
            content = [i.split("=")[1] for i in content]
            content.insert(0,str(rawEventTs))
            rawEventLine = rawEvents.readline()

        elif rawHistEventTs <= rawEventTs and rawHistEventTs != '':
            content = rawHistEventLine.split("; ")[1][14:-3].split(", ")
            content = [i.split("=")[1] for i in content]
            content.insert(0,str(rawHistEventTs))
            rawHistEventLine = rawHistoricalEvents.readline()

        csv_writer.writerow(content)
