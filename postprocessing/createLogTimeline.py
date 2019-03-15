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

if not os.path.exists(data + '/out/'):
    os.makedirs(data + '/out/')

log = open(data + '/log.txt', 'r')
logLine = log.readline()

computedFrames = open(data + '/computed_frames.txt', 'r')
computedFramesLine = computedFrames.readline()

errorcount = 0
marker1warning = 0
marker2warning = 0
successcount = 0
totalframes = 0

errorcountList = []
tsList = []
progessProblemCount = 0
with open(data + '/out/log.csv', mode='w') as timeline:
    timeline_writer = csv.writer(timeline, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    timeline_writer.writerow(['Timestamp', 'totalFrames', 'successFrames', 'errorFrames', 'errorRate', 'marker 1 errors', 'marker 2 errors', 'problemRate', 'errormessage'])

    while logLine != '' or computedFramesLine != '':

        try:
            tmpErrorTs = datetime.strptime(logLine.split("; ")[0], "%Y-%m-%d-%H-%M-%S-%f")
            errorTs = tmpErrorTs
        except:
            tmpArray = logLine.split("(")
            tmpLine = tmpArray[len(tmpArray)-1][:-3]

            try:
                tmpErrorTs = datetime.strptime(tmpLine, "%Y-%m-%d-%H-%M-%S-%f")
                errorTs = tmpErrorTs
            except:
                progessProblemCount += 1
                pass

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


print(data + ": " + str(progessProblemCount))

#begin drawing plot
plt.plot(tsList,errorcountList)
plt.gcf().autofmt_xdate()
plt.ylabel('errors')
plt.xlabel('time')

task = ''
if data[:3].lower() == 'acc':
    task = 'accuracy'
elif data[:3].lower() == 'cha':
    task = 'chat'
elif data[:3].lower() == 'gal':
    task = 'gallery'
elif data[:3].lower() == 'map':
    task = 'map'

if task != '':
    phoneLog = open(data + '/phoneData/' + task + '/' + data + '/log.txt', 'r')
    phoneLogLine = phoneLog.readline()[:-1]
    phoneLogTs = datetime.strptime(phoneLogLine.split(": ")[0], "%Y-%m-%d %H:%M:%S,%f")

    while phoneLogLine != '':
        print(phoneLogLine)
        phoneLogLine = phoneLog.readline()[:-1]
        if phoneLogLine != '':
            phoneLogTs = datetime.strptime(phoneLogLine.split("; ")[0], "%Y-%m-%d %H:%M:%S.%f")
            plt.axvline(x=phoneLogTs, color='black', linestyle='--')
            plt.text(phoneLogTs, errorcount, phoneLogLine.split("; ")[1], rotation=90)

plt.savefig(data + '/out/logTimeline.pdf')
#plt.show()
