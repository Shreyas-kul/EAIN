import cv2
import numpy as np
import base64
from typing import Dict, Any, Tuple

def estimate_vision_tokens(width: int, height: int, detail: str = "auto") -> int:
    """
    Standard Vision Token calculation formula (OpenAI & Gemini compatible).
    - Base low-res: ~85 tokens.
    - High-res tile calculation: 512x512 tiles @ 170 tokens/tile + base.
    """
    if detail == "low":
        return 85
    
    # Scale to fit inside 2048x2048
    if width > 2048 or height > 2048:
        scale = 2048.0 / max(width, height)
        width = int(width * scale)
        height = int(height * scale)

    # Scale shortest side to 768
    if min(width, height) > 768:
        scale = 768.0 / min(width, height)
        width = int(width * scale)
        height = int(height * scale)

    # Calculate 512x512 tiles
    tiles_w = (width + 511) // 512
    tiles_h = (height + 511) // 512
    total_tiles = tiles_w * tiles_h
    return 85 + (total_tiles * 170)

def compress_image_opencv(
    image_bytes: bytes,
    max_dimension: int = 768,
    jpeg_quality: int = 80
) -> Tuple[bytes, Dict[str, Any]]:
    """
    OpenCV Vision Compressor:
    Downscales large images and re-encodes with optimal compression
    to slash vision tokens and latency by up to 70%.
    """
    # Decode raw bytes using OpenCV
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Invalid image buffer: could not decode via OpenCV")

    orig_h, orig_w = img.shape[:2]
    orig_tokens = estimate_vision_tokens(orig_w, orig_h, detail="high")

    # Downscale if larger than max_dimension
    if max(orig_h, orig_w) > max_dimension:
        if orig_w >= orig_h:
            new_w = max_dimension
            new_h = int(orig_h * (max_dimension / float(orig_w)))
        else:
            new_h = max_dimension
            new_w = int(orig_w * (max_dimension / float(orig_h)))
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    else:
        new_w, new_h = orig_w, orig_h

    # Re-encode to optimized JPEG
    encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality]
    _, compressed_buf = cv2.imencode(".jpg", img, encode_params)
    compressed_bytes = compressed_buf.tobytes()

    new_tokens = estimate_vision_tokens(new_w, new_h, detail="high")
    tokens_saved = max(0, orig_tokens - new_tokens)
    pct_saved = round((tokens_saved / max(1, orig_tokens)) * 100, 1)

    metadata = {
        "original_resolution": f"{orig_w}x{orig_h}",
        "compressed_resolution": f"{new_w}x{new_h}",
        "original_bytes": len(image_bytes),
        "compressed_bytes": len(compressed_bytes),
        "bytes_reduction_pct": round(((len(image_bytes) - len(compressed_bytes)) / max(1, len(image_bytes))) * 100, 1),
        "vision_tokens_before": orig_tokens,
        "vision_tokens_after": new_tokens,
        "tokens_saved": tokens_saved,
        "percent_tokens_saved": pct_saved
    }

    return compressed_bytes, metadata
