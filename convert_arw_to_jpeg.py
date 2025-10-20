import rawpy
import imageio
import os
import argparse
from multiprocessing import Pool
from PIL import Image
import io

def process_file(arw_file, output_folder):
    # Generate the output JPEG file path
    file_name = os.path.basename(arw_file)
    jpeg_file_path = os.path.join(output_folder, os.path.splitext(file_name)[0] + '.jpg')

    # Read and convert the ARW file into memory
    with rawpy.imread(arw_file) as raw:
        rgb = raw.postprocess(use_camera_wb=True)

    # Convert the raw image to an in-memory file object using BytesIO
    img_data = io.BytesIO()
    imageio.imwrite(img_data, rgb, format="jpeg", quality=100)

    # Rewind the in-memory file object
    img_data.seek(0)

    # Open the in-memory image with Pillow directly from the BytesIO object
    with Image.open(img_data) as img:
        # Ensure no black lines by trimming any black edges
        img = img.crop(img.getbbox())

        # Rotate the image if necessary to ensure landscape orientation
        width, height = img.size
        if height > width:
            img = img.rotate(90, expand=True)
        
        # Resize the image to the desired size without stretching or adding borders
        target_size = (6192, 4128)
        img.thumbnail(target_size, Image.Resampling.LANCZOS)

        # Ensure the image exactly matches the target size by resizing and cropping to fit
        img = img.resize(target_size, Image.Resampling.LANCZOS)

        # Save the final JPEG
        img.save(jpeg_file_path, 'JPEG', quality=100, dpi=(260, 260))

    print(f"Converted {arw_file} to {jpeg_file_path}")

def convert_arw_to_jpeg(input_folder, output_folder, num_workers):
    # Find all ARW files in the input folder
    arw_files = [os.path.join(input_folder, f) for f in os.listdir(input_folder) if f.lower().endswith('.arw')]

    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Create a pool of workers to parallelize the conversion
    with Pool(processes=num_workers) as pool:
        pool.starmap(process_file, [(arw_file, output_folder) for arw_file in arw_files])

if __name__ == "__main__":
    # Setup argument parser
    parser = argparse.ArgumentParser(description="Convert ARW files to JPEG format")
    parser.add_argument("input_folder", type=str, help="Path to the folder containing ARW files")
    parser.add_argument("output_folder", type=str, help="Path to the folder where JPEG files will be saved")

    # Get number of workers from SLURM environment variable or default to CPU count
    num_workers = int(os.environ.get('SLURM_CPUS_ON_NODE', os.cpu_count()))

    # Convert ARW files in parallel
    args = parser.parse_args()
    convert_arw_to_jpeg(args.input_folder, args.output_folder, num_workers)