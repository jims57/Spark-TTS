import argparse
import os
from pathlib import Path
from IPython.display import Audio, display

def play_wav_file(filename):
    # Remove .wav extension if present
    filename = filename.replace('.wav', '')
    
    # Construct the full path - updated to use absolute path
    results_dir = Path('/root/Spark-TTS/results')  # Update this based on your root path
    wav_path = results_dir / filename / f"{filename}.wav"
    
    # Check if file exists
    if not wav_path.exists():
        print(f"Error: File {wav_path} not found!")
        return False
    
    try:
        # Create and display audio player in notebook with autoplay
        audio = Audio(str(wav_path), autoplay=True)
        display(audio)
        return True
    except Exception as e:
        print(f"Error playing file: {e}")
        return False

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Play WAV file from results folder')
    parser.add_argument('--filename', required=True, 
                      help='Filename without or with .wav extension (e.g., 50a6eb0f1eebb367478e332668736972 or 50a6eb0f1eebb367478e332668736972.wav)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Play the file
    play_wav_file(args.filename)

if __name__ == "__main__":
    main() 