"""
Generation history routes — SmartTrim 360 Phase 3.

Endpoints
---------
POST /history/           Save a generation record for the current user
GET  /history/           List current user's generation history (paginated)
GET  /history/{id}       Get a single generation record
DELETE /history/{id}     Delete a generation record
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional

from app.auth import get_current_user
from app.db.session import get_db
from app.db.models import User, Generation

history_router = APIRouter(prefix="/history", tags=["History"])

# ─── Schemas ──────────────────────────────────────────────────────────────────

class GenerationIn(BaseModel):
    hairstyle:  str
    style_name: Optional[str]  = None
    face_shape: Optional[str]  = None
    result_url: Optional[str]  = None
    pipeline:   Optional[str]  = None          # 'diffusion' or 'template'
    duration_ms: Optional[int] = None


class GenerationOut(BaseModel):
    id:          str
    hairstyle:   str
    style_name:  Optional[str]
    face_shape:  Optional[str]
    result_url:  Optional[str]
    pipeline:    Optional[str]
    duration_ms: Optional[int]
    created_at:  str

    class Config:
        from_attributes = True

# ─── Routes ───────────────────────────────────────────────────────────────────

@history_router.post("/", response_model=GenerationOut, status_code=status.HTTP_201_CREATED)
def save_generation(
    body:         GenerationIn,
    current_user: User    = Depends(get_current_user),
    db:           Session = Depends(get_db),
):
    """Record a new hairstyle generation for the authenticated user."""
    gen = Generation(
        user_id     = current_user.id,
        hairstyle   = body.hairstyle,
        style_name  = body.style_name,
        face_shape  = body.face_shape,
        result_url  = body.result_url,
        pipeline    = body.pipeline,
        duration_ms = body.duration_ms,
    )
    db.add(gen)
    db.commit()
    db.refresh(gen)
    return _format(gen)


@history_router.get("/", response_model=List[GenerationOut])
def list_generations(
    skip:         int     = Query(default=0,  ge=0),
    limit:        int     = Query(default=20, ge=1, le=100),
    current_user: User    = Depends(get_current_user),
    db:           Session = Depends(get_db),
):
    """Return the user's generation history, newest first."""
    gens = (
        db.query(Generation)
        .filter(Generation.user_id == current_user.id)
        .order_by(Generation.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_format(g) for g in gens]


@history_router.get("/{generation_id}", response_model=GenerationOut)
def get_generation(
    generation_id: str,
    current_user:  User    = Depends(get_current_user),
    db:            Session = Depends(get_db),
):
    gen = db.query(Generation).filter(
        Generation.id == generation_id,
        Generation.user_id == current_user.id,
    ).first()
    if gen is None:
        raise HTTPException(status_code=404, detail="Generation not found.")
    return _format(gen)


@history_router.delete("/{generation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_generation(
    generation_id: str,
    current_user:  User    = Depends(get_current_user),
    db:            Session = Depends(get_db),
):
    gen = db.query(Generation).filter(
        Generation.id == generation_id,
        Generation.user_id == current_user.id,
    ).first()
    if gen is None:
        raise HTTPException(status_code=404, detail="Generation not found.")
    db.delete(gen)
    db.commit()


def _format(gen: Generation) -> dict:
    return {
        "id":          gen.id,
        "hairstyle":   gen.hairstyle,
        "style_name":  gen.style_name,
        "face_shape":  gen.face_shape,
        "result_url":  gen.result_url,
        "pipeline":    gen.pipeline,
        "duration_ms": gen.duration_ms,
        "created_at":  gen.created_at.isoformat() if gen.created_at else None,
    }
