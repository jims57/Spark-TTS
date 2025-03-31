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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("spark-tts-api")

# Add the Spark-TTS module to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the module instead
from cli import inference

app = FastAPI(title="Spark-TTS API", description="API for Spark-TTS text-to-speech synthesis")

# Model and device configuration
MODEL_DIR = "pretrained_models/Spark-TTS-0.5B"
DEFAULT_SAVE_DIR = "example/results"
DEFAULT_PROMPT_TEXT = "吃燕窝就选燕之屋，本节目由26年专注高品质燕窝的燕之屋冠名播出。豆奶牛奶换着喝，营养更均衡，本节目由豆本豆豆奶特约播出。"
DEFAULT_PROMPT_SPEECH_PATH = "example/prompt_audio.wav"

# Global variables to store loaded models
global_model = None
global_device = None
global_is_half = None

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
    """Load model on startup to avoid loading it on each request"""
    global global_model, global_device, global_is_half
    
    logger.info("Initializing Spark-TTS API...")
    
    # Since we can't directly load the model here without the proper functions,
    # we'll initialize these variables but load the model during inference
    if torch.cuda.is_available():
        global_device = 0
        logger.info(f"CUDA is available. Using GPU: {torch.cuda.get_device_name(0)}")
    else:
        global_device = "cpu"
        logger.info("CUDA is not available. Using CPU.")
    
    global_model = None
    global_is_half = None

@app.post("/tts", response_model=TTSResponse)
async def tts(request: TTSRequest, background_tasks: BackgroundTasks):
    """
    Generate speech from text using Spark-TTS
    
    Parameters:
    - text: Text to synthesize
    - prompt_text: Optional prompt text
    - prompt_speech_path: Optional path to prompt audio file
    - save_dir: Optional directory to save generated audio
    """
    global global_model, global_device, global_is_half
    
    if global_model is None:
        raise HTTPException(status_code=500, detail="Model not loaded. Please wait for initialization.")
    
    logger.info(f"Processing TTS request: '{request.text}'")
    
    # Set up parameters
    prompt_text = request.prompt_text if request.prompt_text else DEFAULT_PROMPT_TEXT
    prompt_speech_path = request.prompt_speech_path if request.prompt_speech_path else DEFAULT_PROMPT_SPEECH_PATH
    save_dir = request.save_dir if request.save_dir else DEFAULT_SAVE_DIR
    
    # Make sure the save directory exists
    os.makedirs(save_dir, exist_ok=True)
    
    # Generate a unique filename based on timestamp
    timestamp = int(time.time())
    output_filename = f"tts_output_{timestamp}.wav"
    output_path = os.path.join(save_dir, output_filename)
    
    # Log inference parameters
    logger.info(f"Inference parameters:")
    logger.info(f"  - Text: {request.text}")
    logger.info(f"  - Prompt text: {prompt_text}")
    logger.info(f"  - Prompt speech path: {prompt_speech_path}")
    logger.info(f"  - Output path: {output_path}")
    logger.info(f"  - Using device: {global_device}")
    
    try:
        inference_start = time.time()
        logger.info("Synthesizing speech...")
        
        # Run inference using the same approach as demo.sh
        sys.argv = [
            "cli.inference",
            "--text", request.text,
            "--device", str(global_device),
            "--save_dir", save_dir,
            "--model_dir", MODEL_DIR,
            "--prompt_text", prompt_text,
            "--prompt_speech_path", prompt_speech_path
        ]
        
        inference.main()
        
        inference_time = time.time() - inference_start
        logger.info(f"Speech synthesized in {inference_time:.2f} seconds")
        
        # The output file will be in the save_dir with a timestamp
        output_path = os.path.join(save_dir, output_filename)
        
        return TTSResponse(
            audio_path=output_path,
            inference_time=inference_time,
            text=request.text
        )
    
    except Exception as e:
        logger.error(f"Error during speech synthesis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during speech synthesis: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=7860, reload=False)