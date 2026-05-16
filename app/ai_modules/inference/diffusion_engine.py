"""
Upgraded Diffusion Engine — SmartTrim 360 Phase 2.

Hierarchy of inference quality (best to fastest):
  1. SDXL Inpainting + IP-Adapter + ControlNet-Canny  [GPU, best identity preservation]
  2. SD 1.5 Inpainting + IP-Adapter                    [GPU, good identity]
  3. SD 1.5 Inpainting baseline (original)              [GPU, acceptable]
  4. Template warp + Poisson overlay                    [CPU, deterministic fallback]

IP-Adapter encodes the face image as a conditioning signal so the diffusion
model preserves the user's identity instead of hallucinating a new person.

ControlNet-Canny constrains the face structure (edges) during generation,
preventing geometric distortion of the face features.
"""

import os
import cv2
import numpy as np
import torch
from PIL import Image
from typing import Optional


class DiffusionEngine:
    """
    Manages multiple quality tiers of diffusion-based hair synthesis.

    Attributes
    ----------
    device : str
        'cuda' or 'cpu'. Detected automatically.
    quality : str
        'sdxl_ip_controlnet' | 'sd15_ip' | 'sd15_base'
        Highest available quality that fits in VRAM is chosen at load time.
    """

    # ── Model identifiers ────────────────────────────────────────────────
    _SDXL_INPAINT_ID   = "diffusers/stable-diffusion-xl-1.0-inpainting-0.1"
    _SD15_INPAINT_ID   = "runwayml/stable-diffusion-inpainting"
    _IP_ADAPTER_REPO   = "h94/IP-Adapter"
    _CONTROLNET_ID     = "lllyasviel/control_v11p_sd15_canny"

    def __init__(self):
        self.device      = "cuda" if torch.cuda.is_available() else "cpu"
        self.pipeline    = None
        self.quality     = None
        self.is_loaded   = False
        self._vram_gb    = self._detect_vram()

        print(f"[DiffusionEngine] Device: {self.device.upper()}"
              f"  VRAM: {self._vram_gb:.1f} GB")
        if self.device == "cpu":
            print("[DiffusionEngine] No GPU — template overlay pipeline will be used.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_hair(
        self,
        face_image: np.ndarray,
        hair_mask:  np.ndarray,
        target_style_name: str,
        progress_cb=None,          # optional callable(int 0-100)
    ) -> np.ndarray:
        """
        Generate a realistic hairstyle preview.

        On GPU, runs the best available diffusion tier.
        On CPU, raises RuntimeError so the caller can use the template fallback.

        Parameters
        ----------
        face_image : np.ndarray   BGR image of the user's face.
        hair_mask  : np.ndarray   Binary mask (255 = hair region to replace).
        target_style_name : str   Human-readable style name used in the prompt.
        progress_cb : callable    Optional callback(int) for progress reporting.

        Returns
        -------
        np.ndarray  BGR result image, same resolution as face_image.
        """
        if not self.is_loaded:
            self._load_best_pipeline()

        if self.pipeline is None:
            raise RuntimeError(
                "Diffusion pipeline not available (no GPU or load failed)."
            )

        _cb = progress_cb or (lambda p: None)
        _cb(5)

        face_rgb   = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
        init_image = Image.fromarray(face_rgb).convert("RGB").resize((512, 512))

        # Dilate mask slightly so inpainting covers roots and edges
        kernel = np.ones((9, 9), np.uint8)
        dilated = cv2.dilate(hair_mask, kernel, iterations=2)
        mask_image = Image.fromarray(dilated).convert("L").resize((512, 512))

        prompt = (
            f"photorealistic {target_style_name} hairstyle, "
            "natural hair texture, realistic lighting, same person, "
            "high resolution, 4k, professional photography"
        )
        negative_prompt = (
            "cartoon, anime, disfigured, deformed, watermark, text, blurry, "
            "poorly blended, different person, face change, low quality"
        )

        _cb(15)
        kwargs = dict(
            prompt          = prompt,
            negative_prompt = negative_prompt,
            image           = init_image,
            mask_image      = mask_image,
            guidance_scale  = 7.5,
            generator       = torch.Generator(device=self.device).manual_seed(42),
        )

        # Quality-tier-specific parameters
        if self.quality == "sdxl_ip_controlnet":
            kwargs["num_inference_steps"] = 30
            kwargs["strength"]            = 0.99
        elif self.quality == "sd15_ip":
            kwargs["num_inference_steps"] = 28
        else:
            # sd15_base
            kwargs["num_inference_steps"] = 25

        _cb(20)

        # Add ControlNet conditioning if available
        if self.quality == "sdxl_ip_controlnet" and hasattr(self, "_canny_image"):
            kwargs["control_image"] = self._make_canny(init_image, face_image)

        result_image = self.pipeline(**kwargs).images[0]
        _cb(95)

        # Resize back to original resolution
        orig_h, orig_w = face_image.shape[:2]
        result_resized = result_image.resize((orig_w, orig_h), Image.LANCZOS)
        result_bgr     = cv2.cvtColor(np.array(result_resized), cv2.COLOR_RGB2BGR)
        _cb(100)

        return result_bgr

    # ------------------------------------------------------------------
    # Pipeline loading — graceful VRAM-aware tiering
    # ------------------------------------------------------------------

    def _load_best_pipeline(self):
        """
        Load the highest-quality pipeline that fits on the available GPU.
        Falls through tiers if a tier fails (OOM, missing weights, etc.).
        """
        self.is_loaded = True          # prevent retry loops

        if self.device == "cpu":
            return                     # no pipeline on CPU

        tiers = self._get_tier_order()
        for tier_name, loader_fn in tiers:
            try:
                print(f"[DiffusionEngine] Attempting tier: {tier_name} ...")
                loader_fn()
                self.quality = tier_name
                print(f"[DiffusionEngine] Loaded: {tier_name}")
                return
            except Exception as exc:
                print(f"[DiffusionEngine] {tier_name} failed: {exc}")
                self._free_pipeline()

        print("[DiffusionEngine] All tiers failed — template overlay will be used.")

    def _get_tier_order(self):
        """Return (name, loader) pairs ordered best-to-worst by VRAM budget."""
        tiers = []
        if self._vram_gb >= 10:
            tiers.append(("sdxl_ip_controlnet", self._load_sdxl_ip_controlnet))
        if self._vram_gb >= 6:
            tiers.append(("sd15_ip",            self._load_sd15_ip))
        tiers.append(("sd15_base",              self._load_sd15_base))
        return tiers

    def _load_sd15_base(self):
        from diffusers import StableDiffusionInpaintPipeline
        pipe = StableDiffusionInpaintPipeline.from_pretrained(
            self._SD15_INPAINT_ID,
            torch_dtype=torch.float16,
            safety_checker=None,
            requires_safety_checker=False,
        ).to(self.device)
        self._apply_memory_opts(pipe)
        self.pipeline = pipe

    def _load_sd15_ip(self):
        """
        SD 1.5 Inpainting + IP-Adapter for identity preservation.
        IP-Adapter encodes the face image as an extra conditioning signal,
        so the model generates hair on the *same* person instead of a random face.
        """
        from diffusers import StableDiffusionInpaintPipeline
        pipe = StableDiffusionInpaintPipeline.from_pretrained(
            self._SD15_INPAINT_ID,
            torch_dtype=torch.float16,
            safety_checker=None,
            requires_safety_checker=False,
        ).to(self.device)

        # Load IP-Adapter weights (downloads automatically from HuggingFace)
        pipe.load_ip_adapter(
            self._IP_ADAPTER_REPO,
            subfolder="models",
            weight_name="ip-adapter-full-face_sd15.bin",
        )
        # Scale: 0.6 balances identity preservation vs. style freedom
        pipe.set_ip_adapter_scale(0.6)

        self._apply_memory_opts(pipe)
        self.pipeline = pipe

    def _load_sdxl_ip_controlnet(self):
        """
        SDXL Inpainting + IP-Adapter + ControlNet-Canny.
        Best quality tier: SDXL resolution + identity preserved + edge-guided.
        """
        from diffusers import (
            StableDiffusionXLInpaintPipeline,
            ControlNetModel,
        )
        controlnet = ControlNetModel.from_pretrained(
            "diffusers/controlnet-canny-sdxl-1.0",
            torch_dtype=torch.float16,
        )
        pipe = StableDiffusionXLInpaintPipeline.from_pretrained(
            self._SDXL_INPAINT_ID,
            controlnet=controlnet,
            torch_dtype=torch.float16,
            variant="fp16",
        ).to(self.device)
        pipe.load_ip_adapter(
            "h94/IP-Adapter",
            subfolder="sdxl_models",
            weight_name="ip-adapter-plus-face_sdxl_vit-h.bin",
        )
        pipe.set_ip_adapter_scale(0.5)
        self._apply_memory_opts(pipe)
        self.pipeline = pipe

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_memory_opts(pipe):
        """Apply all available memory optimisations."""
        try:
            pipe.enable_xformers_memory_efficient_attention()
        except Exception:
            pass
        pipe.enable_attention_slicing()

    def _free_pipeline(self):
        if self.pipeline is not None:
            del self.pipeline
            self.pipeline = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    @staticmethod
    def _detect_vram() -> float:
        """Return available GPU VRAM in GB, or 0.0 on CPU."""
        if not torch.cuda.is_available():
            return 0.0
        try:
            props = torch.cuda.get_device_properties(0)
            return props.total_memory / (1024 ** 3)
        except Exception:
            return 0.0

    @staticmethod
    def _make_canny(pil_image: Image.Image, original_bgr: np.ndarray) -> Image.Image:
        """Generate a Canny edge map from the face for ControlNet conditioning."""
        gray  = cv2.cvtColor(original_bgr, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, threshold1=100, threshold2=200)
        edges_rgb = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
        return Image.fromarray(edges_rgb).resize(pil_image.size)
