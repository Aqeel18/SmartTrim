import torch
import torchvision.transforms as transforms
import cv2
import numpy as np
import os
from app.models.bisenet.model import BiSeNet

class HairSegmenter:
    """
    Hair segmentation module using pretrained BiSeNet.
    Extracts binary hair mask from face images.
    """

    def __init__(self, model_path=None, device=None):
        """
        Initialize the hair segmenter.

        Args:
            model_path (str, optional): Path to pretrained BiSeNet weights.
            device (str, optional): 'cuda' or 'cpu'. Auto-detects if None.
        """
        self.device = device if device else ('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Default model path relative to this file
        if model_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.model_path = os.path.join(current_dir, '..', 'models', 'bisenet', '79999_iter.pth')
        else:
            self.model_path = model_path

        self.n_classes = 19  # BiSeNet for face parsing typically has 19 classes
        self.net = BiSeNet(n_classes=self.n_classes)
        
        # Load weights
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model weights not found at {self.model_path}. Please download 79999_iter.pth.")

        try:
            # Use map_location to handle CPU/GPU mismatch
            checkpoint = torch.load(self.model_path, map_location=self.device)
            
            # Handle dictionary state_dict vs direct model save
            if isinstance(checkpoint, dict) and 'state_dict' in checkpoint:
                self.net.load_state_dict(checkpoint['state_dict'])
            elif isinstance(checkpoint, dict):
                 # Assume it's the state_dict itself
                self.net.load_state_dict(checkpoint, strict=True)
            else:
                 # Unexpected format
                raise ValueError(f"Unexpected checkpoint format in {self.model_path}")
                
        except Exception as e:
            raise RuntimeError(f"Failed to load model weights: {e}")

        self.net.to(self.device)
        self.net.eval()

        # Preprocessing transforms: Standard ImageNet normalization
        self.to_tensor = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)),
        ])

    def segment_hair(self, image_bgr):
        """
        Perform hair segmentation on a BGR image.

        Args:
            image_bgr (numpy.ndarray): Input image in BGR format.

        Returns:
            numpy.ndarray: Binary hair mask (0 or 255) of same (H, W) as input.
        """
        if image_bgr is None:
            raise ValueError("Input image is None")

        h, w = image_bgr.shape[:2]
        
        # 1. Preprocess
        # Resize to 512x512 for inference (standard for face parsing models)
        img_resized = cv2.resize(image_bgr, (512, 512))
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        
        img_tensor = self.to_tensor(img_rgb)
        img_tensor = torch.unsqueeze(img_tensor, 0)
        img_tensor = img_tensor.to(self.device)

        # 2. Inference
        with torch.no_grad():
            out, _, _ = self.net(img_tensor)
            # Output shape: [1, 19, 512, 512]
            parsing = out.squeeze(0).cpu().numpy().argmax(0)
            # parsing shape: (512, 512) with class indices

        # 3. Extract Hair Class
        # Class 17 is typically hair in CelebAMask-HQ / BiSeNet face parsing
        # Adjust if using a different dataset mapping
        hair_class_index = 17 
        hair_mask = np.zeros_like(parsing).astype(np.uint8)
        hair_mask[parsing == hair_class_index] = 255

        # 4. Postprocess
        # Resize mask back to original resolution
        # Use INTER_NEAREST to keep binary values clean, or INTER_LINEAR + threshold
        full_mask = cv2.resize(hair_mask, (w, h), interpolation=cv2.INTER_NEAREST)

        return full_mask
