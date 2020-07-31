import cv2
import os

image_path = "../test-data/unknown/work group will.jpg"
image = cv2.imread(image_path, cv2.IMREAD_COLOR)

# Parameter specifying how much the image size is reduced at each image scale.
fd_scaleFactor = 1.1

# Parameter specifying how many neighbors each candidate rectangle should have to retain it.
fd_minNeighbors = 3

# Initializes classifiers
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

# Resize image to reasonable display size
start_x = image.shape[1]
start_y = image.shape[0]
scale_factor = 1000 / start_x
resized = cv2.resize(image, None, fx=scale_factor, fy=scale_factor)

# detectMultiScale requires an CV_U8 image (gray).
gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Detects objects of different sizes in the input image.
# The detected objects are returned as a list of rectangles.
image_faces = face_cascade.detectMultiScale(gray_image, fd_scaleFactor, fd_minNeighbors, minSize=(80, 80))
print(f"Detected {len(image_faces)} faces in {image_path}")

# Draw rectangle around the faces
for (x, y, w, h) in image_faces:
    new_x = int(round(x * scale_factor))
    new_y = int(round(y * scale_factor))
    new_w = int(round(w * scale_factor))
    new_h = int(round(h * scale_factor))
    cv2.rectangle(resized, (new_x, new_y), (new_x + new_w, new_y + new_h), (0, 255, 0), 2)
cv2.imshow(f"LITS - Faces found in {image_path}", resized)
cv2.waitKey(0)

