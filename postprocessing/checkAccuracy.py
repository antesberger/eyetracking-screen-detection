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
import math

if len(sys.argv) != 2:
    print "Please provide the folder name as an argument"
else:
    data = sys.argv[1]

# pixel postions on 1440x2880 pixel screen
marker = [(329,843), (720, 843), (1112, 843), (343, 1505), (720, 1505), (1112, 1505), (329, 2170), (720, 2155), (1112, 2170)]

log = open('./data/phone/accuracy/' + data + '/log.txt', 'r')
logLine = log.readline()
logLine = log.readline()
logLine = log.readline()
logTs = datetime.strptime(logLine.split("; ")[0], "%Y-%m-%d %H:%M:%S.%f")
logTarget = logLine.split("; ")[1][-2:-1]

deviationsX = []
deviationsY = []

with open('./out/' + data + '/accuracy.csv', mode='a') as csvoutput:
    csv_writer = csv.writer(csvoutput, lineterminator='\n')
    csv_writer.writerow(['Eyetracking ts', 'Target appeared ts', 'deviation x', 'deviation y', 'mean deviation x', 'mean deviation y'])

    with open('./out/' + data + '/eyetracking.csv', mode='r') as csvinput:
        csv_reader = csv.reader(csvinput, delimiter=',')

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

            if gazeTs > logTs and gazeTs < (logTs + dt.timedelta(0,3)):
                deviationX = int(math.sqrt((int(marker[int(logTarget) - 1][0]) - gazeX) ** 2))
                deviationY = int(math.sqrt((int(marker[int(logTarget) - 1][1]) - gazeY) ** 2))

                deviationsX.append(deviationX)
                deviationsY.append(deviationY)

                meanDeviationX = reduce(lambda x, y: x + y, deviationsX) / len(deviationsX)
                meanDeviationY = reduce(lambda x, y: x + y, deviationsY) / len(deviationsY)

                csv_writer.writerow([gazeTs, logTs, deviationX, deviationY, meanDeviationX, meanDeviationY])
            elif gazeTs > logTs:
                logLine = log.readline()
                if 'task ended' in logLine:
                    break
                logTs = datetime.strptime(logLine.split("; ")[0], "%Y-%m-%d %H:%M:%S.%f")
                logTarget = logLine.split("; ")[1][-2:-1]
