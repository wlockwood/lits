import numpy as np
import cv2 as cv
from copy import deepcopy
from time import perf_counter as pc

cap = cv.VideoCapture(0)

if not cap.isOpened():
	print("Cannot open camera")
	exit()
while True:
	# Capture frame-by-frame
	ret, frame = cap.read()
	
	# if frame is read correctly ret is True
	if not ret:
		print("Can't receive frame (stream end?) Exiting...")
		break
	
	# Our operations on the frame come here
	edges = cv.Canny(frame, 100, 200, 3)
	inverse = cv.bitwise_not(edges)

	# Display the resulting frame
	cv.imshow('frame', inverse)
	
	if cv.waitKey(1) == ord('q'):
		break
	
# When done, release the camera
cap.release()
cv.destroyAllWindows()