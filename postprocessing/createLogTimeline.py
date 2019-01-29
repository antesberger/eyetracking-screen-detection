import cv2
import json
import numpy as np
import time
import csv
import os
import sys
from datetime import datetime
import matplotlib.pyplot as plt

if len(sys.argv) != 2:
    print "Please provide the folder name as an argument"
else:
    data = sys.argv[1]

log = open('./data/eyetracking/' + data + '/log.txt', 'r')
logLine = log.readline()

computedFrames = open('./data/eyetracking/' + data + '/computed_frames.txt', 'r')
computedFramesLine = computedFrames.readline()

errorcount = 0
marker1warning = 0
marker2warning = 0
successcount = 0
totalframes = 0

errorcountList = []
tsList = []
with open('./out/' + data + '/log.csv', mode='w') as timeline:
    timeline_writer = csv.writer(timeline, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    timeline_writer.writerow(['Timestamp', 'totalFrames', 'successFrames', 'errorFrames', 'errorRate', 'marker 1 errors', 'marker 2 errors', 'problemRate', 'errormessage'])

    while logLine != '' or computedFramesLine != '':

        try:
            errorTs = datetime.strptime(logLine.split("; ")[0], "%Y-%m-%d-%H-%M-%S-%f")
        except:
            pass

        try:
            successTs = datetime.strptime(computedFramesLine.split("; ")[1], "%Y-%m-%d-%H-%M-%S-%f")
        except:
            pass

        if (errorTs <= successTs and logLine != '') or computedFramesLine == '':
            totalframes += 1

            if 'no markers detected' in logLine:
                errorcount += 1
                timeline_writer.writerow([errorTs,totalframes,successcount,errorcount,float(errorcount)/float(totalframes),marker1warning,marker2warning, float(errorcount + marker1warning + marker2warning)/float(totalframes), 'no marker detected'])
                #print str(errorTs) + "; " + str(successcount) + "; " + str(errorcount) + "; " + str(marker1warning) + "; " + str(marker2warning) + "; no marker detected"

            if 'marker 1 not detected' in logLine:
                marker1warning += 1
                timeline_writer.writerow([errorTs,totalframes,successcount,errorcount,float(errorcount)/float(totalframes),marker1warning,marker2warning, float(errorcount + marker1warning + marker2warning)/float(totalframes), 'marker 1 not detected'])
                #print str(errorTs) + "; " + str(successcount) + "; " + str(errorcount) + "; " + str(marker1warning) + "; " + str(marker2warning) + "; marker 1 not detected"

            if 'marker 3 not detected' in logLine:
                marker2warning += 1
                timeline_writer.writerow([errorTs,totalframes,successcount,errorcount,float(errorcount)/float(totalframes),marker1warning,marker2warning, float(errorcount + marker1warning + marker2warning)/float(totalframes), 'marker 3 not detected'])
                #print str(errorTs) + "; " + str(successcount) + "; " + str(errorcount) + "; " + str(marker1warning) + "; " + str(marker2warning) + "; marker 3 not detected"

            tsList.append(errorTs)
            logLine = log.readline()
        elif (errorTs > successTs and computedFramesLine != '') or logLine == '':
            totalframes += 1
            successcount += 1
            tsList.append(successTs)
            timeline_writer.writerow([successTs,totalframes,successcount,errorcount,float(errorcount)/float(totalframes),marker1warning,marker2warning, float(errorcount + marker1warning + marker2warning)/float(totalframes), 'success'])
            #print str(errorTs) + "; " + str(successcount) + "; " + str(errorcount) + "; " + str(marker1warning) + "; " + str(marker2warning) + "; success"
            computedFramesLine = computedFrames.readline()
            computedFramesLine = computedFrames.readline()
            computedFramesLine = computedFrames.readline()

        errorcountList.append(errorcount)

plt.plot(tsList,errorcountList)
plt.gcf().autofmt_xdate()
plt.ylabel('errors')
plt.xlabel('time')
plt.savefig('./out/' + data + '/logTimeline.pdf')
#plt.show()
