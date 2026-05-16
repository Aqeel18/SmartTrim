"""
Job Queue — in-process async job store for SmartTrim 360.

Manages the lifecycle of background inference jobs so the /preview-async
endpoint can return immediately with a job_id and the client can poll
GET /jobs/{job_id} or subscribe via WebSocket /ws/job/{job_id}.

Architecture note:
  This uses a thread-safe in-memory dict suitable for a single-worker
  deployment.  To scale horizontally, swap _store with a Redis-backed
  implementation (e.g. via redis-py) — the public interface is identical.
"""

import uuid
import asyncio
import time
from enum import Enum
from typing import Any, Dict, Optional


class JobStatus(str, Enum):
    PENDING    = "pending"
    PROCESSING = "processing"
    DONE       = "done"
    FAILED     = "failed"


class Job:
    __slots__ = ("job_id", "status", "progress", "message", "result",
                 "error", "created_at", "updated_at")

    def __init__(self, job_id: str):
        self.job_id:     str           = job_id
        self.status:     JobStatus     = JobStatus.PENDING
        self.progress:   int           = 0          # 0-100
        self.message:    str           = "Queued"
        self.result:     Optional[Any] = None       # bytes when done
        self.error:      Optional[str] = None
        self.created_at: float         = time.time()
        self.updated_at: float         = time.time()

    def to_dict(self) -> Dict:
        return {
            "job_id":     self.job_id,
            "status":     self.status.value,
            "progress":   self.progress,
            "message":    self.message,
            "error":      self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class JobStore:
    """Thread-safe, in-process job store."""

    _TTL_SECONDS = 3600   # evict jobs older than 1 hour

    def __init__(self):
        self._store: Dict[str, Job] = {}
        self._lock  = asyncio.Lock()
        # Event per job_id — WebSocket listeners wait on this
        self._events: Dict[str, asyncio.Event] = {}

    async def create(self) -> Job:
        job_id = str(uuid.uuid4())
        job    = Job(job_id)
        async with self._lock:
            self._store[job_id]  = job
            self._events[job_id] = asyncio.Event()
        return job

    async def get(self, job_id: str) -> Optional[Job]:
        async with self._lock:
            return self._store.get(job_id)

    async def update(self, job_id: str, **kwargs) -> None:
        """Update job fields and notify any WebSocket listeners."""
        async with self._lock:
            job = self._store.get(job_id)
            if job is None:
                return
            for k, v in kwargs.items():
                if hasattr(job, k):
                    setattr(job, k, v)
            job.updated_at = time.time()

        # Signal waiters
        ev = self._events.get(job_id)
        if ev:
            ev.set()
            ev.clear()

    async def wait_for_update(self, job_id: str, timeout: float = 30.0) -> None:
        """Block until the job is updated or timeout expires."""
        ev = self._events.get(job_id)
        if ev:
            try:
                await asyncio.wait_for(ev.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                pass

    async def evict_old_jobs(self) -> None:
        """Remove jobs older than _TTL_SECONDS. Call periodically."""
        cutoff = time.time() - self._TTL_SECONDS
        async with self._lock:
            stale = [jid for jid, j in self._store.items()
                     if j.created_at < cutoff]
            for jid in stale:
                del self._store[jid]
                self._events.pop(jid, None)


# Singleton — imported by routes and the inference runner
job_store = JobStore()
