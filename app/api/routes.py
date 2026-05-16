"""
API Routes — SmartTrim 360

Endpoints
---------
GET  /hairstyles             List all available hairstyles with thumbnail URLs.
POST /analyze-face-shape     Detect face shape, head pose, and get recommendations.
POST /recommend              CLIP-based semantic hairstyle recommendations.
POST /preview                Synchronous preview (blocks until done).
POST /preview-async          Submit async inference job, returns job_id immediately.
GET  /jobs/{job_id}          Poll job status + result URL.
WS   /ws/job/{job_id}        WebSocket stream: push progress updates in real time.
"""

from __future__ import annotations

import asyncio
import base64
import os
from typing import List, Optional

import cv2
import numpy as np
from fastapi import (APIRouter, File, Form, HTTPException, UploadFile,
                     WebSocket, WebSocketDisconnect)
from fastapi.responses import Response

# Core pipeline
from app.core.face_analysis import FaceAnalyzer
from app.core.hair_segmentation import HairSegmenter
from app.core.hair_removal import HairRemover
from app.core.color_extraction import HairColorExtractor
from app.core.warp import HairstyleWarper
from app.core.color_transfer import HairColorTransfer
from app.core.overlay import FinalOverlayEngine
from app.core.hairstyle_templates import hairstyle_loader
from app.core.face_shape_classifier import FaceShapeClassifier
from app.core.hairstyle_recommender import HairstyleRecommender
from app.core.clip_recommender import CLIPRecommender

# AI modules
from app.ai_modules.inference.diffusion_engine import DiffusionEngine

# Async job store
from app.jobs import job_store, JobStatus

router = APIRouter()

# ── Model initialisation ─────────────────────────────────────────────────────
# Models are loaded once at import time. The FastAPI lifespan in main.py reads
# MODELS_LOADED to surface startup warnings. Granular try/except means a single
# failing optional model (e.g. CLIP on a low-RAM machine) won't kill the server.

print("[Routes] Initialising pipeline models...")

try:
    analyzer          = FaceAnalyzer()
    segmenter         = HairSegmenter()
    remover           = HairRemover()
    extractor         = HairColorExtractor()
    warper            = HairstyleWarper()
    transfer          = HairColorTransfer()
    overlay_engine    = FinalOverlayEngine()
    face_shape_clf    = FaceShapeClassifier()
    rule_recommender  = HairstyleRecommender()
    diffusion_engine  = DiffusionEngine()
    MODELS_LOADED     = True
    print("[Routes] Core pipeline ready.")
except Exception as exc:
    print(f"[Routes] CRITICAL — pipeline init failed: {exc}")
    MODELS_LOADED = False

# CLIP recommender loads separately (optional, CPU-safe)
try:
    clip_recommender = CLIPRecommender()
except Exception as exc:
    print(f"[Routes] CLIP recommender unavailable: {exc}")
    clip_recommender = None


# ── Helpers ──────────────────────────────────────────────────────────────────

