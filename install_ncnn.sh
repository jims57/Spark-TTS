#!/bin/bash
# Script to install NCNN with PNNX support

set -e  # Exit on error

# Install to home directory
cd $HOME

# Create and enter open-source directory
mkdir -p open-source
cd open-source

# Clone NCNN repository and initialize submodules
git clone https://github.com/csukuangfj/ncnn
cd ncnn
git submodule update --recursive --init

# Install dependencies
sudo apt update
sudo apt install -y cmake g++

# Build NCNN with Python support
mkdir -p build-wheel
cd build-wheel
cmake -DCMAKE_BUILD_TYPE=Release -DNCNN_PYTHON=ON -DNCNN_BUILD_BENCHMARK=OFF -DNCNN_BUILD_EXAMPLES=OFF -DNCNN_BUILD_TOOLS=ON ..
make -j6

# Setup environment variables
cd ~/open-source/ncnn
export PYTHONPATH=$PWD/python:$PYTHONPATH
export PATH=$PWD/tools/pnnx/build/src:$PATH
export PATH=$PWD/build-wheel/tools/quantize:$PATH

# Install CUDNN using conda
conda install -c conda-forge -y cudnn

# Build PNNX (PyTorch Neural Network Exchange)
cd ~/open-source/ncnn/tools/pnnx
mkdir -p build
cd build
rm -rf *  # Clean build directory

# Configure and build PNNX with CUDNN and PyTorch
cmake .. \
    -DCUDNN_INCLUDE_PATH=/root/miniconda3/envs/pnnx/include \
    -DCUDNN_LIBRARY_PATH=/root/miniconda3/envs/pnnx/lib/python3.8/site-packages/torch/lib \
    -DTorch_DIR=/root/miniconda3/envs/pnnx/lib/python3.8/site-packages/torch/share/cmake \
    -DPython3_EXECUTABLE=/root/miniconda3/envs/pnnx/bin/python
make -j6

# Install kaldifeat
cd ~/open-source
wget https://huggingface.co/csukuangfj/kaldifeat/resolve/main/cuda/1.25.5.dev20241029/linux/kaldifeat-1.25.5.dev20250203+cuda11.6.torch1.13.0-cp38-cp38-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
pip install kaldifeat-1.25.5.dev20250203+cuda11.6.torch1.13.0-cp38-cp38-manylinux_2_17_x86_64.manylinux2014_x86_64.whl

# Add environment variables to .bashrc for persistence
echo 'export PYTHONPATH=$HOME/open-source/ncnn/python:$PYTHONPATH' >> $HOME/.bashrc
echo 'export PATH=$HOME/open-source/ncnn/tools/pnnx/build/src:$PATH' >> $HOME/.bashrc
echo 'export PATH=$HOME/open-source/ncnn/build-wheel/tools/quantize:$PATH' >> $HOME/.bashrc

echo "Installation completed successfully!" 