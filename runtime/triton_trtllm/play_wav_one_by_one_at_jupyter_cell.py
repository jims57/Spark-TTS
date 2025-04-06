import os
from audio_player import play_wav_file
import time
import glob
import re
from IPython.display import display, HTML, Audio

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

def read_sorted_sentences_from_directory(directory):
    """Read all numbered text files and extract sentences with their numbers"""
    sentences = []
    
    # Find all txt files in the directory
    txt_files = glob.glob(os.path.join(directory, "*.txt"))
    
    # Sort text files numerically by their filename number
    txt_files.sort(key=lambda x: int(os.path.basename(x).split('.')[0]))
    
    for txt_file in txt_files:
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Find all sentences with numbers like "1. text" or "1.text"
                numbered_sentences = re.findall(r'(\d+)\.[\s]*(.*?)(?=\d+\.|$)', content, re.DOTALL)
                for num, sentence in numbered_sentences:
                    # Clean up the sentence
                    clean_sentence = sentence.strip()
                    if clean_sentence:
                        sentences.append((int(num), clean_sentence))
        except Exception as e:
            print(f"Error reading text file {txt_file}: {e}")
    
    # Sort by the extracted number
    sentences.sort(key=lambda x: x[0])
    return sentences

def get_corresponding_text(wav_path):
    """Find and read the corresponding text file for a wav file"""
    # Get the directory and filename
    directory = os.path.dirname(wav_path)
    wav_filename = os.path.basename(wav_path)
    
    # Extract MD5 hash from filename (remove .wav extension)
    md5_hash = wav_filename.split('.')[0]
    
    # First look for TXT file with same name
    txt_path = os.path.join(directory, f"{md5_hash}.txt")
    if os.path.exists(txt_path):
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            print(f"Error reading text file {txt_path}: {e}")
    
    # Check if we have a matching sentence ID from our sorted sentences
    # This is a fallback method if the exact txt file isn't found
    for num, text in sorted_sentences:
        # Create a simple hash of the text to compare (this is a simplistic approach)
        if str(num) in wav_filename:
            return text
    
    # If no text file is found, look through all txt files in the directory
    txt_files = glob.glob(os.path.join(directory, "*.txt"))
    for txt_file in txt_files:
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                text_content = f.read().strip()
                # You could add more sophisticated matching here
                return text_content
        except Exception as e:
            print(f"Error reading text file {txt_file}: {e}")
    
    # If no text file is found
    return "No corresponding text found"

def play_all_wavs(wav_files, delay=1):  # delay in seconds between files
    for wav_path in wav_files:
        # Extract filename for display
        wav_filename = os.path.basename(wav_path)
        
        # Get the corresponding text
        text_content = get_corresponding_text(wav_path)
        
        # Display the text and create a button for playing
        print(f"\n=== File: {wav_filename} ===")
        print(f"Text: {text_content}")
        
        # Create a button to play the audio file
        try:
            # Create a unique ID for each audio element
            audio_id = f"audio_{hash(wav_path) & 0xFFFFFFFF}"
            
            # Create an Audio widget with the wav file
            audio = Audio(filename=wav_path, autoplay=False)
            display(audio)
        except ImportError:
            print(f"Please install IPython to use the interactive play button.")
            print(f"Alternatively, you can play the file manually from: {wav_path}")

# Expand the ~ to full home directory path
results_dir = os.path.expanduser("~/Spark-TTS/results")
tts_done_sentences_dir = os.path.expanduser("~/Documents/GitHub/Spark-TTS/runtime/triton_trtllm/generated_sentences/tts_done_sentences")

# Load and sort all sentences from text files
sorted_sentences = read_sorted_sentences_from_directory(tts_done_sentences_dir)

# Find all WAV files
wav_files = find_wav_files(results_dir)

# Sort wav files by creation time (oldest first) as requested
wav_files.sort(key=get_file_creation_time)

# Print all found wav files
print(f"Found {len(wav_files)} WAV files:")
for i, wav_file in enumerate(wav_files):
    create_time = time.ctime(os.path.getctime(wav_file))
    print(f"{i+1}. {os.path.basename(wav_file)} (Created: {create_time})")

# Play all files without asking for confirmation
print("\nPlaying all WAV files from oldest to newest...")
play_all_wavs(wav_files)