
import hashlib
import io
import time

import pandas as pd
import streamlit as st

from PIL import Image, UnidentifiedImageError
from PIL.PngImagePlugin import PngInfo

from src.traditional import process_image
from src.ai_assisted import ai_enhance_image
from src.experiments import save_experiment, CSV_PATH
from src.metrics import (
    calculate_metrics,
    calculate_preservation_metrics,
)


#--------------------------------------------------
# Page configuration
#--------------------------------------------------

st.set_page_config(
    page_title="Image Enhancement Lab",
    page_icon="🏠",
    layout="wide",
)


#--------------------------------------------------
# Custom styling and sticky navigation
#--------------------------------------------------

st.html("""
<style>
    .iel-navbar {
        position: fixed;
        top: 3.875rem;
        left: 0;
        right: 0;
        height: 64px;
        background: #14283F;
        color: white;
        z-index: 999;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 36px;
        box-sizing: border-box;
        box-shadow: 0 3px 12px rgba(20, 40, 63, 0.14);
    }

    .iel-brand {
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 19px;
        font-weight: 700;
        letter-spacing: -0.4px;
    }

    .iel-logo {
        width: 36px;
        height: 36px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #2563EB;
        color: #FFFFFF;
        font-size: 20px;
    }

    .iel-nav-label {
        color: #BBD2E6;
        font-size: 13px;
        font-weight: 500;
    }

    .iel-intro {
        padding-top: 20px;
        padding-bottom: 12px;
    }

    .iel-intro h1 {
        font-size: 30px;
        color: #14283F;
        margin-bottom: 8px;
        letter-spacing: -0.8px;
    }

    .iel-intro p {
        color: #64748B;
        font-size: 15px;
        margin: 0;
    }

    @media (max-width: 650px) {
        .iel-navbar {
            padding: 0 16px;
        }

        .iel-brand {
            font-size: 15px;
        }

        .iel-nav-label {
            display: none;
        }
    }
</style>

<div class="iel-navbar">
    <div class="iel-brand">
        <span class="iel-logo">⌂</span>
        <span>Image Enhancement Lab</span>
    </div>
    <div class="iel-nav-label">
        Immobiliare.it · Case Study
    </div>
</div>
""")

#Leave room below the fixed navigation bar
st.html('<div style="height: 76px;"></div>')

st.html("""
<div class="iel-intro">
    <h1>Workflow Comparison</h1>
    <p>
        Analyze, enhance and compare real estate
        photographs using traditional and AI-assisted workflows.
    </p>
</div>
""")

st.divider()


#--------------------------------------------------
# Session state
#--------------------------------------------------

if "experiment" not in st.session_state:
    st.session_state.experiment = None

if "image_hash" not in st.session_state:
    st.session_state.image_hash = None


#--------------------------------------------------
# Helpers
#--------------------------------------------------

def image_to_png(image, processed=False):
    """Convert a PIL image to downloadable PNG bytes."""
    buffer = io.BytesIO()
    metadata = PngInfo()

    if processed:
        metadata.add_text("PhotoLabProcessed", "true")

    image.save(
        buffer,
        format="PNG",
        pnginfo=metadata,
    )

    return buffer.getvalue()


def format_decision(decision):
    """Return a readable workflow status."""
    status = decision.get("status", "unknown")

    labels = {
        "enhanced": "Enhanced",
        "skipped": "Skipped",
        "rejected": "Rejected - review required",
        "error": "Error",
    }

    return labels.get(status, status)


def build_comparison_metrics(images):
    """Calculate the same metrics for all images."""

    metric_names = [
        "brightness",
        "contrast",
        "sharpness",
        "shadow_fraction",
        "highlight_clipping",
        "dynamic_range",
        "local_contrast",
    ]

    metrics = {
        name: calculate_metrics(img)
        for name, img in images.items()
    }

    data = {"Metric": metric_names}

    for name, values in metrics.items():
        data[name] = [
            round(values[metric], 3)
            for metric in metric_names
        ]

    return pd.DataFrame(data)


