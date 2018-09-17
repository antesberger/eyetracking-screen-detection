import cv2
import tobii_research as tr
import time

# Get the eyetracker
found_eyetrackers = tr.find_all_eyetrackers()
print found_eyetrackers
my_eyetracker = found_eyetrackers[0]
print("Address: " + my_eyetracker.address)
print("Model: " + my_eyetracker.model)
print("Name (It's OK if this is empty): " + my_eyetracker.device_name)
print("Serial number: " + my_eyetracker.serial_number)

# Create a VideoCapture object and read from input file
# If the input is taken from the camera, pass 0 instead of the video file name.
cap = cv2.VideoCapture('./markers/test9.mp4')
dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

calibrationFile = "calibrationFileName.xml"
calibrationParams = cv2.FileStorage(calibrationFile, cv2.FILE_STORAGE_READ)
camera_matrix = calibrationParams.getNode("cameraMatrix").mat()
dist_coeffs = calibrationParams.getNode("distCoeffs").mat()

board = cv2.aruco.GridBoard_create(2, 2, 2, 2, dictionary)

i = 0
while(True):
    i = i + 1
    # Capture frame-by-frame
    ret, frame = cap.read()

    # Display the resulting frame
    print("processing frame " + str(i))
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) # aruco.detectMarkers() requires gray image

    markers = cv2.aruco.detectMarkers(frame_gray,dictionary)
    corners, ids, rejectedImgPoints = markers
    cv2.aruco.refineDetectedMarkers(frame_gray, board, corners, ids, rejectedImgPoints)

    if len(markers[0]) > 0:
        print("marker detected")
        marker_image = cv2.aruco.drawDetectedMarkers(frame_gray,markers[0],markers[1])
        retval, rvec, tvec = cv2.aruco.estimatePoseBoard(corners, ids, board, camera_matrix, dist_coeffs)  # posture estimation from a diamond
        if retval != 0:
            im_with_aruco_board = cv2.aruco.drawAxis(marker_image, camera_matrix, dist_coeffs, rvec, tvec, 100)
    else:
        print("no markers in frame")

    # Display the resulting frame
    cv2.imshow('frame',frame_gray)

    if( cv2.waitKey(100) == 27 ):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
