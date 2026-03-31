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

    # Use the new MediaPipe Tasks API
    BaseOptions = mp.tasks.BaseOptions
    FaceDetector = mp.tasks.vision.FaceDetector
    FaceDetectorOptions = mp.tasks.vision.FaceDetectorOptions
    VisionRunningMode = mp.tasks.vision.RunningMode

    options = FaceDetectorOptions(
        base_options=BaseOptions(model_asset_path=_get_face_detection_model()),
        running_mode=VisionRunningMode.IMAGE,
        min_detection_confidence=min_confidence,
    )

    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_array)

    with FaceDetector.create_from_options(options) as detector:
        result = detector.detect(mp_image)

    if not result.detections:
        raise FaceNotFoundError(
            "No face detected in the image. "
            "Try a clearer image with a visible face, or use --crop-box to specify manually."
        )

    # Take highest confidence detection
    best = max(result.detections, key=lambda d: d.categories[0].score)
    bbox = best.bounding_box

    # bbox fields are in pixels
    x = bbox.origin_x
    y = bbox.origin_y
    w = bbox.width
    h = bbox.height

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


def _get_face_detection_model() -> str:
    """Download and cache the MediaPipe face detection model."""
    import os
    import urllib.request

    cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "blabberer")
    os.makedirs(cache_dir, exist_ok=True)
    model_path = os.path.join(cache_dir, "blaze_face_short_range.tflite")

    if not os.path.exists(model_path):
        url = "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite"
        print("Downloading face detection model...")
        urllib.request.urlretrieve(url, model_path)

    return model_path
