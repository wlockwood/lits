# LITS: Local Image Tagging and Search
Concept: Locally-run NN tagging for images. To eventually include faces, emotion, quality, and more

## Minimum viable product
Facial recognition for running in bulk across many images on your local machine.
A dashboard, for capstone requirement

# Development Steps
* User interface: face labeling
* User interface: searching
* User interface: reports/visualizations

# Notes 
Google Photos can easily create a pre-tagged dataset, in the sense that I can have folders where each picture contains at least that person. Not sure how to handle multiple people this way though.

How to handle removed photos?

https://github.com/davidsandberg/facenet* Old but very similar.

What if we identify and rotate faces, *then* crop/resize as necessary just the face?

Need to determine licensing

Visualizing the calls for paperwork: https://stackoverflow.com/questions/582336/how-can-you-profile-a-python-script

# Visualizations
Part of WGU's capstone requirements. 

Create a separate script to extract data from the database and create charts. 

Example of matplotlib and PyQt 5: https://gist.github.com/holesond/b4f9db4b24eca00ef8b01a96c6e53a03

Visualization ideas:
* Number of people in pictures
* Number of people in pictures over time
* Person content over time based on image capture time
* Person / emotive content
* Percent of image that is occupied by face
* Emotive content over time based on image capture time
* exposure details over time
* time of day picture is taken
 
# Optimization
* Multiprocess per-picture. Starmap?
* Take in a list of analyses to perform rather than assuming f_r is it.
* Multi-process access to sqlite may run into concurrency issues
* Test whether images need to be rotated prior to being run through f_r
   * https://medium.com/@ageitgey/the-dumb-reason-your-fancy-computer-vision-app-isnt-working-exif-orientation-73166c7d39da
 
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