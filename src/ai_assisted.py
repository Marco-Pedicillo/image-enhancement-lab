
import io
import json
import os

import cv2
import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image
from src.quality_gate import evaluate_candidate

load_dotenv()

MODEL = "gemini-3.5-flash-lite"


def apply_ai_parameters(image, gamma, clahe_strength, shadow_lift):
    """
    Apply bounded, non-generative image enhancements.
    Preserve original image dimensions and geometry.
    """
    rgb = np.asarray(image.convert("RGB"))

    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)

    #Normalize luminance
    luminance = l_channel.astype(np.float32) / 255.0

    #Global brightening with gamma
    corrected = np.power(luminance, gamma)

    #Optional CLAHE
    corrected_l = np.clip(corrected * 255, 0, 255).astype(np.uint8)

    if clahe_strength > 0:
        clahe = cv2.createCLAHE(
            clipLimit=1.5,
            tileGridSize=(8, 8)
        )
        clahe_l = clahe.apply(corrected_l).astype(np.float32) / 255.0

        corrected = (
            (1.0 - clahe_strength) * corrected
            + clahe_strength * clahe_l
        )

    #Selective shadow lift: stronger effect only where luminance is dark
    shadow_mask = np.clip((0.65 - corrected) / 0.65, 0.0, 1.0)

    lifted = corrected + shadow_lift * shadow_mask * (1.0 - corrected)
    lifted = np.clip(lifted, 0.0, 1.0)

    final_l = np.clip(lifted * 255, 0, 255).astype(np.uint8)

    enhanced_lab = cv2.merge((final_l, a_channel, b_channel))
    enhanced_rgb = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2RGB)

    return Image.fromarray(enhanced_rgb)


def ai_enhance_image(image, already_processed=False):
    """
    Analyze an image with Gemini and apply
    conservative enhancement using OpenCV.

    Returns:
        processed_image, decision
    """
    original = image.convert("RGB")

    if already_processed:
        return original, {
            "status": "skipped",
            "reason": "Previously processed by this application.",
            "model": MODEL,
            "parameters": None,
            "usage": None
        }

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY not found in .env"
        )

    # Resize only the analysis copy
    preview = original.copy()
    preview.thumbnail((768, 768))

    buffer = io.BytesIO()
    preview.save(buffer, format="JPEG", quality=85)

    prompt = """
    You are a real estate photography specialist.

    Analyze this interior photograph and decide whether
    it needs exposure enhancement.

    The goal is to improve the visibility of property
    details while maintaining a natural appearance.

    Important rules:
    - Do not recommend architectural changes.
    - Preserve natural shadows and dark furniture.
    - Avoid washed-out or gray-looking images.
    - Protect bright windows and highlights.
    - If the photo is already good, recommend no changes.
    - If the scene is intentionally dark, be conservative.

    Return a JSON object with:
    - enhancement_needed: boolean
    - gamma: number between 0.55 and 1.0
    - clahe_strength: number between 0.0 and 0.25
    - shadow_lift: number between 0.0 and 0.35
    - reason: short string

    Gamma below 1 brightens the image.
    Lower gamma produces stronger brightening.

    shadow_lift should selectively brighten dark regions
    without excessively affecting bright windows.
    Do not brighten unnecessarily.
    """

    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=[
                prompt,
                types.Part.from_bytes(
                    data=buffer.getvalue(),
                    mime_type="image/jpeg"
                )
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0
            )
        )
    finally:
        client.close()

    if not response.text:
        raise ValueError("Gemini returned an empty response.")

    result = json.loads(response.text)

    if not isinstance(result, dict):
        raise ValueError("Invalid AI response structure.")

    needed = result.get("enhancement_needed")

    if type(needed) is not bool:
        raise ValueError("Invalid enhancement decision.")

    reason = result.get("reason", "")

    if not isinstance(reason, str):
        raise ValueError("Invalid AI reason.")

    usage = None

    if response.usage_metadata:
        usage = {
            "input_tokens": response.usage_metadata.prompt_token_count,
            "output_tokens": response.usage_metadata.candidates_token_count,
            "total_tokens": response.usage_metadata.total_token_count
        }

    if not needed:
        return original, {
            "status": "skipped",
            "reason": reason,
            "model": MODEL,
            "parameters": None,
            "usage": usage
        }

    #Validate model parameters
    raw_gamma = result.get("gamma")
    raw_clahe = result.get("clahe_strength")
    raw_shadow_lift = result.get("shadow_lift")

    if (
        type(raw_gamma) not in (int, float)
        or type(raw_clahe) not in (int, float)
        or type(raw_shadow_lift) not in (int, float)
    ):
        raise ValueError("Invalid enhancement parameters.")

    if not (
        np.isfinite(raw_gamma)
        and np.isfinite(raw_clahe)
        and np.isfinite(raw_shadow_lift)
    ):
        raise ValueError("Non-finite enhancement parameters.")

    gamma = float(np.clip(raw_gamma, 0.55, 1.0))
    clahe_strength = float(np.clip(raw_clahe, 0.0, 0.25))
    shadow_lift = float(np.clip(raw_shadow_lift, 0.0, 0.35))

    enhanced = apply_ai_parameters(
        original,
        gamma,
        clahe_strength,
        shadow_lift
    )

    quality_check = evaluate_candidate(original, enhanced)

    if not quality_check["accepted"]:
        return original, {
            "status": "rejected",
            "reason": "Candidate failed automatic quality checks.",
            "model": MODEL,
            "parameters": {
                "gamma": gamma,
                "clahe_strength": clahe_strength,
                "shadow_lift": shadow_lift
            },
            "quality_check": quality_check,
            "usage": usage,
            "candidate_image": enhanced
        }

    return enhanced, {
        "status": "enhanced",
        "reason": reason,
        "model": MODEL,
        "parameters": {
            "gamma": gamma,
            "clahe_strength": clahe_strength,
            "shadow_lift": shadow_lift
        },
        "usage": usage
    }
