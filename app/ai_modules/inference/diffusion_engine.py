import torch
import cv2
import numpy as np
from PIL import Image
from diffusers import StableDiffusionInpaintPipeline
import os

class DiffusionEngine:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pipeline = None
        self.model_id = "runwayml/stable-diffusion-inpainting"
        self.is_loaded = False
        
        print(f"[DiffusionEngine] Device: {self.device.upper()}")
        if self.device == "cpu":
            print("[DiffusionEngine] No GPU detected. Will use template-based overlay pipeline instead.")
        
    def load_model(self):
        if self.is_loaded:
            return
        
        if self.device == "cpu":
            # Don't attempt to load the massive diffusion model on CPU
            print("[DiffusionEngine] Skipping model load on CPU — template overlay will be used.")
            self.is_loaded = True
            return
            
        print(f"Loading Diffusion Inpainting Model ({self.model_id}) on {self.device}...")
        try:
            self.pipeline = StableDiffusionInpaintPipeline.from_pretrained(
                self.model_id,
                torch_dtype=torch.float16,
                safety_checker=None,
                requires_safety_checker=False,
            )
            self.pipeline = self.pipeline.to(self.device)
            
            try:
                self.pipeline.enable_xformers_memory_efficient_attention()
            except Exception:
                pass
            self.pipeline.enable_attention_slicing()
            
            self.is_loaded = True
            print("Diffusion model loaded successfully.")
        except Exception as e:
            print(f"Failed to load diffusion model: {e}")
            self.is_loaded = True  # Mark as loaded so we don't retry

    def generate_hair(self, face_image: np.ndarray, hair_mask: np.ndarray, target_style_name: str) -> np.ndarray:
        """
        Generates a realistic hairstyle using Stable Diffusion inpainting.
        Only works on GPU. On CPU, raises RuntimeError so the caller
        falls back to the deterministic template warp+overlay pipeline.
        """
        if not self.is_loaded:
            self.load_model()
        
        # No GPU / no pipeline → let the caller use the template overlay fallback
        if self.pipeline is None:
            raise RuntimeError("Diffusion model not available (no GPU). Use template overlay fallback.")

        # GPU path: full Stable Diffusion inpainting
        face_rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
        init_image = Image.fromarray(face_rgb).convert("RGB")
        
        kernel = np.ones((5, 5), np.uint8)
        dilated_mask = cv2.dilate(hair_mask, kernel, iterations=2)
        mask_image = Image.fromarray(dilated_mask).convert("L")

        prompt = f"photorealistic male hairstyle, {target_style_name}, matching skin tone and lighting, natural hair texture, 8k"
        negative_prompt = "cartoon, fake, disfigured, watermark, text, poorly blended"

        print(f"[GPU Mode] Diffusing: '{target_style_name}'...")
        
        generator = torch.Generator(device=self.device).manual_seed(42)
        
        result = self.pipeline(
            prompt=prompt,
            negative_prompt=negative_prompt,
            image=init_image,
            mask_image=mask_image,
            num_inference_steps=8,
            guidance_scale=7.0,
            generator=generator,
        ).images[0]

        result_bgr = cv2.cvtColor(np.array(result), cv2.COLOR_RGB2BGR)
        return result_bgr
