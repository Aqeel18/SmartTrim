import cv2
import numpy as np
import os

class HairstyleTemplateLoader:
    """
    Handles loading, validation, and normalization of hairstyle template images.
    
    This class is responsible for preparing hairstyle assets for the overlay process.
    It ensures that templates are valid PNGs with alpha channels and normalizes
    them to a target size while preserving aspect ratio.
    """
    
    def __init__(self, assets_dir=None):
        """
        Initialize the loader with the directory containing hairstyle assets.
        
        Args:
            assets_dir (str, optional): Path to the hairstyles directory.
                                        Defaults to app/assets/cleaned_hairstyles relative to this file.
        """
        # Support multiple roots so newly added assets are discoverable
        current_dir = os.path.dirname(os.path.abspath(__file__))
        default_cleaned = os.path.abspath(os.path.join(current_dir, '..', 'assets', 'cleaned_hairstyles'))
        default_orig = os.path.abspath(os.path.join(current_dir, '..', 'assets', 'hairstyles'))
        default_raw = os.path.abspath(os.path.join(current_dir, '..', 'assets', 'raw_hairstyles'))

        # Backwards compatible single-dir init; otherwise we build a list of roots
        self.asset_roots = []
        if assets_dir is not None:
            self.asset_roots.append({'label': 'Cleaned', 'key': 'cleaned', 'path': os.path.abspath(assets_dir)})
        else:
            if os.path.isdir(default_cleaned):
                self.asset_roots.append({'label': 'Cleaned', 'key': 'cleaned', 'path': default_cleaned})
            if os.path.isdir(default_orig):
                self.asset_roots.append({'label': 'Original', 'key': 'orig', 'path': default_orig})
            if os.path.isdir(default_raw):
                self.asset_roots.append({'label': 'Raw', 'key': 'raw', 'path': default_raw})

        if not self.asset_roots:
            print("Warning: No hairstyle asset directories found.")

    def load_template(self, filename):
        """
        Load a hairstyle image from disk and verify its validity.
        Supports searching in subdirectories.
        
        Args:
            filename (str): Name of the file to load (e.g., 'style1.png' or 'men/quiff.png').
            
        Returns:
            numpy.ndarray: The loaded image in BGRA format.
            
        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the image format is invalid or missing alpha channel.
        """
        # Try each asset root using the provided filename (which may include subdirs)
        file_path = None
        for root_info in self.asset_roots:
            candidate = os.path.join(root_info['path'], filename)
            if os.path.exists(candidate):
                file_path = candidate
                break

        # If not found as provided, try by basename search across roots
        if file_path is None:
            base = os.path.basename(filename)
            for root_info in self.asset_roots:
                for root, dirs, files in os.walk(root_info['path']):
                    if base in files:
                        file_path = os.path.join(root, base)
                        break
                if file_path is not None:
                    break
        
        if file_path is None:
            roots_str = ", ".join([ri['path'] for ri in self.asset_roots])
            raise FileNotFoundError(f"Hairstyle template not found: {filename} in any of [{roots_str}]")
            
        # Load image with IMREAD_UNCHANGED to preserve alpha channel
        image = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
        
        if image is None:
            raise ValueError(f"Failed to load image: {filename}. File may be corrupted or format not supported.")
            
        # Check for alpha channel (expecting 4 channels: B, G, R, A)
        if len(image.shape) < 3 or image.shape[2] != 4:
            raise ValueError(f"Image {filename} does not have an alpha channel. Found {image.shape[2] if len(image.shape) >= 3 else 0} channels. Please use PNG with transparency.")
            
        return image

    def list_available_styles(self):
        """
        List all available hairstyles across known asset roots, grouped by category.
        
        Returns:
            dict: { 'category': [ { 'label': 'Display Name', 'value': 'path/to/file.ext', 'source': 'cleaned|orig|raw' } ] }
        """
        styles = {}

        for root_info in self.asset_roots:
            base_path = root_info['path']
            root_label = root_info['label']
            source_key = root_info['key']

            for root, dirs, files in os.walk(base_path):
                rel_path = os.path.relpath(root, base_path)
                inner_cat = "General" if rel_path == "." else rel_path
                category = f"{root_label} / {inner_cat}" if inner_cat != "General" else f"{root_label}"

                category_styles = []
                for f in files:
                    # Include common image extensions for discovery in UI strips.
                    # Processing later still requires PNG with alpha; non-PNGs are for preview/listing only.
                    ext = os.path.splitext(f)[1].lower()
                    if ext in ['.png', '.jpg', '.jpeg', '.webp']:
                        name_no_ext = os.path.splitext(f)[0]
                        label = name_no_ext.replace('_', ' ').replace('-', ' ').title()

                        value = f if rel_path == "." else os.path.join(rel_path, f).replace('\\', '/')

                        category_styles.append({
                            'label': label,
                            'value': value,
                            'source': source_key,
                        })

                if category_styles:
                    if category in styles:
                        styles[category].extend(category_styles)
                    else:
                        styles[category] = category_styles

        return styles

    def normalize_template(self, image, target_width):
        """
        Resize the template to a target width while preserving aspect ratio.
        
        Args:
            image (numpy.ndarray): The source image (BGRA).
            target_width (int): The desired width in pixels.
            
        Returns:
            numpy.ndarray: The resized image.
        """
        height, width = image.shape[:2]
        
        if width == 0:
             raise ValueError("Input image has 0 width.")

        # Calculate scale factor
        scale = target_width / float(width)
        target_height = int(height * scale)
        
        # Resize using INTER_AREA for high quality downscaling or INTER_LINEAR for upscaling
        interpolation = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
        resized_image = cv2.resize(image, (target_width, target_height), interpolation=interpolation)
        
        return resized_image

    def process_template(self, filename, target_width):
        """
        Orchestrate the loading, resizing, and splitting of a hairstyle template.
        
        Args:
            filename (str): Name of the hairstyle file.
            target_width (int): Width of the hair region to match.
            
        Returns:
            dict: structured data containing:
                - 'rgb': Normalized RGB image (numpy array)
                - 'alpha': Normalized Alpha mask (numpy array)
                - 'original_size': (width, height) tuple
                - 'new_size': (width, height) tuple
                - 'success': boolean
                - 'error': string (if failed)
        """
        try:
            # 1. Load and Verify
            original_image = self.load_template(filename)
            orig_h, orig_w = original_image.shape[:2]
            
            # 2. Normalize Size
            resized_image = self.normalize_template(original_image, target_width)
            new_h, new_w = resized_image.shape[:2]
            
            # 3. Split Channels
            # cv2.split is computationally efficient for small number of channels
            b, g, r, a = cv2.split(resized_image)
            
            # Merge BGR back to a 3-channel image
            rgb_image = cv2.merge([b, g, r])
            
            # Alpha is already separated as 'a'
            
            return {
                'success': True,
                'rgb': rgb_image,
                'alpha': a,
                'original_size': (orig_w, orig_h),
                'new_size': (new_w, new_h)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Global instance for convenient import
hairstyle_loader = HairstyleTemplateLoader()
