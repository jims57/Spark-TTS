import argparse
import os
from pathlib import Path
from IPython.display import Audio, display

"""
Usage:
1. In Jupyter Notebook:
   from audio_player import play_wav_file
   
   # Play audio with filename only
   play_wav_file('57987919c743a2d12e744b0e2c5074a1')
   
   # Or with .wav extension
   play_wav_file('57987919c743a2d12e744b0e2c5074a1.wav')

2. From Command Line:
   # Run from terminal
   python audio_player.py --filename 57987919c743a2d12e744b0e2c5074a1
   
   # Or with .wav extension
   python audio_player.py --filename 57987919c743a2d12e744b0e2c5074a1.wav

File Structure:
- The script expects WAV files to be in: /root/Spark-TTS/results/<filename>/<filename>.wav
- Example path: /root/Spark-TTS/results/57987919c743a2d12e744b0e2c5074a1/57987919c743a2d12e744b0e2c5074a1.wav

Returns:
- True: if audio file is found and player is displayed
- False: if file not found or error occurs

Note:
- Best used in Jupyter Notebook for interactive audio playback
- Automatically displays audio player widget with play/pause controls
- Autoplay is enabled by default
"""

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