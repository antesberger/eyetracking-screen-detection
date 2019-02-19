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
import configparser

if len(sys.argv) != 2:
    print("Please provide the folder name as an argument")
    sys.exit(0)
else:
    data = sys.argv[1]

#read config params
config = configparser.ConfigParser()
config.read('../config.ini')
screenHeightMM = int(config['DEFAULT']['screenHeightMM'])
screenWidthMM = int(config['DEFAULT']['screenWidthMM'])
screenHeightPX = int(config['DEFAULT']['screenHeightPX'])
screenWidthPX = int(config['DEFAULT']['screenWidthPX'])

# pixel postions on 1440x2880 pixel screen
marker = [(329,843), (720, 843), (1112, 843), (343, 1505), (720, 1505), (1112, 1505), (329, 2170), (720, 2155), (1112, 2170)]

log = open('./data/phone/accuracy/' + data + '/log.txt', 'r')
logLine = log.readline()
logLine = log.readline()
logLine = log.readline()
logTs = datetime.strptime(logLine.split("; ")[0], "%Y-%m-%d %H:%M:%S.%f")
logTarget = logLine.split("; ")[1][-2:-1]

deviationsXpx = []
deviationsYpx = []
totalDeviationsPx = []
totalDeviationsMm = []
deviationsDeg = []

with open('./out/' + data + '/accuracy.csv', mode='a') as csvoutput:
    csv_writer = csv.writer(csvoutput, lineterminator='\n')
    csv_writer.writerow(['Eyetracking ts', 'Target appeared ts', 'deviation x in px', 'deviation y in px', 'deviation in px', 'deviation mm', 'deviation degree', 'mean deviation px', 'mean deviation mm', 'mean deviation degree'])

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
            gazeZ = float(row[3])

            try: #milliseconds are missing for a few eyetracking timestamps
                gazeTs = datetime.strptime(gazeTs, "%Y-%m-%d %H:%M:%S.%f")
            except:
                gazeTs = datetime.strptime(gazeTs, "%Y-%m-%d %H:%M:%S")

            if gazeTs > logTs and gazeTs < (logTs + dt.timedelta(0,3)):

                #get devation in px
                deviationXpx = int(math.sqrt((int(marker[int(logTarget) - 1][0]) - gazeX) ** 2))
                deviationYpx = int(math.sqrt((int(marker[int(logTarget) - 1][1]) - gazeY) ** 2))
                totalDeviationPx = int(math.sqrt((deviationXpx ** 2) + (deviationYpx ** 2)))

                #deviation in mm
                deviationXmm = float(screenWidthMM) * (float(deviationXpx)/float(screenWidthPX))
                deviationYmm = float(screenHeightMM) * (float(deviationYpx)/float(screenHeightPX))
                totalDeviationMM = int(math.sqrt((deviationXmm ** 2) + (deviationYmm ** 2)))

                #deviation angle: tan(a) = gegenkathete/ankathete
                if gazeZ != 0:
                    tanA = totalDeviationMM/gazeZ
                    deviationDeg =  math.degrees(math.atan(tanA))
                else:
                    deviationDeg = 0

                #getting mean values
                deviationsXpx.append(deviationXpx)
                deviationsYpx.append(deviationYpx)
                totalDeviationsPx.append(totalDeviationPx)
                totalDeviationsMm.append(totalDeviationMM)
                deviationsDeg.append(deviationDeg)

                meanDeviationXpx = reduce(lambda x, y: x + y, deviationsXpx) / len(deviationsXpx)
                meanDeviationYpx = reduce(lambda x, y: x + y, deviationsYpx) / len(deviationsYpx)
                meanTotalDeviationPx = reduce(lambda x, y: x + y, totalDeviationsPx) / len(totalDeviationsPx)
                meanTotalDeviationMm = reduce(lambda x, y: x + y, totalDeviationsMm) / len(totalDeviationsMm)
                meanDeviationDeg = reduce(lambda x, y: x + y, deviationsDeg) / len(deviationsDeg)

                #writing values to csv
                csv_writer.writerow([gazeTs, logTs, deviationXpx, deviationYpx, totalDeviationPx, totalDeviationMM, deviationDeg, meanTotalDeviationPx, meanTotalDeviationMm, meanDeviationDeg])
            elif gazeTs > logTs:
                logLine = log.readline()
                if 'task ended' in logLine:
                    break
                logTs = datetime.strptime(logLine.split("; ")[0], "%Y-%m-%d %H:%M:%S.%f")
                logTarget = logLine.split("; ")[1][-2:-1]
