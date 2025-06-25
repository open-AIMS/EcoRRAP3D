import rawpy  # pip install in environment in Anaconda Prompt before use (pip install rawpy imageio pillow)
import imageio
import os
import glob
from PIL import Image
import argparse
from multiprocessing import Pool
import io

def process_file(nef_file, output_folder):
    # Generate the output JPEG file path
    file_name = os.path.basename(nef_file)
    jpeg_file_path = os.path.join(output_folder, os.path.splitext(file_name)[0] + '.jpg')

    # Read and convert the NEF file into memory
    with rawpy.imread(nef_file) as raw:
        rgb = raw.postprocess(use_camera_wb=True)

    # Convert the raw image to an in-memory file object using BytesIO
    img_data = io.BytesIO()
    imageio.imwrite(img_data, rgb, format="jpeg", quality=100)

    # Rewind the in-memory file object
    img_data.seek(0)

    # Open the in-memory image with Pillow directly from the BytesIO object
    with Image.open(img_data) as img:
        # Resize the image to 8256 x 5504 pixels
        img = img.resize((8256, 5504), Image.Resampling.LANCZOS)
        # Set the DPI to 300 and save the JPEG in the output folder
        img.save(jpeg_file_path, 'JPEG', quality=100, dpi=(300, 300))

    print(f"Converted {nef_file} to {jpeg_file_path}")

def convert_nef_to_jpeg(input_folder, output_folder, num_workers):
    # Find all NEF files in the input folder
    nef_files = glob.glob(os.path.join(input_folder, '*.NEF'))

    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Create a pool of workers to parallelize the conversion
    with Pool(processes=num_workers) as pool:
        pool.starmap(process_file, [(nef_file, output_folder) for nef_file in nef_files])

if __name__ == "__main__":
    # Setup argument parser
    parser = argparse.ArgumentParser(description="Convert NEF files to JPEG format")
    parser.add_argument("input_folder", type=str, help="Path to the folder containing NEF files")
    parser.add_argument("output_folder", type=str, help="Path to the folder where JPEG files will be saved")

    # Get number of workers from SLURM environment variable or default to CPU count
    num_workers = int(os.environ.get('SLURM_CPUS_ON_NODE', os.cpu_count()))

    # Convert NEF files in parallel
    args = parser.parse_args()
    convert_nef_to_jpeg(args.input_folder, args.output_folder, num_workers)