def run_experiment(image, already_processed):
    """Run both workflows on the same input image."""

    results = {
        "run_id": time.time_ns(),
        "original": image.copy(),
        "traditional": None,
        "ai": None,
        "ai_candidate": None,
        "traditional_decision": None,
        "ai_decision": None,
        "traditional_time": None,
        "ai_time": None,
        "traditional_error": None,
        "ai_error": None,
        "ai_blended": False,
    }

    #Workflow A
    start = time.perf_counter()

    try:
        traditional_image, decision = process_image(
            image.copy(),
            already_processed=already_processed,
        )

        results["traditional"] = traditional_image
        results["traditional_decision"] = decision

    except Exception as error:
        results["traditional_error"] = (
            f"{type(error).__name__}: {error}"
        )

    results["traditional_time"] = (
        time.perf_counter() - start
    )

    #Workflow B
    start = time.perf_counter()

    try:
        ai_image, ai_decision = ai_enhance_image(
            image.copy(),
            already_processed=already_processed,
        )

        #Remove PIL image from metadata dictionary
        candidate = ai_decision.pop(
            "candidate_image",
            None,
        )

        results["ai_candidate"] = candidate
        results["ai_decision"] = ai_decision

        #Experimental manual override: retain a softened rejected candidate without pretending it passed the gate
        if (
            ai_decision["status"] == "rejected"
            and candidate is not None
        ):
            ai_image = Image.blend(
                image.convert("RGB"),
                candidate.convert("RGB"),
                alpha=0.70,
            )

            results["ai_blended"] = True

        results["ai"] = ai_image

    except Exception as error:
        results["ai_error"] = (
            f"{type(error).__name__}: {error}"
        )

    results["ai_time"] = (
        time.perf_counter() - start
    )

    return results


#--------------------------------------------------
# Image upload
#--------------------------------------------------

uploaded_file = st.file_uploader(
    "Upload a real estate photo",
    type=["jpg", "jpeg", "png"],
)

if uploaded_file is None:
    st.info("Upload an image to start the experiment.")

