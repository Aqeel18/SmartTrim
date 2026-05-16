import os
import torch
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
from app.models.modnet import MODNet

class HairAssetMatting:
    _instance = None
    _model = None
    _device = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HairAssetMatting, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # 1. Detect GPU automatically
        if torch.cuda.is_available():
            self._device = torch.device("cuda")
        else:
            self._device = torch.device("cpu")
        
        print(f"Initializing HairAssetMatting on {self._device}...")

        # 2. Load Model
        # Assuming the weights are in app/models/modnet/
        ckpt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                 "app", "models", "modnet", "modnet_photographic_portrait_matting.ckpt")
        
        if not os.path.exists(ckpt_path):
            raise FileNotFoundError(f"MODNet weights not found at {ckpt_path}")

        # Initialize MODNet with MobileNetV2 backbone
        self._model = MODNet(backbone_pretrained=False)
        
        # The pretrained weights were saved with DataParallel, so we need to wrap the model
        self._model = nn.DataParallel(self._model)
        
        if torch.cuda.is_available():
            self._model = self._model.cuda()
            weights = torch.load(ckpt_path)
        else:
            weights = torch.load(ckpt_path, map_location=torch.device('cpu'))
            
        self._model.load_state_dict(weights)
        self._model.eval()
        
        # 3. Define transforms
        # Using (0.5, 0.5, 0.5) as per standard MODNet inference for this checkpoint
        self.transforms = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
        ])
        print("MODNet loaded successfully.")

    def extract_rgba(self, input_path, output_path):
        """
        Reads original image, runs MODNet, merges RGB + alpha, and saves as TRUE 4-channel PNG.
        """
        # Read image
        image = Image.open(input_path).convert('RGB')
        w, h = image.size
        
        # 2. Automatically resize images so BOTH sides are divisible by 32
        new_w = w - (w % 32)
        new_h = h - (h % 32)
        
        # Ensure we don't shrink to 0
        if new_w == 0: new_w = 32
        if new_h == 0: new_h = 32
        
        im_resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Prepare input
        tensor = self.transforms(im_resized)
        tensor = tensor.unsqueeze(0).to(self._device)
        
        # 4. Run inference safely with torch.no_grad()
        with torch.no_grad():
            # MODNet returns (matte, _) or just matte depending on mode. 
            # In eval mode with this checkpoint, forward(False) usually returns just matte?
            # Let's check the code or usage. 
            # usage: _, _, matte = modnet(input, True)
            _, _, matte = self._model(tensor, True)
            
        # 5. Produce a FLOAT alpha matte (0–1)
        matte = matte[0][0].cpu().numpy()
        
        # Post-processing (Allowed ONLY)
        # • Clamp values between 0–1
        matte = np.clip(matte, 0, 1)
        
        # • Remove near-zero noise (<0.02)
        matte[matte < 0.02] = 0
        
        # Resize matte back to original size to match RGB image
        matte_image = Image.fromarray((matte * 255).astype(np.uint8), mode='L')
        matte_image = matte_image.resize((w, h), Image.Resampling.LANCZOS)
        
        # Merge RGB + alpha
        # We use the original image for RGB to preserve maximum quality
        final_image = image.copy()
        final_image.putalpha(matte_image)
        
        # Save as TRUE 4-channel PNG
        final_image.save(output_path, "PNG")
        
        return output_path
