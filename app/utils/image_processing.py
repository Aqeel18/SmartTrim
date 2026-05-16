import cv2
import numpy as np

def resize_image(image, width=None, height=None):
    """
    Resizes an image maintaining aspect ratio.
    """
    (h, w) = image.shape[:2]
    if width is None and height is None:
        return image
    
    if width is None:
        r = height / float(h)
        dim = (int(w * r), height)
    else:
        r = width / float(w)
        dim = (width, int(h * r))
        
    return cv2.resize(image, dim, interpolation=cv2.INTER_AREA)
