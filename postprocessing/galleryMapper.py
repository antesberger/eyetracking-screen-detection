import cv2
import json
import numpy as np
import time
import csv
import os
import sys
from datetime import datetime

if len(sys.argv) != 2:
    print "Please provide the folder name as an argument (e.g. "
else:
    data = sys.argv[1]

images = ['activity_1','activity_2','activity_3','activity_4','activity_5','activity_6','activity_7','activity_8','activity_9','friends_1','friends_2','friends_3','friends_4','friends_5','friends_6','friends_7','friends_8','friends_9','friends_10','selfie_1','selfie_2','selfie_3','selfie_4','selfie_5','selfie_6','selfie_7','selfie_8','selfie_9','selfie_10','captioned_1','captioned_2','captioned_3','captioned_4','captioned_5','captioned_6','captioned_7','captioned_8','captioned_9','captioned_10','gadget_1','gadget_2','gadget_3','gadget_4','gadget_5','gadget_6','gadget_7','gadget_8','gadget_9','gadget_10','pet_1','pet_2','pet_3','pet_4','pet_5','pet_6','pet_7','pet_8','pet_9','pet_10','fashion_1','fashion_2','fashion_3','fashion_4','fashion_5','fashion_6','fashion_7','fashion_8','fashion_9','fashion_10','food_1','food_2','food_3','food_4','food_5','food_6','food_7','food_8','food_9','food_10']
imagesHeight = [480, 480, 480, 405, 500, 405, 480, 925, 480, 450, 540, 510, 480, 530, 480, 480, 480, 480, 510, 480, 480, 480, 480, 480, 468, 960, 480, 480, 1080, 960, 560, 480, 480, 480, 540, 405, 540, 480, 940, 480, 480, 480, 450, 480, 510, 480, 480, 480, 405, 480, 480, 480, 1083, 406, 540, 480, 480, 540, 1080, 480, 480, 480, 480, 480, 430, 440, 480, 390, 480, 480, 480, 480, 480, 840, 480, 480, 405, 420, 430]
imagesHeight = [(i * 2) + 55 for i in imagesHeight]

imageData = open(data + '/scrollInfo.txt', 'r')
randomOrder = open(data + '/imageorder.txt', 'r')
scrollLine = imageData.readline()
nextScrollLine = imageData.readline()

randomOrderIndices = randomOrder.readline()
randomOrderIndices = randomOrder.readline()
randomOrderIndices = randomOrderIndices[:-1].split(";  ")[1].split(", ")

#restore random order
i = len(imagesHeight) - 1
for index in randomOrderIndices:
    tmp = images[int(index)]
    images[int(index)] = images[i]
    images[i] = tmp

    tmp = imagesHeight[int(index)]
    imagesHeight[int(index)] = imagesHeight[i]
    imagesHeight[i] = tmp

    i = i - 1
with open(data + '/out/imageMapping.csv', mode='a') as csvoutput:
    csv_writer = csv.writer(csvoutput, lineterminator='\n')
    csv_writer.writerow(['Timestamp', 'x', 'y', 'image', 'first image end', 'second image end', 'third image end'])

with open(data + '/out/eyetracking.csv', mode='r') as csvinput:
    csv_reader = csv.reader(csvinput, delimiter=',')

    all = []

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

        if nextScrollLine.split("; ")[0] == '':
            continue

        scrollTs = datetime.strptime(scrollLine.split("; ")[0], "%Y-%m-%d %H:%M:%S.%f")
        nextScrollTs = datetime.strptime(nextScrollLine.split("; ")[0], "%Y-%m-%d %H:%M:%S.%f")

        #if scrolled in meantime
        if gazeTs >= nextScrollTs:
            scrollLine = nextScrollLine
            nextScrollLine = imageData.readline()
            scrollLineSplit = scrollLine.split("; ")

        try:
            scrollLineSplit[2]
        except:
            print "except"
            continue

        #print(imageDataLine[2])
        lastVisibleImage = int(scrollLineSplit[1])
        relativeScrollPostion = scrollLineSplit[2].split(",")

        if len(relativeScrollPostion) == 3:
            relativeScrollPostion = relativeScrollPostion[2][:-2]
            offset = 0
            i = 0

            while i < lastVisibleImage:
                offset += int(imagesHeight[i])
                i += 1

            try:
                firstImage = int(relativeScrollPostion)
                secondImage = firstImage + imagesHeight[i+1]
                thirdImage = secondImage + imagesHeight[i+2]
            except:
                pass

            #print str(firstImage) + ", " + str(secondImage) + ", " + str(thirdImage)
            image = ''
            if gazeX > 0 and gazeX < 1440:
                if gazeY > 0 and gazeY <= firstImage:
                    image = images[i]
                    print(str(gazeTs) + ": " + images[i] + "; " + str(gazeY) + "; " + str(firstImage))
                elif gazeY <= secondImage:
                    image = images[i + 1]
                    print(str(gazeTs) + ": " + images[i+1] + "; " + str(gazeY) + "; " + str(secondImage))
                elif gazeY < (2880 - 170) and gazeY <= thirdImage: # 170 because of black bar at the bootom
                    image = images[i + 2]
                    print(str(gazeTs) + ": " + images[i+2] + "; " + str(gazeY) + "; " + str(thirdImage))
                else:
                    image = 'none'
                    print(str(gazeTs) + ": " + 'none')
            else:
                image = 'none'
                print(str(gazeTs) + ": " + 'none')

            with open(data + '/out/imageMapping.csv', mode='a') as csvoutput:
                csv_writer = csv.writer(csvoutput, lineterminator='\n')
                csv_writer.writerow([gazeTs, gazeX, gazeY, image, str(firstImage), str(secondImage), str(thirdImage)])

        else:
            print "problems reading"
