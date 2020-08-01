# LITS: Local Image Tagging and Search
Concept: Locally-run NN tagging for images. To eventually include faces, emotion, quality, and more

## Minimum viable product
Facial recognition for running in bulk across many images on your local machine.
An interface for putting names to face groups (many face versions that are all the same person)

!! Even if I don't use an SVM, I can get better matches by allowing each person to have N known pictures for almost no additional cost. This would let me supply a picture with a hat, or sunglasses, and still get good matches. !!

# Development Steps
* Read image tags
* Write image tags
* ? Detect a face in an image
* ? Detect all faces in an image
* ? Detect all faces in multiple images
* Face alignment: https://www.pyimagesearch.com/2017/05/22/face-alignment-with-opencv-and-python/
* Recognize one face in one image
* Recognize multiple faces in one image
   *Promising: https://www.pyimagesearch.com/2018/06/18/face-recognition-with-opencv-python-and-deep-learning/
* Face recognition optimization
   * Batch process: https://github.com/ageitgey/face_recognition/blob/master/examples/find_faces_in_batches.py
* Database (at picture root, probably SQLite)
* After a scan, update database so that reports are fast
* User interface: face labeling
* User interface: searching
* User interface: reports/visualizations

# Modules
Module breakdown moved to Modules.md

# Program flow
* Ask user for image search root
* Ask user for known people folder
* Ask user which analysis to do: face/quality/objects/emotion/age/gender
* List all files in folder, filter for files we can process, notify user of files we can't
* If image is in database, skip if it already has all the data we're extracting this run (face/quality/etc) and the date modified (?) matches
* Encode faces
* Run analyses on it and store to database
* Save tags for group

# Database design
* Images: Names, date taken, date modified, MD5 hash (?), exposure data, camera/lens data
* People: Names and encodings of known people
* ImagePeople: Encodings and locations of faces in images, FK:ImageId, FK:PeopleId if matched to a known person
* ImageObjects: Encodings of objects? Maybe just image-object associations. Maybe should just be on the image table?

# Optimization
* Either multiprocess per-picture, or look at the batching approach in f_r
* Take in a list of analyses to perform rather than assuming f_r is it.
* Multi-process access to sqlite may run into concurrency issues
* Test whether images need to be rotated prior to being run through f_r
   * https://medium.com/@ageitgey/the-dumb-reason-your-fancy-computer-vision-app-isnt-working-exif-orientation-73166c7d39da

# Notes 
Google Photos can easily create a pre-tagged dataset, in the sense that I can have folders where each picture contains at least that person. Not sure how to handle multiple people this way though.

How to handle removed photos?

https://github.com/davidsandberg/facenet* Old but very similar.

What if we identify and rotate faces, *then* crop/resize as necessary just the face?

Should we store encoded faces somewhere in the IPTC data? This would make recovering from a lost/corrupt database very fast.

# Visualizations
Part of WGU's capstone requirements. 

Create a separate script to extract data from the database and create charts. 

Plotly or Matplotlib. Others?

Visualization ideas:
* Number of people in pictures
* Number of people in pictures over time
* Person content over time based on image capture time
* Person / emotive content
* Percent of image that is occupied by face
* Emotive content over time based on image capture time
 
 
 
# Enhancements
Add a face clustering functionality so that users can easily pick out which people should be added to known faces

Detect people shapes and not just faces

Use multiple images of each known person
* https://github.com/ageitgey/face_recognition/blob/master/examples/face_recognition_svm.py

Tag pictures with emotional content
* https://www.neonopen.org/ is a dataset for this
* MS offers this as a service
* dlib and opencv both do this

Evaluate aesthetic and technical quality of pictures
* https://idealo.github.io/image-quality-assessment/ is a system for this, based on https://ai.googleblog.com/2017/12/introducing-nima-neural-image-assessment.html

Tag pictures with detected objects
* https://www.fritz.ai/object-detection/

Tag pictures with estimated age and gender of people
* https://towardsdatascience.com/predict-age-and-gender-using-convolutional-neural-network-and-opencv-fd90390e3ce6

Feature to re-root a database, ie, moving it or the pictures relative to each other.
* Would need hashes of the pictures or similar
* Match by file name and EXIF data, then hash?
* Update database with new path relative to picture root