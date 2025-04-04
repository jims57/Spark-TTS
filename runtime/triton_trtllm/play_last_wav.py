import os
from pathlib import Path
from IPython.display import Audio, display, HTML
import glob
import argparse

def play_latest_audio(jupyter_mode=True):
    """
    Find and play the most recently generated audio in the results directory
    and display its associated text content.
    
    Args:
        jupyter_mode (bool): If True, displays formatted output in Jupyter notebook.
                           If False, prints plain text to console.
    """
    # Get the results directory path
    results_dir = Path('/root/Spark-TTS/results')
    
    # Find all subdirectories (MD5 folders) in results, excluding .ipynb_checkpoints
    md5_folders = [d for d in results_dir.glob('*') 
                  if d.is_dir() and d.name != '.ipynb_checkpoints']
    
    if not md5_folders:
        print("❌ No audio files found in results directory!")
        return
    
    # Get the most recent folder based on modification time
    latest_folder = max(md5_folders, key=lambda x: x.stat().st_mtime)
    md5_hash = latest_folder.name
    
    # Get the wav and txt files
    wav_file = latest_folder / f"{md5_hash}.wav"
    txt_file = latest_folder / f"{md5_hash}.txt"
    
    if not wav_file.exists() or not txt_file.exists():
        print(f"❌ Missing files in {md5_hash} folder!")
        return
    
    # Read the text content
    with open(txt_file, 'r', encoding='utf-8') as f:
        text_content = f.read().strip()
    
    if jupyter_mode:
        # Display information in a formatted way for Jupyter
        display(HTML(f"""
        <div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin: 10px 0;">
            <h3 style="color: #2c3e50; margin: 0 0 10px 0;">🎵 Latest Generated Audio</h3>
            <p><strong>📁 Folder:</strong> {md5_hash}</p>
            <p><strong>📝 Text Content:</strong> "{text_content}"</p>
        </div>
        """))
        
        # Create and display audio player in Jupyter
        print("▶️ Playing audio...")
        audio = Audio(str(wav_file), autoplay=True)
        display(audio)
    else:
        # Print information in console format
        print("\n=== Latest Generated Audio ===")
        print(f"📁 Folder: {md5_hash}")
        print(f"📝 Text Content: \"{text_content}\"")
        print(f"🎵 Audio file: {wav_file}")
        print("\nTo play this audio in Jupyter notebook, use:")
        print(f"from IPython.display import Audio, display")
        print(f"display(Audio('{wav_file}', autoplay=True))")

def main():
    parser = argparse.ArgumentParser(description='Play the latest generated audio file')
    parser.add_argument('--jupyter', action='store_true', 
                      help='Run in Jupyter notebook mode (default: False)')
    
    args = parser.parse_args()
    play_latest_audio(jupyter_mode=args.jupyter)

if __name__ == "__main__":
    main()