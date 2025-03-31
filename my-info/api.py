import os
import time
import torch
import logging
import argparse
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn
import sys
import numpy as np
from pathlib import Path
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("spark-tts-api")

# Add the Spark-TTS module to the path
spark_tts_root = "/root/Spark-TTS"
sys.path.append(spark_tts_root)

app = FastAPI(title="Spark-TTS API", description="API for Spark-TTS text-to-speech synthesis")

# Model and device configuration
MODEL_DIR = "pretrained_models/Spark-TTS-0.5B"
DEFAULT_SAVE_DIR = "example/results"
DEFAULT_PROMPT_TEXT = "吃燕窝就选燕之屋，本节目由26年专注高品质燕窝的燕之屋冠名播出。豆奶牛奶换着喝，营养更均衡，本节目由豆本豆豆奶特约播出。"
DEFAULT_PROMPT_SPEECH_PATH = "example/prompt_audio.wav"

class TTSRequest(BaseModel):
    text: str
    prompt_text: Optional[str] = None
    prompt_speech_path: Optional[str] = None
    save_dir: Optional[str] = None

class TTSResponse(BaseModel):
    audio_path: str
    inference_time: float
    text: str

@app.on_event("startup")
async def startup_event():
    """Initialize API and check CUDA availability"""
    logger.info("Initializing Spark-TTS API...")
    
    if torch.cuda.is_available():
        logger.info(f"CUDA is available. Using GPU: {torch.cuda.get_device_name(0)}")
    else:
        logger.info("CUDA is not available. Using CPU.")

@app.post("/tts", response_model=TTSResponse)
async def tts(request: TTSRequest, background_tasks: BackgroundTasks):
    """
    Generate speech from text using Spark-TTS
    """
    logger.info(f"Processing TTS request: '{request.text}'")
    
    # Validate the input text
    if not request.text or len(request.text.strip()) < 5:
        raise HTTPException(status_code=400, detail="Text must be at least 5 characters long")
    
    # Set up parameters
    prompt_text = request.prompt_text if request.prompt_text else DEFAULT_PROMPT_TEXT
    prompt_speech_path = request.prompt_speech_path if request.prompt_speech_path else DEFAULT_PROMPT_SPEECH_PATH
    save_dir = request.save_dir if request.save_dir else DEFAULT_SAVE_DIR
    
    # Make sure the save directory exists
    os.makedirs(os.path.join(spark_tts_root, save_dir), exist_ok=True)
    
    # Generate a unique filename based on timestamp
    timestamp = int(time.time())
    output_filename = f"{timestamp}.wav"
    output_path = os.path.join(save_dir, output_filename)
    abs_output_path = os.path.join(spark_tts_root, output_path)
    
    # Log inference parameters
    logger.info(f"Inference parameters:")
    logger.info(f"  - Text: {request.text}")
    logger.info(f"  - Prompt text: {prompt_text}")
    logger.info(f"  - Prompt speech path: {prompt_speech_path}")
    logger.info(f"  - Output path: {output_path}")
    logger.info(f"  - Using device: {'cuda' if torch.cuda.is_available() else 'cpu'}")
    
    try:
        # Try using the example text from the demo.sh script that we know works
        reference_text = "A beautiful melody is created note by note, each one essential to the whole."
        
        inference_start = time.time()
        logger.info("Synthesizing speech...")
        
        # Run the command using a command proven to work from demo.sh
        cmd = [
            "python", "-m", "cli.inference",
            "--text", request.text,
            "--device", "0" if torch.cuda.is_available() else "cpu",
            "--save_dir", save_dir,
            "--model_dir", MODEL_DIR,
            "--prompt_text", DEFAULT_PROMPT_TEXT,  # Use the full default prompt
            "--prompt_speech_path", prompt_speech_path
        ]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=spark_tts_root  # Run from Spark-TTS root directory
        )
        
        # Log the output
        if process.stdout:
            logger.info(f"Process output: {process.stdout}")
        if process.stderr:
            logger.error(f"Process error: {process.stderr}")
            
        if process.returncode != 0:
            # If it fails, try with the reference text that's known to work
            logger.warning(f"First attempt failed. Trying with reference text from demo.sh")
            
            # Try with the reference text
            cmd = [
                "python", "-m", "cli.inference",
                "--text", reference_text,
                "--device", "0" if torch.cuda.is_available() else "cpu",
                "--save_dir", save_dir,
                "--model_dir", MODEL_DIR,
                "--prompt_text", DEFAULT_PROMPT_TEXT,
                "--prompt_speech_path", prompt_speech_path
            ]
            
            logger.info(f"Running command with reference text: {' '.join(cmd)}")
            
            reference_process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=spark_tts_root
            )
            
            if reference_process.returncode != 0:
                raise Exception(f"Inference failed with reference text: {reference_process.stderr}")
            else:
                # If reference works but original doesn't, then it's an issue with the input text
                raise Exception(f"Input text is not compatible with the model. Error: {process.stderr}")
        
        inference_time = time.time() - inference_start
        logger.info(f"Speech synthesized in {inference_time:.2f} seconds")
        
        return TTSResponse(
            audio_path=abs_output_path,
            inference_time=inference_time,
            text=request.text
        )
    
    except Exception as e:
        logger.error(f"Error during speech synthesis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during speech synthesis: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=7860, reload=False)