def _decode_upload(file_bytes: bytes) -> np.ndarray:
    np_buf = np.frombuffer(file_bytes, dtype=np.uint8)
    img    = cv2.imdecode(np_buf, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Invalid or corrupt image data.")
    return img


def _encode_jpeg(img: np.ndarray, quality: int = 90) -> bytes:
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to encode result image.")
    return buf.tobytes()


def _run_template_pipeline(face_bgr: np.ndarray, hairstyle: str) -> np.ndarray:
    """Deterministic warp+Poisson pipeline used as the CPU/fallback path."""
    analysis    = analyzer.detect_landmarks(face_bgr)
    if not analysis.get("face_detected"):
        raise HTTPException(status_code=422, detail="No face detected.")
    landmarks   = np.array(analysis["landmarks_pixel"], dtype=np.float32)
    hair_mask   = segmenter.segment_hair(face_bgr)
    hair_removed = remover.remove_hair(face_bgr, hair_mask)

    template_bgra  = hairstyle_loader.load_template(hairstyle)
    tmpl_rgb       = template_bgra[:, :, :3]
    tmpl_alpha_raw = template_bgra[:, :, 3]
    t_res          = analyzer.detect_landmarks(tmpl_rgb)
    tmpl_landmarks = (np.array(t_res["landmarks_pixel"], dtype=np.float32)
                      if t_res and t_res.get("face_detected") else None)
    tmpl_hair_mask = segmenter.segment_hair(tmpl_rgb)
    tmpl_alpha     = cv2.bitwise_and(tmpl_alpha_raw, tmpl_hair_mask)

    h, w = face_bgr.shape[:2]
    warped_rgb, warped_alpha = warper.warp_hairstyle(
        tmpl_rgb, tmpl_alpha, landmarks, tmpl_landmarks, output_shape=(h, w)
    )
    color_stats = extractor.extract_color_stats(face_bgr, hair_mask)
    warped_rgb  = transfer.transfer_color(warped_rgb, warped_alpha, color_stats)
    return overlay_engine.overlay(face_bgr, hair_removed, warped_rgb, warped_alpha, hair_mask)


# ── GET /hairstyles ───────────────────────────────────────────────────────────

@router.get("/hairstyles", tags=["Assets"])
async def get_available_hairstyles():
    """List all available hairstyle assets grouped by category with thumbnail URLs."""
    data = hairstyle_loader.list_available_styles()
    enriched = {}
    for cat, items in data.items():
        new_items = []
        for it in items:
            val    = it.get("value")
            source = it.get("source", "cleaned")
            if isinstance(val, str):
                prefix    = {"cleaned": "/hairstyle-assets",
                             "orig":    "/hairstyle-assets-orig",
                             "raw":     "/hairstyle-assets-raw"}.get(source, "/hairstyle-assets")
                image_url = f"{prefix}/{val}".replace("\\", "/")
            else:
                image_url = None
            new_items.append({**it, "image_url": image_url})
        enriched[cat] = new_items
    return enriched


# ── POST /analyze-face-shape ──────────────────────────────────────────────────

@router.post("/analyze-face-shape", tags=["Analysis"])
async def analyze_face_shape(image: UploadFile = File(...)):
    """
    Detect face landmarks → classify face shape (with confidence + per-class scores)
    → extract 3D head pose → return ranked hairstyle recommendations.
    """
    if not MODELS_LOADED:
        raise HTTPException(status_code=503, detail="Pipeline models not ready.")
    try:
        face_bgr = _decode_upload(await image.read())

        analysis = analyzer.detect_landmarks(face_bgr)
        if not analysis.get("face_detected"):
            raise HTTPException(status_code=422, detail="No face detected in the image.")

        landmarks  = analysis["landmarks_pixel"]
        head_pose  = analysis.get("head_pose", {})
        fs_result  = face_shape_clf.analyze(landmarks, face_bgr=face_bgr)

        available_values = [
            it["value"]
            for items in hairstyle_loader.list_available_styles().values()
            for it in items
            if isinstance(it.get("value"), str)
        ]

        rec_values, reasons = rule_recommender.recommend_with_reasons(
            fs_result["face_shape"], available_values
        )

        return {
            "face_shape":      fs_result["face_shape"],
            "confidence":      fs_result.get("confidence"),
            "scores":          fs_result.get("scores", {}),
            "method":          fs_result.get("method", "geometric"),
            "metrics":         fs_result["metrics"],
            "head_pose":       head_pose,
            "is_front_facing": head_pose.get("is_front_facing", True),
            "recommended":     rec_values,
            "reasons":         reasons,
        }

    except HTTPException:
        raise
    except Exception as exc:
        print(f"[analyze-face-shape] {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ── POST /recommend ───────────────────────────────────────────────────────────

@router.post("/recommend", tags=["Analysis"])
async def semantic_recommend(
    image:      UploadFile = File(...),
    face_shape: str        = Form(...),
):
    """
    CLIP-powered semantic hairstyle recommendations.

    Encodes all hairstyle assets with CLIP ViT-B/32 and ranks by cosine
    similarity to a text description of ideal styles for the given face shape.
    Falls back to the rule-table if CLIP is unavailable.
    """
    if not MODELS_LOADED:
        raise HTTPException(status_code=503, detail="Pipeline models not ready.")
    try:
        face_bgr = _decode_upload(await image.read())
        analysis = analyzer.detect_landmarks(face_bgr)
        head_pose = analysis.get("head_pose", {}) if analysis.get("face_detected") else {}

        available_values = [
            it["value"]
            for items in hairstyle_loader.list_available_styles().values()
            for it in items
            if isinstance(it.get("value"), str)
        ]

        rec = clip_recommender or CLIPRecommender()
        results = rec.recommend(
            face_shape=face_shape,
            head_pose=head_pose,
            available_values=available_values,
        )
        return {"face_shape": face_shape, "recommendations": results}

    except HTTPException:
        raise
    except Exception as exc:
        print(f"[recommend] {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ── POST /preview (synchronous) ───────────────────────────────────────────────

@router.post("/preview", tags=["Generation"])
async def create_hairstyle_preview(
    image:     UploadFile = File(...),
    hairstyle: str        = Form(...),
):
    """
    Synchronous hairstyle preview. Blocks until the result is ready.
    For long-running GPU inference, prefer /preview-async.
    """
    if not MODELS_LOADED:
        raise HTTPException(status_code=503, detail="Pipeline models not ready.")
    try:
        face_bgr   = _decode_upload(await image.read())
        hair_mask  = segmenter.segment_hair(face_bgr)
        style_name = os.path.splitext(os.path.basename(hairstyle))[0].replace("_", " ")

        try:
            final_bgr = diffusion_engine.generate_hair(face_bgr, hair_mask, style_name)
        except Exception as diff_exc:
            print(f"[preview] Diffusion failed ({diff_exc}), using template pipeline.")
            final_bgr = _run_template_pipeline(face_bgr, hairstyle)

        return Response(content=_encode_jpeg(final_bgr), media_type="image/jpeg")

    except HTTPException:
        raise
    except Exception as exc:
        print(f"[preview] {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ── POST /preview-async ───────────────────────────────────────────────────────

@router.post("/preview-async", tags=["Generation"])
async def create_hairstyle_preview_async(
    image:     UploadFile = File(...),
    hairstyle: str        = Form(...),
):
    """
    Submit a hairstyle generation job. Returns a job_id immediately.

    Poll GET /jobs/{job_id} for status, or subscribe to WS /ws/job/{job_id}
    for real-time progress updates.
    """
    if not MODELS_LOADED:
        raise HTTPException(status_code=503, detail="Pipeline models not ready.")

    file_bytes = await image.read()
    job        = await job_store.create()

    async def _run():
        try:
            await job_store.update(job.job_id, status=JobStatus.PROCESSING,
                                   progress=5, message="Decoding image...")
            face_bgr  = _decode_upload(file_bytes)
            hair_mask = segmenter.segment_hair(face_bgr)

            style_name = os.path.splitext(os.path.basename(hairstyle))[0].replace("_", " ")
            await job_store.update(job.job_id, progress=15, message="Starting inference...")

            def _progress_cb(pct: int):
                # Bridge sync callback → async update (fire-and-forget)
                asyncio.get_event_loop().call_soon_threadsafe(
                    lambda: asyncio.ensure_future(
                        job_store.update(job.job_id, progress=pct,
                                         message=f"Generating... {pct}%")
                    )
                )

            try:
                final_bgr = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: diffusion_engine.generate_hair(
                        face_bgr, hair_mask, style_name, progress_cb=_progress_cb
                    ),
                )
            except Exception as diff_exc:
                print(f"[preview-async] Diffusion failed ({diff_exc}), using template.")
                await job_store.update(job.job_id, progress=50,
                                       message="Using template pipeline...")
                final_bgr = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: _run_template_pipeline(face_bgr, hairstyle)
                )

            jpeg_bytes = _encode_jpeg(final_bgr)
            b64        = base64.b64encode(jpeg_bytes).decode()
            await job_store.update(
                job.job_id,
                status=JobStatus.DONE,
                progress=100,
                message="Done",
                result=b64,
            )
        except Exception as exc:
            print(f"[preview-async job {job.job_id}] {exc}")
            await job_store.update(
                job.job_id,
                status=JobStatus.FAILED,
                progress=0,
                message="Failed",
                error=str(exc),
            )

    asyncio.create_task(_run())
    return {"job_id": job.job_id, "status": "pending"}


# ── GET /jobs/{job_id} ────────────────────────────────────────────────────────

@router.get("/jobs/{job_id}", tags=["Generation"])
async def get_job_status(job_id: str):
    """
    Poll a job's current status, progress percentage, and result.

    When status == 'done', the 'result' field contains the base64-encoded JPEG.
    """
    job = await job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    payload = job.to_dict()
    if job.status == JobStatus.DONE and job.result:
        payload["result"] = job.result      # base64 string
    return payload


# ── WebSocket /ws/job/{job_id} ────────────────────────────────────────────────

@router.websocket("/ws/job/{job_id}")
async def websocket_job_progress(websocket: WebSocket, job_id: str):
    """
    Real-time job progress stream.

    The server pushes a JSON message on every status change:
      {"job_id": "...", "status": "processing", "progress": 45, "message": "..."}

    When status == 'done', the message includes 'result' (base64 JPEG).
    Connection closes automatically when the job reaches 'done' or 'failed'.
    """
    await websocket.accept()
    try:
        while True:
            job = await job_store.get(job_id)
            if job is None:
                await websocket.send_json({"error": "Job not found"})
                break

            payload = job.to_dict()
            if job.status == JobStatus.DONE and job.result:
                payload["result"] = job.result

            await websocket.send_json(payload)

            if job.status in (JobStatus.DONE, JobStatus.FAILED):
                break

            # Wait for next update (up to 30 s) before pushing again
            await job_store.wait_for_update(job_id, timeout=30.0)

    except WebSocketDisconnect:
        pass
    finally:
        await websocket.close()
