import os
import sys
from tqdm import tqdm

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.asset_matting import HairAssetMatting

def main():
    raw_dir = os.path.join("app", "assets", "raw_hairstyles")
    cleaned_dir = os.path.join("app", "assets", "cleaned_hairstyles")
    
    if not os.path.exists(raw_dir):
        print(f"Error: {raw_dir} does not exist.")
        return
        
    if not os.path.exists(cleaned_dir):
        os.makedirs(cleaned_dir)
        
    # Walk through raw_dir to find all images including subdirectories
    all_tasks = []
    for root, dirs, files in os.walk(raw_dir):
        for filename in files:
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.avif')):
                input_path = os.path.join(root, filename)
                
                # Maintain subdirectory structure
                rel_path = os.path.relpath(root, raw_dir)
                dest_subdir = os.path.join(cleaned_dir, rel_path)
                
                if not os.path.exists(dest_subdir):
                    os.makedirs(dest_subdir)
                
                output_filename = os.path.splitext(filename)[0] + ".png"
                output_path = os.path.join(dest_subdir, output_filename)
                
                all_tasks.append((input_path, output_path, filename))
    
    if not all_tasks:
        print("No image files found in raw_hairstyles.")
        return
        
    print(f"Cleaning {len(all_tasks)} hairstyle assets...")
    
    # Initialize matting engine (singleton)
    matting_engine = HairAssetMatting()
    
    for input_path, output_path, filename in tqdm(all_tasks):
        try:
            matting_engine.extract_rgba(input_path, output_path)
        except Exception as e:
            print(f"Failed to process {filename}: {e}")
            
    print("Batch cleaning completed.")

if __name__ == "__main__":
    main()

