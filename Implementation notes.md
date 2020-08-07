# Implementation notes
## OpenCV Face Detection
face_recognition uses dlib, which uses a CNN to recognize faces. This turns out to be fairly slow, so I attempted to improve speed by using OpenCV (which detects but does not recognize faces in real time) to identify face locations before passing to face_recognition to recognize faces, but this resulted in faces never being recognized, possibly because the bounding boxes were too small (which could be solved with padding), but after adding a visualization to the face detection step, I realized OpenCV had high rates for both false positives (detecting a face where there was none) and false negatives (failing to detect faces in a picture). 

I addressed the speed issue by resizing pictures to around 750px (~0.6 megapixels) while maintaining their aspect ratios as many of the pictures in my dataset were at or 4000x2669 (10 megapixels) or larger. There was a more-or-less linear correlation between image resolution and time taken to encode the faces in that image.

## Dlib Resizing
In an attempt to reduce my dependencies after getting rid of opencv, I switched to using dlib's image resizing algorithm, which brought the script's successful face match rate from around 90% to around 3%. I failed to re-profile face recognition performance after this change, and was surprised a few days later when said metric had dropped to a rather abysmal 3%. I changed over to loading and resizing images with Pillow and tested out the effect of different resize targets: 

## Accuracy
In addition to being somewhat slow, the CNN wasn't initially particularly accurate. The [Github repo](https://github.com/ageitgey/face_recognition) claims this:
> Built using dlib's state-of-the-art face recognition built with deep learning. The model has an accuracy of 99.38% on the Labeled Faces in the Wild benchmark.

Subjectively the accuracy felt significantly lower, so I set out to see if I could identify where I would see diminishing returns in time-spent-per-image vs accuracy. For each image, I used the calculation below to determine accuracy:

```
[success percent] = [faces found] - ([false positive] + [false negatives])/2 / [expected face count] if [expected face count] > 0]
```
Dividing the sum of false positive/negative hits by two means the system isn't doubly penalized for mistaking a face. Images with no faces in them were included in the test set and were assigned a score of 100% if no faces were found.

The readme also indicates that dlib's face recognition is poor at recognizing children, and my own tests bore that out - basically any child under about six year old matched with the child in my "known" group, a blonde three-year-old girl.


## Duplication of Work
Two days after I finished the work to get the system to correctly identify known people in unknown pictures - the bulk of the work that was done on this project - I realized that one of the libaries I was importing included a CLI interface for doing exactly that. This was pretty disheartening, but ultimately, it's limited to just that, and is missing the database integration and metadata tagging features that make this activity useful to a photographer.

## File Identification
In the database, each `ImageFile` is uniquely identified by an auto-incrementing integer id, but I needed some way to reliably associate any given image file with the correct row in the database, preferably in a way that would survive files being moved around. I came up with (filename + date modified + file size) together as a way of doing so, although this has the major downside that any changes to a picture's metadata - which don't affect the content of the image itself, but are stored in the file and thus affect both its date modified according to the filesystem and the total size of the file (in most cases).

