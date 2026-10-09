"""
Review Queue — Human-in-the-Loop Publishing Gate
Ensures every generated video requires explicit review and approval before live upload,
displaying channel identity, format, Made-for-Kids status, and QC scores.
"""
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from automation.db import get_db_connection
from core.channel_registry import registry
from core.logger import log_info, log_warn


class ReviewQueueManager:
    """Manages videos awaiting human approval prior to publishing."""

    def submit_for_review(
        self,
        job_id: str,
        channel_id: str,
        title: str,
        format_type: str,
        made_for_kids: bool,
        qc_score: float,
        video_path: str
    ) -> bool:
        """Submit a successfully generated video to the review queue."""
        now = datetime.now(timezone.utc).isoformat()
        with get_db_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO review_queue (
                    job_id, channel_id, title, format, made_for_kids,
                    qc_score, video_path, status, submitted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
            """, (
                job_id, channel_id, title, format_type,
                1 if made_for_kids else 0, qc_score, video_path, now
            ))
            conn.commit()

        log_info(f"[REVIEW QUEUE] Video for job '{job_id}' ({channel_id}) submitted for review (QC: {qc_score:.1f}).")
        return True

    def list_pending(self, channel_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all videos pending human approval."""
        query = "SELECT * FROM review_queue WHERE status = 'pending'"
        params = []
        if channel_id:
            query += " AND channel_id = ?"
            params.append(channel_id)
        query += " ORDER BY submitted_at DESC"

        with get_db_connection() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
            items = []
            for r in rows:
                chan_ctx = registry.get_channel(r["channel_id"])
                chan_name = chan_ctx.name if chan_ctx else r["channel_id"]
                items.append({
                    "job_id": r["job_id"],
                    "channel_id": r["channel_id"],
                    "channel_name": chan_name,
                    "title": r["title"],
                    "format": r["format"],
                    "made_for_kids": bool(r["made_for_kids"]),
                    "qc_score": r["qc_score"],
                    "video_path": r["video_path"],
                    "status": r["status"],
                    "submitted_at": r["submitted_at"]
                })
            return items

    def approve(self, job_id: str, notes: str = "") -> bool:
        """Approve a video for publishing."""
        now = datetime.now(timezone.utc).isoformat()
        with get_db_connection() as conn:
            cur = conn.execute("""
                UPDATE review_queue
                SET status = 'approved', reviewed_at = ?, review_notes = ?
                WHERE job_id = ?
            """, (now, notes, job_id))
            conn.commit()
            if cur.rowcount > 0:
                log_info(f"[REVIEW QUEUE] Job '{job_id}' APPROVED for publish.")
                return True
            return False

    def reject(self, job_id: str, notes: str = "") -> bool:
        """Reject a video."""
        now = datetime.now(timezone.utc).isoformat()
        with get_db_connection() as conn:
            cur = conn.execute("""
                UPDATE review_queue
                SET status = 'rejected', reviewed_at = ?, review_notes = ?
                WHERE job_id = ?
            """, (now, notes, job_id))
            conn.commit()
            if cur.rowcount > 0:
                log_info(f"[REVIEW QUEUE] Job '{job_id}' REJECTED.")
                return True
            return False

    def is_approved(self, job_id: str) -> bool:
        """Check if a video has been explicitly approved."""
        with get_db_connection() as conn:
            row = conn.execute("SELECT status FROM review_queue WHERE job_id = ?", (job_id,)).fetchone()
            if row and row["status"] == "approved":
                return True
            return False


review_queue = ReviewQueueManager()
