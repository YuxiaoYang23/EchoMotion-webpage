import os
import subprocess
import argparse
import tempfile
import shutil

def crop_video_top_half(input_path, overwrite=False):
    """
    Crops a video to its top half and re-encodes it using FFmpeg.
    
    Args:
        input_path (str): Path to the input video file.
        overwrite (bool): If True, overwrite the original file.
    """
    print(f"Processing: {input_path}")
    
    if overwrite:
        # Use a temporary file to avoid read/write conflicts
        temp_dir = tempfile.gettempdir()
        temp_output_path = os.path.join(temp_dir, f"temp_crop_{os.path.basename(input_path)}")
        output_path_final = input_path
    else:
        # Create a new filename with '_cropped' suffix
        base, ext = os.path.splitext(input_path)
        output_path_final = f"{base}_cropped{ext}"
        temp_output_path = output_path_final
        
    # FFmpeg command with the 'crop' filter
    # crop=iw:ih/2:0:0  (width:height:x:y)
    # iw:    input width (keep original width)
    # ih/2:  input height divided by 2 (take top half)
    # 0:     x-coordinate of the top-left corner (start from the left edge)
    # 0:     y-coordinate of the top-left corner (start from the top edge)
    command = [
        'ffmpeg',
        '-y',                  # Overwrite output file if it exists
        '-i', input_path,      # Input file
        '-vf', 'crop=iw:ih/2:0:0', # The cropping filter
        '-c:v', 'libx264',     # Re-encode with H.264 for compatibility
        '-pix_fmt', 'yuv420p',   # Standard pixel format
        '-preset', 'fast',
        '-crf', '18',
        '-movflags', '+faststart',
        '-an',                 # No audio
        temp_output_path
    ]

    try:
        # Run FFmpeg command, hide output unless there's an error
        result = subprocess.run(command, check=True, capture_output=True, text=True)

        if overwrite:
            # Move the successfully cropped temp file to replace the original
            shutil.move(temp_output_path, output_path_final)
            print(f"SUCCESS: Cropped and overwrote original file -> {output_path_final}")
        else:
            print(f"SUCCESS: Saved cropped video to -> {output_path_final}")

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
        exit()


def find_and_crop_videos(root_dir, exclude_keyword="motion", overwrite=False):
    """
    Finds and crops all .mp4 files that DO NOT contain a specific keyword.
    
    Args:
        root_dir (str): The root directory to start searching from.
        exclude_keyword (str): The keyword to exclude from filenames.
        overwrite (bool): If True, overwrite the original files.
    """
    if not os.path.isdir(root_dir):
        print(f"Error: Directory '{root_dir}' not found.")
        return

    print(f"Starting to search for '*.mp4' files without '{exclude_keyword}' in '{root_dir}'...")
    if overwrite:
        print("WARNING: Overwrite mode is enabled. Original files will be replaced.")

    video_paths_to_process = []
    # First, collect all paths to avoid issues with directory walking
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            # Check if the file is an mp4 and does NOT contain the exclude keyword
            if filename.lower().endswith('.mp4') and exclude_keyword.lower() not in filename.lower():
                # Avoid processing files that were already cropped ('_cropped.mp4')
                if not overwrite and filename.lower().endswith('_cropped.mp4'):
                    continue
                video_paths_to_process.append(os.path.join(dirpath, filename))

    if not video_paths_to_process:
        print("No matching video files found to crop.")
        return

    print(f"Found {len(video_paths_to_process)} video(s) to process.")
    for path in video_paths_to_process:
        crop_video_top_half(path, overwrite=overwrite)
    
    print("\nProcessing complete.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Crop the top half of MP4 videos that do not contain 'motion' in their name.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('directory', 
                        help="The target directory to process.")
    parser.add_argument('--exclude', default='motion',
                        help="The keyword to exclude from filenames (default: 'motion').")
    parser.add_argument('--overwrite', action='store_true',
                        help="Enable this flag to overwrite the original video files.\n"
                             "Without this flag, new files with '_cropped.mp4' suffix will be created.")

    args = parser.parse_args()
    
    find_and_crop_videos(args.directory, args.exclude, args.overwrite)
