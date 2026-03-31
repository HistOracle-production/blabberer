"""Blabberer — Generate lip sync mouth shape sprites from any face image using AI."""

__version__ = "0.1.0"

from blabberer.generator import generate_sprites
from blabberer.face_detect import detect_face_crop, FaceNotFoundError
from blabberer.postprocess import remove_backgrounds, apply_soft_edges, full_postprocess

__all__ = [
    "generate_sprites",
    "detect_face_crop",
    "FaceNotFoundError",
    "remove_backgrounds",
    "apply_soft_edges",
    "full_postprocess",
]
