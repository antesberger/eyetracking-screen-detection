import cv2

# Create a VideoCapture object and read from input file
# If the input is taken from the camera, pass 0 instead of the video file name.
cap = cv2.VideoCapture('./markers/test2.mp4')
dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

i = 0
while(True):
    i = i + 1
    # Capture frame-by-frame
    ret, frame = cap.read()

    # Display the resulting frame
    print("processing frame " + str(i))
    res = cv2.aruco.detectMarkers(frame,dictionary)

    if len(res[0]) > 0:
        print("marker detected")
        cv2.aruco.drawDetectedMarkers(frame,res[0],res[1])
    else:
        print("no markers in frame")

    # Display the resulting frame
    cv2.imshow('frame',frame)

    if( cv2.waitKey(100) == 27 ):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
