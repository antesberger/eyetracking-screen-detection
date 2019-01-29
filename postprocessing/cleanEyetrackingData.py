import json
import numpy as np
import time

trackingdata = open('./eyetrackingData/test-11-map-2019-01-09/eyetracking_data_processed.txt', 'r+')
gazecoordinates = open('./eyetrackingData/test-11-map-2019-01-09/gazecoordinates.txt', 'a+')
line = json.loads(trackingdata.readline())

while 'ts' in line:

    try:
        line = trackingdata.readline()
        line = json.loads(line)
    except:
        pass

    if 'gp' in line:
        # print line['gp']

        # width, height, c = frame.shape
        x = line['gp'][0] * 720
        y = line['gp'][1] * 1440

        gazecoordinates.write(str(line['ts']) + '; ' + str(int(x)) + '; ' + str(int(y)) + '\n')
