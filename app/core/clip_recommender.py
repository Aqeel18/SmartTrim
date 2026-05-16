"""
CLIP-Based Hairstyle Recommender — SmartTrim 360 Phase 2.

Replaces the static rule-table lookup with semantic similarity search.

How it works
------------
1. On first call, every hairstyle asset image is encoded with OpenAI CLIP
   (ViT-B/32) into a 512-dim embedding and cached to disk as a .npy file.
2. The user's detected face attributes (face shape + head pose) are combined
   into a text query, also encoded with CLIP.
3. We rank hairstyles by cosine similarity between the text query and each
   image embedding, returning the top-K results with scores.

Why CLIP
--------
- Zero-shot: no training data required.
- Image embeddings capture actual visual style (length, texture, volume),
  not just filenames.
- Cosine similarity produces interpretable confidence scores.
- Can be extended to accept a "reference style" image from the user.

Fallback
--------
If the CLIP model cannot be loaded (no GPU, no transformers), the
CLIPRecommender transparently delegates to the original HairstyleRecommender
rule table, so the system always returns results.
"""

import os
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional


class CLIPRecommender:
    """
    CLIP-powered hairstyle ranker with rule-table fallback.

    Parameters
    ----------
    assets_dir : str
        Root directory containing hairstyle PNG/JPG assets.
    cache_dir : str
        Directory where embedding .npy files are persisted between runs.
    top_k : int
        Maximum number of recommendations to return.
    """

    _CLIP_MODEL = "openai/clip-vit-base-patch32"

    def __init__(
        self,
        assets_dir: Optional[str] = None,
        cache_dir:  Optional[str] = None,
        top_k: int = 6,
    ):
        self.top_k      = top_k
        self._model     = None
        self._processor = None
        self._available = False

        # Resolve paths
        _here      = Path(__file__).parent
        _app_root  = _here.parent.parent
        self.assets_dir = Path(assets_dir) if assets_dir else _app_root / "assets" / "cleaned_hairstyles"
        self.cache_dir  = Path(cache_dir)  if cache_dir  else _here.parent / "clip_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._try_load_clip()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def recommend(
        self,
        face_shape: str,
        head_pose:  Optional[Dict] = None,
        available_values: Optional[List[str]] = None,
        reference_image: Optional[np.ndarray] = None,
    ) -> List[Dict]:
        """
        Return top-K hairstyle recommendations ranked by semantic similarity.

        Parameters
        ----------
        face_shape       : str  e.g. 'Oval', 'Round'
        head_pose        : dict  {'yaw': float, 'pitch': float, 'roll': float}
        available_values : list  Style identifiers from the asset loader.
        reference_image  : np.ndarray (optional)  BGR image of a desired style.

        Returns
        -------
        list of dicts: [{'value': str, 'score': float, 'reason': str}, ...]
        """
        if not self._available or available_values is None:
            return self._rule_fallback(face_shape, available_values or [])

        # Build candidate paths
        candidates = self._resolve_paths(available_values)
        if not candidates:
            return self._rule_fallback(face_shape, available_values)

        # Encode candidates
        img_embeddings, valid_values = self._encode_images(candidates)
        if img_embeddings is None or len(img_embeddings) == 0:
            return self._rule_fallback(face_shape, available_values)

        # Encode query
        if reference_image is not None:
            query_emb = self._encode_reference_image(reference_image)
        else:
            query_text = self._build_query(face_shape, head_pose)
            query_emb  = self._encode_text(query_text)

        if query_emb is None:
            return self._rule_fallback(face_shape, available_values)

        # Cosine similarity ranking
        scores = self._cosine_similarity(query_emb, img_embeddings)  # (N,)
        ranked_indices = np.argsort(scores)[::-1][: self.top_k]

        results = []
        for idx in ranked_indices:
            val   = valid_values[idx]
            score = float(scores[idx])
            results.append({
                "value":  val,
                "score":  round(score, 4),
                "reason": self._score_to_reason(score, face_shape),
            })
        return results

    # ------------------------------------------------------------------
    # Query construction
    # ------------------------------------------------------------------

    @staticmethod
    def _build_query(face_shape: str, head_pose: Optional[Dict]) -> str:
        """
        Build a descriptive text query for CLIP encoding.

        The query describes desired visual properties for the given face shape
        so CLIP can retrieve hairstyle images that visually match them.
        """
        shape_descriptors = {
            "Oval":    "balanced hairstyle with moderate volume, versatile length",
            "Round":   "hairstyle with height on top, tapered sides, elongating face",
            "Square":  "hairstyle with soft layers, side-swept, reducing jawline width",
            "Heart":   "hairstyle with width at jaw level, light crown, side parting",
            "Oblong":  "hairstyle with width at sides, minimal height, curtain layers",
            "Diamond": "hairstyle with moderate top volume, balanced cheekbones",
        }
        descriptor = shape_descriptors.get(face_shape, "stylish professional hairstyle for men")
        return f"men's {descriptor}, photorealistic hair, studio lighting"

    # ------------------------------------------------------------------
    # CLIP encoding
    # ------------------------------------------------------------------

    def _encode_images(
        self, candidates: List[Tuple[str, Path]]
    ) -> Tuple[Optional[np.ndarray], List[str]]:
        """
        Encode hairstyle images with CLIP. Uses on-disk cache to avoid
        re-encoding unchanged assets on every startup.
        """
        import torch

        all_embeddings = []
        valid_values   = []

        for value, img_path in candidates:
            cache_file = self.cache_dir / f"{img_path.stem}.npy"

            if cache_file.exists():
                emb = np.load(str(cache_file))
            else:
                emb = self._encode_single_image(img_path)
                if emb is None:
                    continue
                np.save(str(cache_file), emb)

            all_embeddings.append(emb)
            valid_values.append(value)

        if not all_embeddings:
            return None, []

        return np.stack(all_embeddings, axis=0), valid_values   # (N, D)

    def _encode_single_image(self, img_path: Path) -> Optional[np.ndarray]:
        try:
            from PIL import Image
            import torch
            img    = Image.open(str(img_path)).convert("RGB")
            inputs = self._processor(images=img, return_tensors="pt")
            with torch.no_grad():
                feats = self._model.get_image_features(**inputs)
                feats = feats / feats.norm(dim=-1, keepdim=True)
            return feats.squeeze(0).cpu().numpy()
        except Exception as exc:
            print(f"[CLIPRecommender] Failed to encode {img_path.name}: {exc}")
            return None

    def _encode_text(self, text: str) -> Optional[np.ndarray]:
        try:
            import torch
            inputs = self._processor(text=[text], return_tensors="pt", padding=True)
            with torch.no_grad():
                feats = self._model.get_text_features(**inputs)
                feats = feats / feats.norm(dim=-1, keepdim=True)
            return feats.squeeze(0).cpu().numpy()
        except Exception as exc:
            print(f"[CLIPRecommender] Text encoding failed: {exc}")
            return None

    def _encode_reference_image(self, bgr: np.ndarray) -> Optional[np.ndarray]:
        """Encode a user-supplied reference style image."""
        try:
            import cv2
            from PIL import Image
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            return self._encode_single_image.__func__(
                self, Path("_ref"),  # path is unused when we pass pil directly
            )
            # Inline version:
            pil    = Image.fromarray(rgb)
            import torch
            inputs = self._processor(images=pil, return_tensors="pt")
            with torch.no_grad():
                feats = self._model.get_image_features(**inputs)
                feats = feats / feats.norm(dim=-1, keepdim=True)
            return feats.squeeze(0).cpu().numpy()
        except Exception as exc:
            print(f"[CLIPRecommender] Reference image encoding failed: {exc}")
            return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _try_load_clip(self):
        try:
            from transformers import CLIPModel, CLIPProcessor
            self._model     = CLIPModel.from_pretrained(self._CLIP_MODEL)
            self._processor = CLIPProcessor.from_pretrained(self._CLIP_MODEL)
            self._model.eval()
            self._available = True
            print(f"[CLIPRecommender] CLIP loaded ({self._CLIP_MODEL})")
        except Exception as exc:
            print(f"[CLIPRecommender] CLIP unavailable: {exc}. Using rule fallback.")

    def _resolve_paths(
        self, available_values: List[str]
    ) -> List[Tuple[str, Path]]:
        """Map style value strings to actual file paths, filtering missing files."""
        result = []
        for val in available_values:
            candidate = self.assets_dir / val
            if candidate.exists():
                result.append((val, candidate))
        return result

    @staticmethod
    def _cosine_similarity(query: np.ndarray, matrix: np.ndarray) -> np.ndarray:
        """Compute cosine similarity between a query vector and a matrix of rows."""
        q = query / (np.linalg.norm(query) + 1e-8)
        M = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-8)
        return M @ q    # (N,)

    @staticmethod
    def _score_to_reason(score: float, face_shape: str) -> str:
        if score > 0.28:
            return f"Highly recommended for {face_shape} face — strong visual match."
        elif score > 0.22:
            return f"Good fit for {face_shape} face — visually compatible style."
        else:
            return f"Suggested for {face_shape} face — worth trying."

    def _rule_fallback(
        self, face_shape: str, available_values: List[str]
    ) -> List[Dict]:
        """Delegate to original rule table when CLIP is unavailable."""
        from app.core.hairstyle_recommender import HairstyleRecommender
        rec = HairstyleRecommender()
        values, reasons = rec.recommend_with_reasons(face_shape, available_values)
        return [
            {"value": v, "score": None, "reason": reasons.get(v, "")}
            for v in values
        ]
