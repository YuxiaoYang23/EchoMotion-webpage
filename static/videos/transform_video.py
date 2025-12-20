import os
import subprocess
import argparse
import tempfile
import shutil

def re_encode_video(input_path, overwrite=False):
    """
    Re-encodes a single video file to a web-compatible H.264 format using FFmpeg.
    If overwrite is True, it replaces the original file. Otherwise, it creates a new file.
    
    Args:
        input_path (str): Path to the input video file.
        overwrite (bool): If True, overwrite the original file.
    """
    print(f"Processing: {input_path}")
    
    if overwrite:
        # Use a temporary file for the output to avoid read/write conflicts
        temp_dir = tempfile.gettempdir()
        temp_output_path = os.path.join(temp_dir, f"temp_{os.path.basename(input_path)}")
        output_path_final = input_path
    else:
        # Create a new filename with '_new' suffix
        base, ext = os.path.splitext(input_path)
        output_path_final = f"{base}_new{ext}"
        temp_output_path = output_path_final

    command = [
        'ffmpeg',
        '-y',                  # Overwrite output file if it exists (important for temp file)
        '-i', input_path,      # Input file
        '-c:v', 'libx264',     # Video codec: H.264 (the web standard)
        '-pix_fmt', 'yuv420p',   # Pixel format for maximum compatibility
        '-preset', 'fast',     # Encoding speed vs. compression balance
        '-crf', '18',          # Constant Rate Factor (quality, 18 is visually lossless)
        '-movflags', '+faststart', # IMPORTANT: for web streaming
        '-an',                 # No audio
        temp_output_path
    ]
    
    try:
        # Run FFmpeg command, hide output unless there's an error
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        
        if overwrite:
            # Move the successfully re-encoded temp file to replace the original
            shutil.move(temp_output_path, output_path_final)
            print(f"SUCCESS: Overwrote original file -> {output_path_final}")
        else:
            print(f"SUCCESS: Saved re-encoded video to -> {output_path_final}")

    except subprocess.CalledProcessError as e:
        # Print error details if FFmpeg fails
        print(f"ERROR processing {input_path}:")
        print(f"  Return code: {e.returncode}")
        print(f"  Stderr: {e.stderr}")
        # Clean up temp file on error
        if overwrite and os.path.exists(temp_output_path):
            os.remove(temp_output_path)
    except FileNotFoundError:
        print("ERROR: ffmpeg command not found. Is FFmpeg installed and in your system's PATH?")
        # Exit the script if ffmpeg is not found
        exit()


def find_and_process_videos(root_dir, keyword="motion", overwrite=False):
    """
    Finds and re-encodes all .mp4 files containing a keyword in their names.
    
    Args:
        root_dir (str): The root directory to start searching from.
        keyword (str): The keyword to look for in the filenames.
        overwrite (bool): If True, overwrite the original files.
    """
    if not os.path.isdir(root_dir):
        print(f"Error: Directory '{root_dir}' not found.")
        return

    print(f"Starting to search for '*.mp4' files with '{keyword}' in '{root_dir}'...")
    if overwrite:
        print("WARNING: Overwrite mode is enabled. Original files will be replaced.")
    
    video_paths_to_process = []
    # First, collect all paths to avoid issues with directory walking
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith('.mp4') and keyword.lower() in filename.lower():
                # Avoid processing files that were already re-encoded ('_new.mp4')
                if not overwrite and filename.lower().endswith('_new.mp4'):
                    continue
                video_paths_to_process.append(os.path.join(dirpath, filename))
    
    if not video_paths_to_process:
        print("No matching video files found.")
        return

    print(f"Found {len(video_paths_to_process)} video(s) to process.")
    for path in video_paths_to_process:
        re_encode_video(path, overwrite=overwrite)
                
    print(f"\nProcessing complete.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Re-encode MP4 videos containing 'motion' for web compatibility.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('directory', 
                        help="The target directory to process.")
    parser.add_argument('--keyword', default='motion',
                        help="The keyword to search for in filenames (default: 'motion').")
    parser.add_argument('--overwrite', action='store_true',
                        help="Enable this flag to overwrite the original video files.\n"
                             "Without this flag, new files with '_new.mp4' suffix will be created.")
    
    args = parser.parse_args()
    
    find_and_process_videos(args.directory, args.keyword, args.overwrite)
