import numpy as np
import cv2
import glob

imgpoints = []
objpoints = []
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
objp = np.zeros((6*9,3), np.float32)
objp[:,:2] = np.mgrid[0:9,0:6].T.reshape(-1,2)
framecount = 0
buffer = '000'
firstimg = cv2.imread('./markers/frames/frame-0001.jpg',0)

while framecount < 407:
    framecount += 5

    if framecount == 10:
        buffer = '00'
    elif framecount == 100:
        buffer = '0'

    path = './markers/frames/frame-' + buffer + str(framecount) + '.jpg'
    print path
    img = cv2.imread(path, 0)
    if img is not None:
        # Find the chess board corners
        state,corners = cv2.findChessboardCorners(img, (9,6), flags=cv2.CALIB_CB_FILTER_QUADS)

        # If found, add object points, image points (after refining them)
        if state == 1:
            objpoints.append(objp)

            corners2 = cv2.cornerSubPix(img,corners,(11,11),(-1,-1),criteria)
            imgpoints.append(corners2)

            # Draw and display the corners
            img = cv2.drawChessboardCorners(img, (9,6), corners2,state)
        
        cv2.imshow('img',img)
        cv2.waitKey(500)

ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, firstimg.shape[::-1], None, None)
h,  w = firstimg.shape[:2]
newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w,h), 1, (w,h))
print('dist')
print(dist)
print('newcameramtx')
print(newcameramtx)

dst = cv2.undistort(firstimg, mtx, dist, None, newcameramtx)
cv2.imwrite('calibresult.png', dst)

cv2.destroyAllWindows()
