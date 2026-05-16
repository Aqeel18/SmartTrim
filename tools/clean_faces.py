import os
import sys
import cv2
import PIL.Image
import pillow_avif  # Ensure this is installed if possible, or use a fallback

def clean_faces():
    faces_dir = os.path.join("app", "assets", "faces")
    if not os.path.exists(faces_dir):
        print(f"Error: {faces_dir} does not exist.")
        return

    print("Cleaning face assets (converting to JPG)...")
    
    for root, dirs, files in os.walk(faces_dir):
        for filename in files:
            if filename.lower().endswith(('.avif', '.webp', '.png', '.jpeg', '.jpg')):
                input_path = os.path.join(root, filename)
                
                # Check if it's already a good JPG
                if filename.lower().endswith('.jpg'):
                    # Try reading with OpenCV
                    img = cv2.imread(input_path)
                    if img is not None:
                        continue
                
                print(f"Processing {filename}...")
                try:
                    # Use PIL for better format support including AVIF (with pillow-avif-plugin)
                    pil_img = PIL.Image.open(input_path).convert('RGB')
                    
                    # Save as JPG
                    output_filename = os.path.splitext(filename)[0] + ".jpg"
                    output_path = os.path.join(root, output_filename)
                    
                    pil_img.save(output_path, "JPEG", quality=95)
                    
                    # If we created a new file, we can optionally delete the old one
                    # but for testing let's keep it or just replace if same name
                    if output_path != input_path:
                        print(f"  Converted to {output_filename}")
                        # os.remove(input_path) # Uncomment to remove original
                except Exception as e:
                    print(f"  Failed to process {filename}: {e}")

if __name__ == "__main__":
    clean_faces()
