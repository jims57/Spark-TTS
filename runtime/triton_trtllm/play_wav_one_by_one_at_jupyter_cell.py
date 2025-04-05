import os
from audio_player import play_wav_file
import time
import glob

def find_wav_files(directory):
    wav_files = []
    # Walk through all directories and files
    for root, dirs, files in os.walk(directory):
        # Find files with .wav extension (case insensitive)
        for file in files:
            if file.lower().endswith('.wav'):
                # Get full path of the wav file
                full_path = os.path.join(root, file)
                wav_files.append(full_path)
    return wav_files

def get_file_creation_time(file_path):
    """Get the creation time of a file for sorting purposes"""
    return os.path.getctime(file_path)

def get_corresponding_text(wav_path):
    """Find and read the corresponding text file for a wav file"""
    # Get the directory and filename
    directory = os.path.dirname(wav_path)
    wav_filename = os.path.basename(wav_path)
    
    # Find all txt files in the same directory
    txt_files = glob.glob(os.path.join(directory, "*.txt"))
    
    for txt_file in txt_files:
        # Read the content of the text file
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                text_content = f.read().strip()
                return text_content
        except Exception as e:
            print(f"Error reading text file {txt_file}: {e}")
    
    # If no text file is found
    return "No corresponding text found"

def play_all_wavs(wav_files, delay=1):  # delay in seconds between files
    for wav_path in wav_files:
        # Extract just the directory name (which appears to be the ID)
        wav_id = wav_path.split('/')[-2]  # Gets the parent directory name
        
        # Get the corresponding text
        text_content = get_corresponding_text(wav_path)
        
        # Display the text before playing
        print(f"\n=== Playing: {wav_id} ===")
        print(f"Text: {text_content}")
        
        # Play the wav file
        play_wav_file(wav_id)
        
        # Wait for a bit before playing the next file
        time.sleep(delay)

# Expand the ~ to full home directory path
results_dir = os.path.expanduser("~/Spark-TTS/results")
wav_files = find_wav_files(results_dir)

# Sort wav files by creation time (oldest first)
wav_files.sort(key=get_file_creation_time)

# Print all found wav files
print(f"Found {len(wav_files)} WAV files:")
for i, wav_file in enumerate(wav_files):
    create_time = time.ctime(os.path.getctime(wav_file))
    print(f"{i+1}. {wav_file} (Created: {create_time})")

# Play all files without asking for confirmation
print("\nPlaying all WAV files from oldest to newest...")
play_all_wavs(wav_files)