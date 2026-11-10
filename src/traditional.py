
import cv2
import numpy as np
from PIL import Image



def enhance_image(image: Image.Image) -> Image.Image:
    """
    Conservative enhancement of indoor photographs.

    - Gamma-based brightness correction
    - Gentle local contrast enhancement
    - Preservation of black points
    - No geometry modification
    """

    rgb = np.asarray(image.convert("RGB"))

    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)

    luminance = l_channel.astype(np.float32) / 255.0

    #Estimate overall exposure
    median = float(np.median(l_channel))

    #Choose a moderate gamma correction
    if median < 55:
        gamma = 0.78
    elif median < 85:
        gamma = 0.87
    elif median < 115:
        gamma = 0.95
    else:
        gamma = 1.0

    #Gamma correction preserves absolute black (0)
    corrected = np.power(luminance, gamma)

    corrected_l = np.clip(
        corrected * 255.0,
        0, 255
    ).astype(np.uint8)

    #Very mild local contrast enhancement
    clahe = cv2.createCLAHE(
        clipLimit=1.2,
        tileGridSize=(8, 8)
    )

    contrast_l = clahe.apply(corrected_l)

    #Blend most of the gamma result with a small amount of CLAHE
    final_l = cv2.addWeighted(
        corrected_l, 0.90,
        contrast_l, 0.10,
        0
    )

    #Preserve original chromatic channels
    enhanced_lab = cv2.merge(
        (final_l, a_channel, b_channel)
    )

    enhanced_rgb = cv2.cvtColor(
        enhanced_lab,
        cv2.COLOR_LAB2RGB
    )

    return Image.fromarray(enhanced_rgb)



def assess_image(image: Image.Image) -> dict:
    """
    Estimate whether a photograph may benefit
    from brightness enhancement.

    Heuristic assessment, not a trained classifier.
    """
    rgb = np.asarray(image.convert("RGB"))

    gray = cv2.cvtColor(
        rgb, cv2.COLOR_RGB2GRAY
    )

    median = float(np.median(gray))
    dark_fraction = float(np.mean(gray < 60))
    clipped_fraction = float(np.mean(gray >= 250))

    #Conservative initial thresholds
    needs_enhancement = (
        median < 105
        or dark_fraction > 0.40
    )

    return {
        "median_brightness": round(median, 2),
        "dark_fraction": round(dark_fraction, 3),
        "clipped_fraction": round(clipped_fraction, 3),
        "needs_enhancement": needs_enhancement
    }



def process_image(
    image: Image.Image,
    already_processed: bool = False
) -> tuple:
    """
    Decide whether to enhance or retain the image.

    Returns:
        processed_image, decision
    """

    original = image.convert("RGB")
    assessment = assess_image(original)

    if already_processed:
        return original, {
            "status": "skipped",
            "reason": "Previously processed by this application.",
            "assessment": assessment
        }

    if not assessment["needs_enhancement"]:
        return original, {
            "status": "skipped",
            "reason": "No significant underexposure detected.",
            "assessment": assessment
        }

    enhanced = enhance_image(original)

    #Reject changes that increase clipping too much
    after = assess_image(enhanced)

    if (
        after["clipped_fraction"]
        - assessment["clipped_fraction"] > 0.02
    ):
        return original, {
            "status": "skipped",
            "reason": "Candidate rejected: excessive highlight clipping.",
            "assessment": assessment
        }

    #Reject nearly invisible modifications 
    before_rgb = np.asarray(
        original, dtype=np.float32
    )
    after_rgb = np.asarray(
        enhanced, dtype=np.float32
    )

    mean_change = float(
        np.mean(np.abs(after_rgb - before_rgb))
    )

    if mean_change < 2.0:
        return original, {
            "status": "skipped",
            "reason": "Enhancement produced negligible changes.",
            "assessment": assessment
        }

    return enhanced, {
        "status": "enhanced",
        "reason": "Underexposure detected; enhancement applied.",
        "assessment": assessment
    }
