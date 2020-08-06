# Implementation notes
## OpenCV Face Detection
face_recognition uses dlib, which uses a CNN to recognize faces. This turns out to be fairly slow, so I attempted to improve speed by using OpenCV (which detects but does not recognize faces in real time) to identify face locations before passing to face_recognition to recognize faces, but this resulted in faces never being recognized, possibly because the bounding boxes were too small (which could be solved with padding), but after adding a visualization to the face detection step, I realized OpenCV had high rates for both false positives (detecting a face where there was none) and false negatives (failing to detect faces in a picture). 

I addressed the speed issue by resizing pictures to around 750px (~0.6 megapixels) while maintaining their aspect ratios as many of the pictures in my dataset were at or 4000x2669 (10 megapixels) or larger. There was a more-or-less linear correlation between image resolution and time taken to encode the faces in that image.

## Dlib Resizing
In an attempt to reduce my dependencies after getting rid of opencv, I switched to using dlib's image resizing algorithm, which brought the script's successful face match rate from around 90% to around 3%. I failed to re-profile face recognition performance after this change, and was surprised a few days later when said metric had dropped to a rather abysmal 3%. I changed over to loading and resizing images with Pillow and tested out the effect of different resize targets: 

## Accuracy
In addition to being somewhat slow, the CNN isn't particularly accurate. The [Github repo](https://github.com/ageitgey/face_recognition) claims this:
> Built using dlib's state-of-the-art face recognition built with deep learning. The model has an accuracy of 99.38% on the Labeled Faces in the Wild benchmark.

Subjectively the accuracy felt significantly lower, so I set out to see if I could identify where I would see diminishing returns in time-spent-per-image vs accuracy. For each image, I used the calculation below to determine accuracy:

```
[success percent] = [faces found] - ([false positive] + [false negatives])/2 / [expected face count] if [expected face count] > 0]
```
Dividing the sum of false positive/negative hits by two means the system isn't doubly penalized for mistaking a face. Images with no faces in them were included in the test set and were assigned a score of 100% if no faces were found.


## Duplication of work
Two days after I finished the work to get the system to correctly identify known people in unknown pictures - the bulk of the work that was done on this project - I realized that one of the libaries I was importing included a CLI interface for doing exactly that. This was pretty disheartening, but ultimately, it's limited to just that, and is missing the database integration and metadata tagging features that make this activity useful to a photographer.

## File identification
In the database, each `ImageFile` is uniquely identified by an auto-incrementing integer id, but I needed some way to reliably associate any given image file with the correct row in the database, preferably in a way that would survive files being moved around. I came up with (filename + date modified + file size) together as a way of doing so, although this has the major downside that any changes to a picture's metadata - which don't affect the content of the image itself, but are stored in the file and thus affect both its date modified according to the filesystem and the total size of the file (in most cases).

To get around this, I intend to replace the current approach with an algorithm that would identify images by filename and confirm them by comparing a [perceptual hash](https://pypi.org/project/ImageHash/) of *just* the image data, and accepting anything within a fairly small hashed distance. This would mean that files that are only changed slightly should still be recognized and not re-scanned. The point in using two passes (filename *and then* a hash of image data) is that hashing an image's contents is significantly more expensive than reading its filename or filesystem metadata.