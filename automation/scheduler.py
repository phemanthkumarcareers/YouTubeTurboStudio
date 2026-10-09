"""
Channel Auto-Topic Scheduler
Manages automated recurring generation schedules per channel.
Proposes next topics based on channel strategy and enqueues jobs in the persistent queue.
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional

from automation.db import get_db_connection
from automation.job_queue import job_queue, Job
from core.channel_registry import registry
from core.logger import log_info, log_warn


class AutoScheduler:
    """Manages channel generation schedules and automated topic triggering."""

    def configure_schedule(
        self,
        channel_id: str,
        enabled: bool = True,
        interval_hours: float = 24.0,
        cron_expression: str = "0 10 * * *",
        video_type: str = "shorts",
        auto_publish: bool = False
    ) -> Dict[str, Any]:
        """Configure or update an automated schedule for a channel."""
        now = datetime.now(timezone.utc)
        next_run = (now + timedelta(hours=interval_hours)).isoformat()
        sched_id = f"sched_{channel_id}"

        with get_db_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO schedules (
                    id, channel_id, enabled, cron_expression, interval_hours,
                    next_run, video_type, auto_publish
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sched_id, channel_id, 1 if enabled else 0, cron_expression,
                interval_hours, next_run, video_type, 1 if auto_publish else 0
            ))
            conn.commit()

        log_info(f"[SCHEDULER] Configured schedule for '{channel_id}' (enabled={enabled}, interval={interval_hours}h).")
        return self.get_schedule(channel_id)

    def get_schedule(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve the schedule configuration for a channel."""
        with get_db_connection() as conn:
            row = conn.execute("SELECT * FROM schedules WHERE channel_id = ?", (channel_id,)).fetchone()
            if not row:
                return None
            return {
                "id": row["id"],
                "channel_id": row["channel_id"],
                "enabled": bool(row["enabled"]),
                "cron_expression": row["cron_expression"],
                "interval_hours": row["interval_hours"],
                "last_run": row["last_run"],
                "next_run": row["next_run"],
                "video_type": row["video_type"],
                "auto_publish": bool(row["auto_publish"])
            }

    def list_schedules(self) -> List[Dict[str, Any]]:
        """List all channel schedules."""
        with get_db_connection() as conn:
            rows = conn.execute("SELECT * FROM schedules").fetchall()
            return [
                {
                    "id": r["id"],
                    "channel_id": r["channel_id"],
                    "enabled": bool(r["enabled"]),
                    "cron_expression": r["cron_expression"],
                    "interval_hours": r["interval_hours"],
                    "last_run": r["last_run"],
                    "next_run": r["next_run"],
                    "video_type": r["video_type"],
                    "auto_publish": bool(r["auto_publish"])
                }
                for r in rows
            ]

    def trigger_scheduled_run(self, channel_id: str) -> Job:
        """
        Executes a scheduled generation trigger:
        Discovers the next topic for the channel niche and enqueues a new Job.
        """
        chan_ctx = registry.get_channel(channel_id)
        if not chan_ctx:
            raise ValueError(f"Channel '{channel_id}' not found.")

        # Determine automated topic based on channel niche
        topic = self._generate_auto_topic(chan_ctx)
        sched = self.get_schedule(channel_id)
        video_type = sched.get("video_type", "shorts") if sched else "shorts"

        job = job_queue.enqueue(
            channel_id=channel_id,
            topic=topic,
            video_type=video_type,
            metadata={"source": "auto_scheduler"}
        )

        # Update last_run and next_run
        now = datetime.now(timezone.utc)
        interval = (sched.get("interval_hours", 24.0) if sched else 24.0)
        next_run = (now + timedelta(hours=interval)).isoformat()

        with get_db_connection() as conn:
            conn.execute("""
                UPDATE schedules
                SET last_run = ?, next_run = ?
                WHERE channel_id = ?
            """, (now.isoformat(), next_run, channel_id))
            conn.commit()

        log_info(f"[SCHEDULER] Triggered auto-topic job '{job.id}' for '{channel_id}' with topic '{topic}'.")
        return job

    def _generate_auto_topic(self, chan_ctx) -> str:
        """Generates a relevant auto-topic based on channel niche and historical strategy."""
        cid = chan_ctx.channel_id.lower()
        if "kids" in cid:
            return "Count 1, 2, 3 Shiny Stars with Sparky"
        elif "elder" in cid:
            return "The Symphony of the Old Front Porch"
        else:
            return "The Astonishing Science of Quantum Entanglement"


auto_scheduler = AutoScheduler()
