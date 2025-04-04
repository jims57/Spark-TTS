#!/usr/bin/env python3
import os
import sys
import glob
import json
import time
import argparse
import re
import requests
import subprocess
from pathlib import Path

def parse_arguments():
    parser = argparse.ArgumentParser(description='Process batches of sentences with TTS')
    parser.add_argument('--total-sentences', type=int, default=100,
                        help='Total number of sentences to process')
    parser.add_argument('--total_sentences_per_batch', type=int, default=10,
                        help='Number of sentences to generate in each batch')
    parser.add_argument('--reference-text', type=str, 
                        default="很多这样的人，而这样有个通病就是，很自信，甚至自负",
                        help='Reference text for TTS')
    parser.add_argument('--reference-audio', type=str, 
                        default="example/leijun.wav",
                        help='Reference audio file path')
    parser.add_argument('--save-dir', type=str, 
                        default="example/results",
                        help='Directory to save TTS output')
    parser.add_argument('--tts-api-url', type=str, 
                        default="http://localhost:9003/tts",
                        help='URL of the TTS API endpoint')
    return parser.parse_args()

def generate_sentences(total_sentences):
    """Generate sentences using AI and return the path to the generated file"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    generate_script = os.path.join(script_dir, "generate_sentences_by_ai.py")
    
    print(f"Generating {total_sentences} sentences...")
    result = subprocess.run(
        [sys.executable, generate_script, str(total_sentences)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Error generating sentences: {result.stderr}")
        return None
    
    # Extract the file path from the output
    generated_dir = os.path.join(script_dir, "generated_sentences")
    latest_file = max(
        glob.glob(os.path.join(generated_dir, "*.txt")),
        key=os.path.getctime,
        default=None
    )
    
    return latest_file

def process_sentences(file_path, tts_api_url, reference_text, reference_audio, save_dir):
    """Process each sentence in the file and send to TTS API"""
    print(f"Processing sentences from {file_path}")
    
    # Get file name for the done sentences file
    filename = os.path.basename(file_path)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    done_dir = os.path.join(script_dir, "generated_sentences", "tts_done_sentences")
    done_file = os.path.join(done_dir, filename)
    
    # Make sure the done directory exists
    os.makedirs(done_dir, exist_ok=True)
    
    # Read all sentences from the file at once to reduce IO
    with open(file_path, 'r', encoding='utf-8') as f:
        sentences = f.readlines()
    
    processed_count = 0
    
    for line in sentences:
        line = line.strip()
        if not line:
            continue
        
        # Extract the sentence by removing the number and dot prefix
        match = re.match(r'^(\d+\.\s+)(.*)', line)
        if match:
            prefix, sentence = match.groups()
            print(f"Processing: {line}")
            
            # Call the TTS API
            tts_request = {
                "text": sentence,
                "reference_text": reference_text,
                "reference_audio": reference_audio,
                "save_dir": save_dir
            }
            
            try:
                response = requests.post(
                    tts_api_url, 
                    headers={"Content-Type": "application/json"},
                    data=json.dumps(tts_request)
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    if response_data.get("errcode") == 0:
                        print(f"TTS successful: {sentence}")
                        
                        # Append the processed sentence to the done file
                        with open(done_file, 'a', encoding='utf-8') as f:
                            f.write(f"{line}\n")
                        
                        processed_count += 1
                    else:
                        print(f"TTS error: {response_data.get('message')}")
                else:
                    print(f"HTTP error: {response.status_code}")
                    print(response.text)
            
            except Exception as e:
                print(f"Exception during TTS processing: {str(e)}")
        else:
            print(f"Malformed sentence (no prefix): {line}")
    
    return processed_count

def main():
    args = parse_arguments()
    
    # Calculate number of batches
    num_batches = args.total_sentences // args.total_sentences_per_batch
    if args.total_sentences % args.total_sentences_per_batch != 0:
        num_batches += 1
    
    print(f"Starting TTS batch processing:")
    print(f"Total sentences: {args.total_sentences}")
    print(f"Sentences per batch: {args.total_sentences_per_batch}")
    print(f"Number of batches: {num_batches}")
    
    total_processed = 0
    
    for batch in range(1, num_batches + 1):
        print(f"\nProcessing batch {batch} of {num_batches}")
        
        # Generate sentences
        sentences_file = generate_sentences(args.total_sentences_per_batch)
        if not sentences_file:
            print("Failed to generate sentences, skipping batch")
            continue
        
        # Process sentences
        processed = process_sentences(
            sentences_file, 
            args.tts_api_url, 
            args.reference_text, 
            args.reference_audio, 
            args.save_dir
        )
        
        total_processed += processed
        print(f"Completed batch {batch}. Processed {processed} sentences in this batch.")
        print("----------------------------------------")
    
    print(f"\nAll batches completed. Total sentences processed: {total_processed}")

if __name__ == "__main__":
    main() 