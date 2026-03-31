"""
Auto face detection using MediaPipe.

Detects a face in the input image and returns a crop box expanded to include
the head, forehead, and upper neck — suitable for lip sync sprite generation.
"""

import numpy as np
from PIL import Image


class FaceNotFoundError(Exception):
    """Raised when no face is detected in the input image."""
    pass


def detect_face_crop(
    image: Image.Image,
    expand_top: float = 0.3,
    expand_bottom: float = 0.5,
    expand_sides: float = 0.25,
    min_confidence: float = 0.5,
) -> tuple[int, int, int, int]:
    """
    Detect a face and return an expanded crop box.

    Args:
        image: PIL Image to detect face in.
        expand_top: Expand upward by this fraction of face height (forehead/hair).
        expand_bottom: Expand downward by this fraction of face height (chin/neck).
        expand_sides: Expand left/right by this fraction of face width.
        min_confidence: Minimum detection confidence (0-1).

    Returns:
        Tuple of (left, top, right, bottom) pixel coordinates for Pillow .crop().

    Raises:
        FaceNotFoundError: If no face is detected with sufficient confidence.
    """
    import mediapipe as mp

    img_width, img_height = image.size
    img_array = np.array(image.convert("RGB"))

    with mp.solutions.face_detection.FaceDetection(
        model_selection=1,  # full-range model (0.5m - 5m distance)
        min_detection_confidence=min_confidence,
    ) as face_detection:
        results = face_detection.process(img_array)

    if not results.detections:
        raise FaceNotFoundError(
            "No face detected in the image. "
            "Try a clearer image with a visible face, or use --crop-box to specify manually."
        )

    # Take highest confidence detection
    best = max(results.detections, key=lambda d: d.score[0])
    bbox = best.location_data.relative_bounding_box

    # Convert relative coordinates to pixels
    x = bbox.xmin * img_width
    y = bbox.ymin * img_height
    w = bbox.width * img_width
    h = bbox.height * img_height

    # Expand the bounding box
    left = x - w * expand_sides
    top = y - h * expand_top
    right = x + w + w * expand_sides
    bottom = y + h + h * expand_bottom

    # Clamp to image boundaries
    left = max(0, int(left))
    top = max(0, int(top))
    right = min(img_width, int(right))
    bottom = min(img_height, int(bottom))

    if right <= left or bottom <= top:
        raise FaceNotFoundError(
            "Face detected but crop box is invalid after expansion. "
            "The face may be too close to the image edge."
        )

    return (left, top, right, bottom)