To get around this, I intend to replace the current approach with an algorithm that would identify images by filename and confirm them by comparing a [perceptual hash](https://pypi.org/project/ImageHash/) of *just* the image data, and accepting anything within a fairly small hashed distance. This would mean that files that are only changed slightly should still be recognized and not re-scanned. The point in using two passes (filename *and then* a hash of image data) is that hashing an image's contents is significantly more expensive than reading its filename or filesystem metadata.

## Overall Performance Optimization
The first pass over any given set of pictures is expected to be fairly slow, but any passes after the first one should generally be quite fast. This was true, but I noticed the application was slowing down as I fixed a couple of bugs that cropped up.

I intially used the built-in tool cProfile to identify where things were slowing down as I added the database code, but found that with a well-developed application (as opposed to a small script) the output was too noisy to be useful. I tried filtering it a bit in Excel, but stopped after seeing a recommendation from [an article](https://pythonspeed.com/articles/beyond-cprofile/) that recommended Pyinstrument. Pyinstrument gave me this output, which made it immediately obvious where my application was spending its time on a run where all the encodings can be pulled from the database:
```py
13.025 <module>  lits.py:16
├─ 10.781 main  lits.py:42
│  ├─ 10.350 update_image_attributes  Controllers\Database.py:126
│  │  └─ 10.342 [self]  
│  └─ 0.349 get_all_compatible_files  lits.py:199
│     └─ 0.348 <listcomp>  lits.py:204
│        └─ 0.348 __init__  Model\ImageFile.py:16
│           └─ 0.348 init_metadata  Model\ImageFile.py:54
│              └─ 0.235 read_exif  pyexiv2\core.py:38
│                    [2 frames hidden]  pyexiv2
└─ 2.103 <module>  Controllers\FaceRecognizer.py:2
   └─ 2.102 <module>  face_recognition\__init__.py:3
         [315 frames hidden]  face_recognition, face_recognition_mo...
```
I added a "dirty" tracker for the "unknown" files and only updating database attributes for files that I knew had changed. Below is the view after that change.  
<sub>Note: Pyinstrument is non-deterministic and won't always show exactly the same results for methods with low runtime, even though it will still be, broadly speaking, showing how long methods were running.<sub>

```py
2.697 <module>  lits.py:16
├─ 2.097 <module>  Controllers\FaceRecognizer.py:2
│  └─ 2.096 <module>  face_recognition\__init__.py:3
│        [325 frames hidden]  face_recognition, face_recognition_mo...
│           2.096 <module>  face_recognition\api.py:3
│           ├─ 1.980 [self]  
├─ 0.462 main  lits.py:42
│  ├─ 0.362 get_all_compatible_files  lits.py:199
│  │  └─ 0.361 <listcomp>  lits.py:204
│  │     └─ 0.360 __init__  Model\ImageFile.py:16
│  │        └─ 0.359 init_metadata  Model\ImageFile.py:54
│  │           ├─ 0.244 read_exif  pyexiv2\core.py:38
│  │           │     [5 frames hidden]  pyexiv2
│  │           └─ 0.110 __init__  pyexiv2\core.py:14
│  │                 [2 frames hidden]  pyexiv2
│  └─ 0.055 match_best  Controllers\FaceRecognizer.py:49
│     └─ 0.035 face_distance  face_recognition\api.py:63
│           [2 frames hidden]  face_recognition
└─ 0.110 <module>  numpy\__init__.py:106
      [127 frames hidden]  numpy, pathlib, urllib, collections, ...
```

For comparison, below is the same tree on a run where every image is new and thus needs to be encoded. Note that vast majority of time is spent on encoding, with a distant second-place going to writing the encodings into the database. There's not much that can be done to speed up the encoding, but reducing the number of times encodings are added would increase performance and prevent database size bloat. Adding a maintenance routine that would identify old image database entries would also help prevent bloat.

```py
128.642 <module>  lits.py:16
├─ 126.444 main  lits.py:42
│  ├─ 99.613 ensure_image_in_database  lits.py:177
│  │  ├─ 53.847 encode_faces  Controllers\FaceRecognizer.py:19
│  │  │  ├─ 46.096 face_encodings  face_recognition\api.py:203
│  │  │  │     [8 frames hidden]  face_recognition
│  │  │  │        44.110 _raw_face_locations  face_recognition\api.py:92
│  │  │  └─ 7.368 resize  PIL\Image.py:1838
│  │  │        [8 frames hidden]  PIL
│  │  └─ 45.494 add_image  Controllers\Database.py:99
│  │     ├─ 30.835 add_encoding  Controllers\Database.py:158
│  │     │  ├─ 16.037 get_or_associate_encoding  Controllers\Database.py:176
│  │     │  └─ 14.799 [self]  
│  │     └─ 14.659 [self]  
│  ├─ 13.607 update_image_attributes  Controllers\Database.py:126
│  └─ 12.112 get_or_associate_encoding  Controllers\Database.py:176
└─ 2.066 <module>  Controllers\FaceRecognizer.py:2
   └─ 2.065 <module>  face_recognition\__init__.py:3
         [328 frames hidden]  face_recognition, face_recognition_mo...
```
I loaded more data, bringing the test data set from 78 images to 510, and re-ran LITS. The profiler output for that run is below, but take note of the 352 seconds of "show dashboard" that are caused by it waiting on the user once everything else is complete. Removing that, we can see that the 432 additional pictures were encoded and added to the database in 445 seconds, a rate of ~1.0 images per second. Also note that the resize operation took 25% of that 452 seconds. This is explained partially by the bulk load of extra data being images straight from a Nikon D7100 and being 3-9MB in size.
```py
917.595 <module>  lits.py:16
└─ 915.088 main  lits.py:42
   ├─ 445.905 ensure_image_in_database  lits.py:181
   │  ├─ 343.901 encode_faces  Controllers\FaceRecognizer.py:19
   │  │  ├─ 218.451 face_encodings  face_recognition\api.py:203
   │  │  │     [8 frames hidden]  face_recognition
   │  │  │        216.538 _raw_face_locations  face_recognition\api.py:92
   │  │  └─ 123.011 resize  PIL\Image.py:1838
   │  │        [10 frames hidden]  PIL
   │  └─ 98.610 add_image  Controllers\Database.py:105
   │     ├─ 73.174 [self]  
   │     └─ 25.436 add_encoding  Controllers\Database.py:166
   │        ├─ 13.146 get_or_associate_encoding  Controllers\Database.py:184
   │        └─ 12.290 [self]  
   ├─ 352.076 show_dashboard  dashboard.py:17
   │  └─ 351.277 show  matplotlib\pyplot.py:307
   │        [1530 frames hidden]  matplotlib, tkinter, logging, numpy, ...
   │           351.265 mainloop  tkinter\__init__.py:1281
   │           ├─ 324.834 [self]  
   ├─ 83.185 update_image_attributes  Controllers\Database.py:134
   │  └─ 83.154 [self]  
   ├─ 21.103 get_all_compatible_files  lits.py:203
   │  └─ 21.098 <listcomp>  lits.py:208
   │     └─ 21.098 __init__  Model\ImageFile.py:18
   │        └─ 21.097 init_metadata  Model\ImageFile.py:56
   │           ├─ 11.687 __init__  pyexiv2\core.py:14
   │           │     [2 frames hidden]  pyexiv2
   │           └─ 9.408 read_exif  pyexiv2\core.py:38
   │                 [6 frames hidden]  pyexiv2
   └─ 11.010 get_or_associate_encoding  Controllers\Database.py:184
```

## Analysis and Debugging Tools
As this application uses SQLite, I initially looked at the contents of the database using Python's built-in `sqlite3` module, but later discovered [SQLite Tools](https://www.sqlite.org/download.html), a command-line interface that is made available by the SQLite project. This was very helpful in that it enabled me to run ad-hoc queries using standard SQL syntax and see the results without writing a couple lines of code each time.
A few days after I found SQLite Tools, I discovered [DBBrowser for SQLite](https://sqlitebrowser.org/), which has a GUI very reminiscent of SQL Server Management Studio, with which most Microsoft-stack database administrators and users will likely have decent familiarity.

## Model Refactors
I initially built my application as though it would work entirely in memory and simply write data to images. This would have worked very nicely in many ways, but unfortunately face encodings end up being too large to reliably put into any metadata tag without inventing my XMP namespace, which I'd still like to investigate at some later date.
Instead, LITS now applies keyword tags directly to the image's metadata, but face encodings are stored in the database so they don't need to be re-generated on each run, which is unfortunately somewhat slow.