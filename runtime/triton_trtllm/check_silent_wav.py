import argparse
import numpy as np
import wave
import sys

def is_wav_silent(wav_filename, threshold=0.01):
    """
    Check if a WAV file is silent based on a threshold.
    
    Args:
        wav_filename (str): Path to the WAV file
        threshold (float): Amplitude threshold below which audio is considered silent
                          (values between 0 and 1, where 0 is absolute silence)
    
    Returns:
        bool: True if the file is silent, False otherwise
    """
    try:
        with wave.open(wav_filename, 'rb') as wav_file:
            # Get basic info about the WAV file
            n_channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            n_frames = wav_file.getnframes()
            
            # Read all frames
            frames = wav_file.readframes(n_frames)
            
            # Convert bytes to numpy array based on sample width
            if sample_width == 1:  # 8-bit unsigned
                dtype = np.uint8
                max_value = 255
                offset = 128
            elif sample_width == 2:  # 16-bit signed
                dtype = np.int16
                max_value = 32767
                offset = 0
            elif sample_width == 3:  # 24-bit signed
                # Need to handle 24-bit specifically - will convert to 32-bit
                frames_np = np.frombuffer(frames, dtype=np.uint8)
                # Reshape to group bytes and handle endianness (assuming little-endian)
                frames_np = frames_np.reshape(-1, 3)
                audio_data = np.zeros(len(frames_np), dtype=np.int32)
                # Combine 3 bytes into a 24-bit integer, then sign-extend to 32-bit
                for i in range(3):
                    audio_data |= frames_np[:, i].astype(np.int32) << (i * 8)
                # Sign extension for 24-bit to 32-bit
                audio_data = np.where(audio_data & 0x800000, audio_data | ~0xFFFFFF, audio_data)
                max_value = 8388607  # 2^23 - 1
                # Normalize and check RMS
                audio_data = audio_data / max_value
                rms = np.sqrt(np.mean(audio_data**2))
                return rms < threshold
            elif sample_width == 4:  # 32-bit signed
                dtype = np.int32
                max_value = 2147483647
                offset = 0
            else:
                raise ValueError(f"Unsupported sample width: {sample_width}")
            
            # If we haven't returned for 24-bit case yet
            if sample_width != 3:
                audio_data = np.frombuffer(frames, dtype=dtype)
                # Convert to float for consistent processing
                audio_data = (audio_data.astype(float) - offset) / max_value
                
                # Calculate RMS value
                rms = np.sqrt(np.mean(audio_data**2))
                
                # Check if RMS is below threshold
                return rms < threshold
                
    except Exception as e:
        print(f"Error processing WAV file: {e}", file=sys.stderr)
        return None

def main():
    parser = argparse.ArgumentParser(description='Check if a WAV file is silent.')
    parser.add_argument('--wav-filename', required=True, help='Path to the WAV file to check')
    parser.add_argument('--threshold', type=float, default=0.01, 
                        help='Amplitude threshold below which audio is considered silent (default: 0.01)')
    
    args = parser.parse_args()
    
    result = is_wav_silent(args.wav_filename, args.threshold)
    
    if result is None:
        sys.exit(1)
    
    print(result)
    return result

if __name__ == "__main__":
    main() 