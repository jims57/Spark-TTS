#!/bin/bash

nohup jupyter notebook --ip=0.0.0.0 --port=9000 --no-browser --allow-root --notebook-dir=~/ > /var/log/jupyter.log 2>&1 &
echo "Jupyter Notebook started in background on port 9000"

cd ~/Spark-TTS/runtime/triton_trtllm
nohup bash run.sh 3 3 > run.log 2>&1 &
echo "Spark-Triton-server HttpService is running in background on port 9002"

nohup python server-api.py > server.log 2>&1 &
echo "Spark-tts Restful api is running in background on port 9003"