import os
import time
import torch
import logging
import argparse
import hashlib
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn
import sys
import numpy as np
from pathlib import Path
import subprocess
from contextlib import asynccontextmanager
import librosa
import soundfile as sf

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize API and check CUDA availability"""
    logger.info("Initializing Spark-TTS API...")
    
    if torch.cuda.is_available():
        logger.info(f"CUDA is available. Using GPU: {torch.cuda.get_device_name(0)}")
    else:
        logger.info("CUDA is not available. Using CPU.")
    yield

app = FastAPI(
    title="Spark-TTS API", 
    description="API for Spark-TTS text-to-speech synthesis",
    lifespan=lifespan
)

# Model and device configuration
MODEL_DIR = "pretrained_models/Spark-TTS-0.5B"

class TTSRequest(BaseModel):
    text: str
    reference_text: Optional[str] = None
    reference_audio: Optional[str] = None
    save_dir: Optional[str] = None

class TTSResponse(BaseModel):
    errcode: int = 0
    message: str = "success"
    data: dict = {
        "inference_time": 0.0,
        "text": "",
        "saved_filename": ""
    }

@app.post("/tts", response_model=TTSResponse)
async def tts(request: TTSRequest, background_tasks: BackgroundTasks):
    """Generate speech from text using Spark-TTS"""
    logger.info(f"Processing TTS request: '{request.text}'")
    
    # Validate the input text
    if not request.text or len(request.text.strip()) < 5:
        raise HTTPException(status_code=400, detail="Text must be at least 5 characters long")
    
    # Add period if missing
    text = request.text.strip()
    # Check if text contains Chinese characters
    has_chinese = any('\u4e00' <= char <= '\u9fff' for char in text)
    
    if has_chinese:
        if not text.endswith('。'):
            text = text + '。'
            logger.info(f"Added Chinese period. Updated text: '{text}'")
    else:  # Assume English
        if not text.endswith('.'):
            text = text + '.'
            logger.info(f"Added English period. Updated text: '{text}'")
    
    request.text = text
    
    # Set up parameters with detailed logging
    if request.reference_text:
        reference_text = request.reference_text
        logger.info(f"Using provided reference text: {reference_text}")
    else:
        return TTSResponse(
            errcode=400,
            message="Reference text is required",
            data={
                "inference_time": 0.0,
                "text": request.text,
                "saved_filename": ""
            }
        )
    
    if request.reference_audio:
        reference_audio = request.reference_audio
        logger.info(f"Using provided reference audio: {reference_audio}")
    else:
        return TTSResponse(
            errcode=400,
            message="Reference audio is required",
            data={
                "inference_time": 0.0,
                "text": request.text,
                "saved_filename": ""
            }
        )
    
    if request.save_dir:
        save_dir = request.save_dir
        logger.info(f"Using provided save directory: {save_dir}")
    else:
        return TTSResponse(
            errcode=400,
            message="Save directory is required",
            data={
                "inference_time": 0.0,
                "text": request.text,
                "saved_filename": ""
            }
        )
    
    # Make sure the save directory exists
    os.makedirs(os.path.join(spark_tts_root, save_dir), exist_ok=True)
    
    try:
        inference_start = time.time()
        logger.info("Synthesizing speech...")
        
        # Define the file paths using absolute paths
        script_dir = os.path.dirname(os.path.abspath(__file__))
        client_script = os.path.join(script_dir, "client_http.py")
        output_path = os.path.join(spark_tts_root, save_dir, "output.wav")
        ref_audio_path = os.path.join(spark_tts_root, reference_audio)
        
        logger.info(f"Client script path: {client_script}")
        logger.info(f"Output audio path: {output_path}")
        logger.info(f"Reference audio path: {ref_audio_path}")
        
        # Check if client script exists
        if not os.path.exists(client_script):
            raise Exception(f"Client script not found at {client_script}")
        
        # Check if the reference audio exists
        if not os.path.exists(ref_audio_path):
            logger.warning(f"Reference audio file not found: {ref_audio_path}")
            return TTSResponse(
                errcode=400,
                message=f"Reference audio file not found: {reference_audio}",
                data={
                    "inference_time": 0.0,
                    "text": request.text,
                    "saved_filename": ""
                }
            )
        
        # Process reference audio - check if it's 16kHz mono and convert if needed
        processed_ref_audio_path = ref_audio_path
        try:
            # Check audio properties using librosa
            y, sr = librosa.load(ref_audio_path, sr=None, mono=False)
            
            # Log original audio properties
            channels = 1 if len(y.shape) == 1 else y.shape[0]
            logger.info(f"Reference audio properties: Sample rate: {sr} Hz, Channels: {channels}")
            
            # Check if conversion is needed (not 16kHz or not mono)
            if sr != 16000 or channels > 1:
                logger.warning(f"AUDIO CONVERSION NEEDED: '{ref_audio_path}' is not in 16kHz mono format")
                if sr != 16000:
                    logger.warning(f"SAMPLE RATE CONVERSION: Converting from {sr}Hz to 16000Hz")
                if channels > 1:
                    logger.warning(f"CHANNEL CONVERSION: Converting from {channels} channels to mono")
                
                # Create a processed version with _16k_mono suffix
                file_name, ext = os.path.splitext(ref_audio_path)
                processed_ref_audio_path = f"{file_name}_16k_mono{ext}"
                
                # Convert to mono if needed
                if channels > 1:
                    y = librosa.to_mono(y)
                    logger.info(f"Converted audio to mono")
                
                # Resample to 16kHz if needed
                if sr != 16000:
                    y = librosa.resample(y, orig_sr=sr, target_sr=16000)
                    logger.info(f"Resampled audio to 16kHz")
                
                # Save processed audio
                sf.write(processed_ref_audio_path, y, 16000, 'PCM_16')
                logger.warning(f"AUDIO CONVERSION COMPLETE: Saved 16kHz mono version to '{processed_ref_audio_path}'")
            else:
                logger.info("Reference audio is already in the correct format (16kHz mono)")
        except Exception as e:
            logger.error(f"ERROR DURING AUDIO CONVERSION: {str(e)}")
            logger.warning("Using the original reference audio file")
        
        # Run the command with python3 which is verified to work with English text
        cmd = [
            "python3",
            client_script,
            "--server-url", "localhost:9002",
            "--output-audio", output_path,
            "--reference-audio", processed_ref_audio_path,
            "--reference-text", reference_text,
            "--target-text", request.text
        ]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        # Run from the directory containing client_http.py
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=script_dir
        )
        
        # Log the output
        if process.stdout:
            logger.info(f"Process output: {process.stdout}")
        if process.stderr:
            logger.info(f"Process stderr: {process.stderr}")
        
        # Ignore KeyError: 'outputs' as it doesn't affect audio generation
        if process.returncode != 0 and "KeyError: 'outputs'" not in process.stderr:
            raise Exception(f"Error running client_http.py: {process.stderr}")
        
        # Use output.wav as the saved file since we specified it
        saved_filename = "output.wav"
        full_file_path = output_path
        
        inference_time = time.time() - inference_start
        logger.info(f"Speech synthesized in {inference_time:.2f} seconds")
        
        # Rename the file to MD5 format if a file was successfully generated
        md5_filename = saved_filename
        if os.path.exists(full_file_path):
            try:
                # Calculate MD5 hash of the audio file
                md5_hash = hashlib.md5()
                with open(full_file_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b''):
                        md5_hash.update(chunk)
                
                # Create new filename with MD5 hash
                file_ext = os.path.splitext(saved_filename)[1]
                md5_hash_str = md5_hash.hexdigest()
                md5_filename = f"{md5_hash_str}{file_ext}"
                
                # Create MD5 folder
                md5_folder_path = os.path.join(os.path.dirname(full_file_path), md5_hash_str)
                os.makedirs(md5_folder_path, exist_ok=True)
                logger.info(f"Created MD5 folder: {md5_folder_path}")
                
                # Generate the new full path inside the MD5 folder
                new_full_path = os.path.join(md5_folder_path, md5_filename)
                
                # Move the file to the MD5 folder
                os.rename(full_file_path, new_full_path)
                logger.info(f"File moved from {full_file_path} to {new_full_path}")
                
                # Create a text file in the MD5 folder with the input text
                txt_file_path = os.path.join(md5_folder_path, f"{md5_hash_str}.txt")
                with open(txt_file_path, 'w', encoding='utf-8') as txt_file:
                    txt_file.write(request.text)
                logger.info(f"Created text file with input content: {txt_file_path}")
            except Exception as e:
                logger.error(f"Error processing file with MD5 format: {e}")
                # Keep the original filename if processing fails
        
        return TTSResponse(
            errcode=0,
            message="success",
            data={
                "inference_time": inference_time,
                "text": request.text,
                "saved_filename": md5_filename
            }
        )
    
    except Exception as e:
        logger.error(f"Error during speech synthesis: {str(e)}")
        return TTSResponse(
            errcode=500,
            message=f"Error during speech synthesis: {str(e)}",
            data={
                "inference_time": 0.0,
                "text": request.text,
                "saved_filename": ""
            }
        )

if __name__ == "__main__":
    uvicorn.run("server-api:app", host="0.0.0.0", port=9003, reload=False)