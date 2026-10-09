"""
Persistent Job Queue & Lifecycle Management
Provides resilient job lifecycle tracking with strict channel immutability,
status transitions, and retry/resumability.
"""
import uuid
import json
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any

from automation.db import get_db_connection
from core.logger import log_info, log_warn, log_error


VALID_JOB_STATUSES = [
    "queued",
    "researching",
    "scripting",
    "reviewing",
    "storyboarding",
    "acquiring_assets",
    "generating_audio",
    "rendering",
    "qc",
    "ready",
    "publishing",
    "published",
    "failed",
    "cancelled"
]


class ImmutableJobError(ValueError):
    """Raised when attempting to modify an immutable job property (e.g. channel_id)."""
    pass


@dataclass
class Job:
    id: str
    _channel_id: str
    video_type: str = "shorts"
    topic: str = ""
    status: str = "queued"
    current_stage: str = "queued"
    progress_pct: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    output_path: Optional[str] = None
    qc_score: Optional[float] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def channel_id(self) -> str:
        return self._channel_id

    @channel_id.setter
    def channel_id(self, value: str):
        # Enforce job channel immutability requirement from Section 56
        if hasattr(self, "_channel_id") and self._channel_id and self._channel_id != value:
            raise ImmutableJobError(f"Job channel_id is immutable. Cannot change '{self._channel_id}' to '{value}'.")
        self._channel_id = value

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["channel_id"] = self._channel_id
        del d["_channel_id"]
        return d


class JobQueueManager:
    """Manages persistent generation jobs stored in SQLite."""

    def enqueue(
        self,
        channel_id: str,
        topic: str,
        video_type: str = "shorts",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Job:
        """Create and enqueue a new generation job."""
        if not channel_id or not str(channel_id).strip():
            raise ValueError("Job requires a valid channel_id.")
        if not topic or not str(topic).strip():
            raise ValueError("Job requires a non-empty topic.")

        job_id = f"job_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        meta = metadata or {}

        with get_db_connection() as conn:
            conn.execute("""
                INSERT INTO jobs (
                    id, channel_id, video_type, topic, status, current_stage,
                    progress_pct, created_at, metadata_json
                ) VALUES (?, ?, ?, ?, 'queued', 'queued', 0, ?, ?)
            """, (job_id, channel_id, video_type, topic, now, json.dumps(meta)))
            conn.commit()

        job = Job(
            id=job_id,
            _channel_id=channel_id,
            video_type=video_type,
            topic=topic,
            status="queued",
            current_stage="queued",
            created_at=now,
            metadata=meta
        )
        log_info(f"[JOB QUEUE] Enqueued job '{job.id}' for channel '{channel_id}' (topic: '{topic}')")
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        """Fetch a job by ID."""
        with get_db_connection() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if not row:
                return None
            return self._row_to_job(row)

    def get_next_queued_job(self) -> Optional[Job]:
        """Retrieve the oldest pending job in the queue."""
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT * FROM jobs WHERE status = 'queued' ORDER BY created_at ASC LIMIT 1"
            ).fetchone()
            if not row:
                return None
            return self._row_to_job(row)

    def list_jobs(
        self,
        channel_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Job]:
        """List jobs filtered by channel and status."""
        query = "SELECT * FROM jobs WHERE 1=1"
        params = []
        if channel_id:
            query += " AND channel_id = ?"
            params.append(channel_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with get_db_connection() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
            return [self._row_to_job(r) for r in rows]

    def update_job_status(
        self,
        job_id: str,
        status: str,
        current_stage: Optional[str] = None,
        progress_pct: Optional[int] = None,
        output_path: Optional[str] = None,
        qc_score: Optional[float] = None,
        error: Optional[str] = None,
        clear_error: bool = False
    ) -> bool:
        """Update job execution state in the persistent store."""
        if status not in VALID_JOB_STATUSES:
            raise ValueError(f"Invalid job status: {status}")

        updates = ["status = ?"]
        params = [status]

        if current_stage is not None:
            updates.append("current_stage = ?")
            params.append(current_stage)
        if progress_pct is not None:
            updates.append("progress_pct = ?")
            params.append(progress_pct)
        if output_path is not None:
            updates.append("output_path = ?")
            params.append(output_path)
        if qc_score is not None:
            updates.append("qc_score = ?")
            params.append(qc_score)
        if clear_error:
            updates.append("error = NULL")
        elif error is not None:
            updates.append("error = ?")
            params.append(error)

        if status in ("researching", "started"):
            updates.append("started_at = ?")
            params.append(datetime.now(timezone.utc).isoformat())
        elif status in ("ready", "failed", "cancelled", "published"):
            updates.append("completed_at = ?")
            params.append(datetime.now(timezone.utc).isoformat())

        params.append(job_id)
        sql = f"UPDATE jobs SET {', '.join(updates)} WHERE id = ?"

        with get_db_connection() as conn:
            cur = conn.execute(sql, tuple(params))
            conn.commit()
            return cur.rowcount > 0

    def retry_job(self, job_id: str) -> Optional[Job]:
        """Reset a failed or cancelled job back to queued status."""
        job = self.get_job(job_id)
        if not job:
            return None
        if job.status not in ("failed", "cancelled"):
            log_warn(f"[JOB QUEUE] Job '{job_id}' is in status '{job.status}', cannot retry.")
            return job

        self.update_job_status(
            job_id=job_id,
            status="queued",
            current_stage="queued",
            progress_pct=0,
            clear_error=True
        )
        log_info(f"[JOB QUEUE] Retrying job '{job_id}'")
        return self.get_job(job_id)

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a queued or active job."""
        return self.update_job_status(job_id, status="cancelled", error="Cancelled by user")

    def _row_to_job(self, row) -> Job:
        meta = {}
        try:
            if row["metadata_json"]:
                meta = json.loads(row["metadata_json"])
        except Exception:
            meta = {}

        return Job(
            id=row["id"],
            _channel_id=row["channel_id"],
            video_type=row["video_type"],
            topic=row["topic"],
            status=row["status"],
            current_stage=row["current_stage"],
            progress_pct=row["progress_pct"],
            created_at=row["created_at"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            output_path=row["output_path"],
            qc_score=row["qc_score"],
            error=row["error"],
            metadata=meta
        )


job_queue = JobQueueManager()
