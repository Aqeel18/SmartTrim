import os
import sys
from PIL import Image
from tqdm import tqdm

def main():
    raw_dir = os.path.join("app", "assets", "raw_hairstyles")
    cleaned_dir = os.path.join("app", "assets", "cleaned_hairstyles")
    output_dir = os.path.join("test_images", "matting_validation")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    files = [f for f in os.listdir(raw_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not files:
        print("No image files found in raw_hairstyles.")
        return
        
    print("Generating validation images...")
    
    for filename in tqdm(files):
        raw_path = os.path.join(raw_dir, filename)
        cleaned_filename = os.path.splitext(filename)[0] + ".png"
        cleaned_path = os.path.join(cleaned_dir, cleaned_filename)
        
        if not os.path.exists(cleaned_path):
            print(f"Warning: Cleaned version not found for {filename}")
            continue
            
        # Load images
        original = Image.open(raw_path).convert('RGB')
        cleaned = Image.open(cleaned_path).convert('RGBA')
        
        # Resize original to match cleaned if necessary
        if original.size != cleaned.size:
            original = original.resize(cleaned.size, Image.Resampling.LANCZOS)
            
        # Extract Alpha Matte (Grayscale)
        alpha = cleaned.split()[3]
        alpha_rgb = alpha.convert('RGB')
        
        # Extracted Hair (Composite over black to see details)
        background = Image.new('RGB', cleaned.size, (0, 0, 0))
        background.paste(cleaned, mask=alpha)
        extracted_hair_rgb = background
        
        # Concatenate [ Original | Alpha Matte | Extracted Hair ]
        w, h = original.size
        combined = Image.new('RGB', (w * 3, h))
        combined.paste(original, (0, 0))
        combined.paste(alpha_rgb, (w, 0))
        combined.paste(extracted_hair_rgb, (w * 2, 0))
        
        # Save
        save_path = os.path.join(output_dir, f"val_{cleaned_filename}")
        combined.save(save_path)
        
    print("Validation images generated.")

if __name__ == "__main__":
    main()
