from typing import List, Dict
import os


class HairstyleRecommender:
    """
    Rule-based hairstyle recommender keyed by face shape.
    This module is independent from the rendering pipeline; it only suggests.
    """

    def __init__(self):
        # Use available men styles in the repo. Map each face shape to filenames.
        # Keep values as base filenames; API will map to actual available values.
        self.mapping: Dict[str, List[str]] = {
            'Diamond': [
                'texturedcrop.png',
                'sidepart.png',
                'mid-length-layered-haircut.png',
                'faux hawk.png',
            ],
            'Oblong': [
                'bowl-cut-men-wavy.png',
                'side-part-curtain-hairstyle-men.png',
                'Crew-Cut-Haircut-Men.png',
                'Slick_Back.png',
            ],
            'Round': [
                'pompadour.png',
                'quiff.png',
                'sidepart.png',
                'faux hawk.png',
            ],
            'Oval': [
                'texturedcrop.png',
                'pompadour.png',
                'quiff.png',
                'side-part-curtain-hairstyle-men.png',
                'taper-fade.png',
                'ivy-league-haircut-men.png',
            ],
            'Square': ['side-part-curtain-hairstyle-men.png', 'bowl-cut-men-wavy.png', 'sidepart.png'],
            'Heart': ['texturedcrop.png', 'side-part-curtain-hairstyle-men.png', 'mid-length-layered-haircut.png'],
        }

        # Generic style-level reasons to display as tooltips
        self.style_reasons: Dict[str, str] = {
            'quiff.png': 'Adds height and volume on top to elongate and balance.',
            'texturedcrop.png': 'Light texture keeps balance without adding width at the jaw.',
            'pompadour.png': 'Volume on top lengthens the face and sharpens definition.',
            'side-part-curtain-hairstyle-men.png': 'Side part softens angles and balances width.',
            'bowl-cut-men-wavy.png': 'More width at the sides reduces perceived face length.',
            'sidepart.png': 'Classic part adds structure and subtle asymmetry.',
            'mid-length-layered-haircut.png': 'Layers add movement and soften strong cheekbones.',
            'faux hawk.png': 'Tapered sides with center height to elongate vertically.',
            'Crew-Cut-Haircut-Men.png': 'Clean and tidy; reduces perceived face length.',
            'Slick_Back.png': 'Sleek top with controlled sides for a longer silhouette.',
            'taper-fade.png': 'Tight sides with gradual fade to retain balance.',
            'ivy-league-haircut-men.png': 'Short and neat with a side part for versatility.',
        }

        # Shape-specific prefix notes
        self.shape_prefix: Dict[str, str] = {
            'Oval': 'Most styles work on oval faces. These maintain balance.',
            'Round': 'Add height, avoid adding width to the sides.',
            'Square': 'Soften strong angles; keep sides tidy.',
            'Heart': 'Balance broader forehead; avoid extra width at the temples.',
            'Oblong': 'Reduce length with side width; limit height on top.',
            'Diamond': 'Balance prominent cheekbones with moderate top volume.',
        }

    def recommend(self, face_shape: str, available_style_values: List[str]) -> List[str]:
        """
        Returns a list of recommended style values (e.g., 'men/quiff.png') filtered to what's available.

        face_shape: one of the canonical labels from the classifier
        available_style_values: full style identifiers from the loader (e.g., 'men/quiff.png')
        """
        base_list = self.mapping.get(face_shape, [])
        # Build a set of available basenames
        available_basenames = {os.path.basename(v): v for v in available_style_values}
        rec_values = []
        for fname in base_list:
            if fname in available_basenames:
                rec_values.append(available_basenames[fname])
        return rec_values

    def recommend_with_reasons(self, face_shape: str, available_style_values: List[str]):
        """
        Returns a tuple (recommended_values, reasons_map) where reasons_map maps each
        recommended style value to a human-readable reason string.
        """
        rec_values = self.recommend(face_shape, available_style_values)
        prefix = self.shape_prefix.get(face_shape, f"Recommended for {face_shape} face")
        reasons = {}
        for val in rec_values:
            base = os.path.basename(val)
            style_reason = self.style_reasons.get(base, '')
            if style_reason:
                reasons[val] = f"{prefix} — {style_reason}"
            else:
                reasons[val] = f"Recommended for {face_shape} face"
        return rec_values, reasons