else:
    try:
        uploaded_bytes = uploaded_file.getvalue()

        current_hash = hashlib.sha256(
            uploaded_bytes
        ).hexdigest()

        with Image.open(
            io.BytesIO(uploaded_bytes)
        ) as source:

            already_processed = (
                source.info.get("PhotoLabProcessed")
                == "true"
            )

            image = source.convert("RGB")

    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
    ):
        st.error("Unable to read the uploaded image.")
        st.stop()

    #Reset results when the input changes
    if st.session_state.image_hash != current_hash:
        st.session_state.image_hash = current_hash
        st.session_state.experiment = None

    st.write(
        f"Image resolution: "
        f"{image.width} × {image.height} px"
    )

    if already_processed:
        st.info(
            "This image was previously processed "
            "by Image Enhancement Lab."
        )

    #----------------------------------------------
    # Run experiment
    #----------------------------------------------

    if st.button(
        "Run Experiment",
        type="primary",
        icon=":material/play_arrow:",
        width="stretch",
    ):
        with st.spinner("Running both workflows..."):
            st.session_state.experiment = run_experiment(
                image,
                already_processed,
            )

    #----------------------------------------------
    # Experiment results
    #----------------------------------------------

    experiment = st.session_state.experiment

    if experiment is not None:

        original = experiment["original"]
        traditional = experiment["traditional"]
        ai = experiment["ai"]

        traditional_decision = experiment[
            "traditional_decision"
        ]

        ai_decision = experiment["ai_decision"]

        st.divider()
        st.header("Experiment Results", icon=":material/experiment:")

        #------------------------------------------
        # Image comparison
        #------------------------------------------

        st.subheader("Visual Comparison", icon=":material/compare:")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.image(
                original,
                caption="Original Image",
                width="stretch",
            )

        with col2:
            if traditional is not None:
                st.image(
                    traditional,
                    caption="Traditional Enhancement",
                    width="stretch",
                )
            else:
                st.error("Traditional workflow failed.")

        with col3:
            if ai is not None:
                caption = "AI-Assisted Enhancement"

                if experiment["ai_blended"]:
                    caption += " (manual override)"

                st.image(
                    ai,
                    caption=caption,
                    width="stretch",
                )
            else:
                st.error("AI workflow failed.")

        #------------------------------------------
        # Workflow decisions
        #------------------------------------------

        st.subheader("Workflow Decisions", icon=":material/rule:")

        decision_data = []

        for name, decision, error in [
            (
                "Traditional",
                traditional_decision,
                experiment["traditional_error"],
            ),
            (
                "AI-Assisted",
                ai_decision,
                experiment["ai_error"],
            ),
        ]:
            if error:
                status = "Error"
                reason = error
            else:
                status = format_decision(decision)
                reason = decision.get("reason", "")

            decision_data.append({
                "Workflow": name,
                "Status": status,
                "Reason": reason,
            })

        st.dataframe(
            pd.DataFrame(decision_data),
            hide_index=True,
            width="stretch",
        )

        if experiment["ai_blended"]:
            st.warning(
                "The AI candidate failed the Quality Gate. "
                "A 70% candidate / 30% original blend is "
                "displayed for experimental review. "
                "This output has NOT passed the Quality Gate."
            )

        #------------------------------------------
        # Processing times
        #------------------------------------------

        st.subheader("Processing Time", icon=":material/timer:")

        col_a, col_b = st.columns(2)

        with col_a:
            st.metric(
                "Traditional Workflow",
                f"{experiment['traditional_time']:.3f} s",
            )

        with col_b:
            st.metric(
                "AI-Assisted Workflow",
                f"{experiment['ai_time']:.3f} s",
            )

        #------------------------------------------
        # Quality metrics
        #------------------------------------------

        st.subheader("Image Quality Metrics", icon=":material/analytics:")

        available_images = {
            "Original": original,
        }

        if traditional is not None:
            available_images["Traditional"] = traditional

        if ai is not None:
            available_images["AI-Assisted"] = ai

        st.dataframe(
            build_comparison_metrics(available_images),
            hide_index=True,
            width="stretch",
        )

        st.caption(
            "Metrics are diagnostic indicators, not "
            "automatic measures of visual quality. "
            "Higher values are not always better."
        )

        #------------------------------------------
        # Preservation metrics
        #------------------------------------------

        st.subheader("Image Preservation Metrics", icon=":material/verified_user:")

        preservation_rows = []

        for name, output in [
            ("Traditional", traditional),
            ("AI-Assisted", ai),
        ]:
            if output is None:
                continue

            values = calculate_preservation_metrics(
                original,
                output,
            )

            preservation_rows.append({
                "Workflow": name,
                "Black Region Change": round(
                    values["black_region_change"], 3
                ),
                "Mean RGB Change": round(
                    values["mean_rgb_change"], 3
                ),
            })

        if preservation_rows:
            st.dataframe(
                pd.DataFrame(preservation_rows),
                hide_index=True,
                width="stretch",
            )

        #------------------------------------------
        # Detailed decisions and warnings
        #------------------------------------------

        with st.expander("Workflow Details"):

            if traditional_decision is not None:
                st.write("Traditional Workflow")
                st.json(traditional_decision)

            if ai_decision is not None:
                st.write("AI-Assisted Workflow")
                st.json(ai_decision)

            candidate = experiment["ai_candidate"]

            if (
                ai_decision is not None
                and ai_decision.get("status") == "rejected"
            ):
                st.warning(
                    "The AI candidate was rejected "
                    "by the Quality Gate."
                )

                warnings = ai_decision.get(
                    "quality_check", {}
                ).get("warnings", [])

                for warning in warnings:
                    st.write(f"- {warning}")

                if candidate is not None:
                    st.image(
                        candidate,
                        caption="Rejected AI-guided OpenCV candidate",
                        width=min(candidate.width, 650),
                    )

        #------------------------------------------
        # Downloads
        #------------------------------------------

        st.subheader("Download Results", icon=":material/download:")

        col_a, col_b = st.columns(2)

        with col_a:
            if traditional is not None:

                processed = (
                    already_processed
                    or traditional_decision["status"]
                    == "enhanced"
                )

                st.download_button(
                    "Download Traditional Image",
                    data=image_to_png(
                        traditional,
                        processed=processed,
                    ),
                    file_name="traditional_result.png",
                    mime="image/png",
                )

        with col_b:
            if ai is not None:

                processed = (
                    already_processed
                    or ai_decision["status"] == "enhanced"
                    or experiment["ai_blended"]
                )

                st.download_button(
                    "Download AI-Assisted Image",
                    data=image_to_png(
                        ai,
                        processed=processed,
                    ),
                    file_name="ai_assisted_result.png",
                    mime="image/png",
                )

        
        #------------------------------------------
        # Human evaluation
        #------------------------------------------

        st.divider()
        st.header("Human Evaluation", icon=":material/rate_review:")

        st.write(
            "Evaluate the visual quality, naturalness "
            "and property fidelity of each image."
        )

        st.caption(
            "Scores range from 1 (very poor) "
            "to 5 (excellent)."
        )

        evaluation_images = {
            "Original": original,
        }

        if traditional is not None:
            evaluation_images["Traditional"] = traditional

        if ai is not None:
            evaluation_images["AI-Assisted"] = ai

        run_id = experiment["run_id"]

        with st.form(
            key=f"evaluation_form_{run_id}"
        ):

            evaluation = {}

            columns = st.columns(
                len(evaluation_images)
            )

            for col, (name, output) in zip(
                columns,
                evaluation_images.items()
            ):

                with col:
                    st.subheader(name)

                    visual_quality = st.slider(
                        "Visual Quality",
                        min_value=1,
                        max_value=5,
                        value=3,
                        key=f"visual_{name}_{run_id}",
                    )

                    naturalness = st.slider(
                        "Naturalness",
                        min_value=1,
                        max_value=5,
                        value=3,
                        key=f"natural_{name}_{run_id}",
                    )

                    fidelity = st.slider(
                        "Property Fidelity",
                        min_value=1,
                        max_value=5,
                        value=5 if name == "Original" else 3,
                        key=f"fidelity_{name}_{run_id}",
                    )

                    if name != "Original":
                        material_change = st.checkbox(
                            "Potentially misleading alteration",
                            value=False,
                            key=f"alteration_{name}_{run_id}",
                        )
                    else:
                        material_change = False

                    evaluation[name] = {
                        "visual_quality": visual_quality,
                        "naturalness": naturalness,
                        "property_fidelity": fidelity,
                        "material_change": material_change,
                    }

            st.divider()

            preferred = st.radio(
                "Which image would you choose for the listing?",
                options=list(evaluation_images.keys()),
                horizontal=True,
            )

            feedback = st.text_area(
                "Why did you choose this image?",
                placeholder=(
                    "Explain your choice, including any "
                    "visual improvements or problems."
                ),
            )

            submitted = st.form_submit_button(
                "Save Evaluation",
                type="primary",
            )

        
        if submitted:

            experiment["human_evaluation"] = {
                "scores": evaluation,
                "preferred": preferred,
                "feedback": feedback,
            }

            try:
                saved = save_experiment(
                    experiment=experiment,
                    image_hash=current_hash,
                    source_filename=uploaded_file.name,
                )

                if saved:
                    st.success(
                        "Evaluation saved successfully to CSV."
                    )
                else:
                    st.info(
                        "This experiment is already saved. "
                        "No duplicate rows were created."
                    )

                st.caption(
                    f"File: {CSV_PATH}"
                )

            except (OSError, ValueError) as error:
                st.error(
                    f"Unable to save experiment: {error}"
                )

        if experiment.get("human_evaluation"):

            saved = experiment["human_evaluation"]

            st.subheader("Evaluation Summary")

            summary_rows = []

            for name, scores in saved["scores"].items():

                average = (
                    scores["visual_quality"]
                    + scores["naturalness"]
                    + scores["property_fidelity"]
                ) / 3

                summary_rows.append({
                    "Image": name,
                    "Visual Quality": scores["visual_quality"],
                    "Naturalness": scores["naturalness"],
                    "Property Fidelity": scores["property_fidelity"],
                    "Average": round(average, 2),
                    "Potential Alteration": scores["material_change"],
                })

            st.dataframe(
                pd.DataFrame(summary_rows),
                hide_index=True,
                width="stretch",
            )

            st.write(
                f"**Preferred image:** {saved['preferred']}"
            )

            if saved["feedback"]:
                st.write(
                    f"**Evaluator feedback:** "
                    f"{saved['feedback']}"
                )

            st.caption(
                "Average scores are descriptive only. "
                "Potentially misleading alterations "
                "must be reviewed separately."
            )