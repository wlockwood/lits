# Implementation notes
face_recognition uses dlib, which uses a CNN to recognize faces. This turns out to be fairly slow, so I attempted to improve speed by using OpenCV (which detects but does not recognize faces in real time) to identify face locations before passing to face_recognition to recognize faces, but this resulted in faces never being recognized, possibly because the bounding boxes were too small (which could be solved with padding), but after adding a visualization to the face detection step, I realized OpenCV had high rates for both false positives (detecting a face where there was none) and false negatives (failing to detect faces in a picture). 

Ultimately, I addressed this by resizing pictures to around 750px (~0.6 megapixels) while maintaining their aspect ratios as many of the pictures in my dataset were at or 4000x2669 (10 megapixels) or larger. There was a more-or-less linear correlation between image resolution and time taken to encode the faces in that image.

In addition to being somewhat slow, the CNN isn't particularly accurate. The [Github repo](https://github.com/ageitgey/face_recognition) claims this:
> Built using dlib's state-of-the-art face recognition built with deep learning. The model has an accuracy of 99.38% on the Labeled Faces in the Wild benchmark.

Subjectively the accuracy felt significantly lower, so I set out to see how good or bad it was.