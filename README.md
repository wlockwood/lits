# LITS: Local Image Tagging and Search
Concept: Locally-run NN tagging for images. To eventually include faces, emotion, quality, and more.

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

