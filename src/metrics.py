
import cv2
import numpy as np
from PIL import Image


def calculate_metrics(image: Image.Image) -> dict:
    rgb = np.asarray(image.convert("RGB"))

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    gray_float = gray.astype(np.float32)

    p5 = float(np.percentile(gray, 5))
    p95 = float(np.percentile(gray, 95))

    #Local contrast: average variation within non-overlapping 32x32 pixel blocks.
    block_size = 32
    local_values = []

    h, w = gray.shape

    for y in range(0, h - block_size + 1, block_size):
        for x in range(0, w - block_size + 1, block_size):
            block = gray_float[
                y:y + block_size,
                x:x + block_size
            ]
            local_values.append(float(np.std(block)))

    return {
        "brightness": float(np.mean(gray_float)),
        "contrast": float(np.std(gray_float)),
        "sharpness": float(
            cv2.Laplacian(gray, cv2.CV_64F).var()
        ),
        "shadow_fraction": float(np.mean(gray < 50)),
        "highlight_clipping": float(np.mean(gray >= 250)),
        "dynamic_range": p95 - p5,
        "local_contrast": float(
            np.mean(local_values)
        ) if local_values else 0.0
    }


def calculate_preservation_metrics(
    original: Image.Image,
    enhanced: Image.Image
) -> dict:
    if original.size != enhanced.size:
        raise ValueError("Image dimensions must match.")

    before = np.asarray(
        original.convert("RGB"), dtype=np.float32
    )
    after = np.asarray(
        enhanced.convert("RGB"), dtype=np.float32
    )

    original_gray = cv2.cvtColor(
        before.astype(np.uint8),
        cv2.COLOR_RGB2GRAY
    )

    #Pixels initially considered very dark
    dark_mask = original_gray < 30

    black_change = (
        float(np.mean(np.abs(after - before)[dark_mask]))
        if np.any(dark_mask) else 0.0
    )

    #Mean RGB change, not perceptual Delta E
    color_change = float(
        np.mean(np.abs(after - before))
    )

    return {
        "black_region_change": black_change,
        "mean_rgb_change": color_change
    }



def build_metrics_table(original, enhanced):
    """
    Build a comparison table for two images.
    """
    original_metrics = calculate_metrics(original)
    enhanced_metrics = calculate_metrics(enhanced)

    metric_names = [
        "brightness",
        "contrast",
        "sharpness",
        "shadow_fraction",
        "highlight_clipping",
        "dynamic_range",
        "local_contrast"
    ]

    return {
        "Metric": metric_names,
        "Original": [
            round(original_metrics[k], 3)
            for k in metric_names
        ],
        "Enhanced": [
            round(enhanced_metrics[k], 3)
            for k in metric_names
        ]
    }
