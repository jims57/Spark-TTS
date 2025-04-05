from audio_player import play_wav_file
import time

def play_all_wavs(wav_files, delay=2):  # delay in seconds between files
    for wav_path in wav_files:
        # Extract just the directory name (which appears to be the ID)
        wav_id = wav_path.split('/')[-2]  # Gets the parent directory name
        print(f"Playing: {wav_id}")
        
        # Play the wav file
        play_wav_file(wav_id)
        
        # Wait for a bit before playing the next file
        time.sleep(delay)

# Using the wav_files list from previous code
for wav_file in wav_files:
    print(f"Found: {wav_file}")

# Ask user if they want to play all files
response = input("Do you want to play all WAV files? (yes/no): ")
if response.lower() in ['yes', 'y']:
    play_all_wavs(wav_files)