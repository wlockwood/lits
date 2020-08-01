# LITS: Local Image Tagging and Search
Locally-run CNN tagging for images. To eventually include faces, emotion, quality, and more.

LITS will scan all pictures found in a specified folder and apply face recognition to all supported file formats and keep track of which people are in which images by writing known, found people to the IPTC tags of a picture. This allows those pictures to be searched from photography library management tools such as Photoshop Lightroom.

**Supported** file formats: .jpg, .png.  
**Untested** but potentially functional formats: [everything Pillow can read](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html).  
**Unsupported** file formats: DNG and other raw files.

# Usage
After installation, run LITS from a command line in the following fashion:
`py lits.py -scanroot c:\pictures -known c:\pictures\lits-people [-db cache.db -tolerance 0.5]`

Future versions may include a graphical interface.

## `-scanroot` / Images to scan
`-scanroot` specifies the root of the folder structure where pictures are to be scanned for matches to the known people and, later, other features. If the scan root path includes the known image root, the known image root and all its subfolders will be ignored.

## `-known` / Known Image Root
`-known` specifies the root of the folder structure where identified people can be found. Inside should be any combination of:
* single pictures labeled with a name, such was `William Lockwood.jpg`
* folders labeled with a name, such as `William Lockwood`, under which one or more pictures for that person can be found. File names inside this named folder don't need to follow any special logic.

## `-db` / Database
`-db` specifies where the SQLite database will be stored. Defaults to be `lits.db` in the unknown image root.

In addition to writing directly to each image's metadata, LITS will build a database with much of this information in it so that it can quickly identify which files it's already encoded and not need to reprocess them. This significantly decreases the time it takes to update the tagging data when doing a delta after adding more pictures to the collection.

Future versions will enable the user to search the database directly.

## `-tolerance` / Face Matching Tolerance
`-tolerance` is optional and adjusts how strict face matches should be to be considered a match. 
This defaults to 0.6, and lower inputs (ex: 0.2) force stricter matches at the cost of more false negatives

# Install Manual 

Development environment is Windows, so installation assumes that. Installing in other environments should be doable with slight modifications that are left as an exercise to the Linux-using reader.

## Windows Install
1. Install CUDA: https://docs.nvidia.com/cuda/cuda-installation-guide-microsoft-windows/index.html
1. Install cuDNN: https://docs.nvidia.com/deeplearning/sdk/cudnn-install/index.html#download-windows
1. Install Python3 from https://www.python.org/downloads/.
   - This should already come with pip and virtualenv.
1. Create a virtual environment for your LITS install: `py -m venv env`
1. If you want GPU acceleration, otherwise skip:
    1. Install cmake: https://cmake.org/download/
    1. Clone and build dlib locally:
        ```
        git clone https://github.com/davisking/dlib.git
        cd dlib
        mkdir build
        cd build
        cmake .. -DDLIB_USE_CUDA=1 -DUSE_AVX_INSTRUCTIONS=1
        cmake --build .
        cd ..
        python setup.py install --yes USE_AVX_INSTRUCTIONS --yes DLIB_USE_CUDA
        ```
1. Install face_recognition: `pip install face_recognition`.
1. Install OpenCV: `pip install opencv-python`

