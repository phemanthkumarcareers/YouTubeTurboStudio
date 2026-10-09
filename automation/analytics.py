"""
Channel-Partitioned Analytics Ingestion
Ingests, stores, and aggregates per-video performance metrics strictly partitioned
by channel. Ensures zero data leakage between Science, Kids, and Elders channels.
"""
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from automation.db import get_db_connection
from core.logger import log_info, log_warn


class AnalyticsManager:
    """Manages channel-isolated performance metrics without data fabrication."""

    def ingest_metrics(
        self,
        channel_id: str,
        video_id: str,
        title: str,
        format_type: str = "shorts",
        views: int = 0,
        likes: int = 0,
        comments: int = 0,
        watch_time_hours: float = 0.0,
        avg_view_duration_sec: float = 0.0,
        avg_view_pct: float = 0.0,
        subscribers_gained: int = 0
    ) -> int:
        """
        Record verified performance metrics for a video.
        Strictly partitions by channel_id.
        """
        if not channel_id:
            raise ValueError("Analytics ingestion requires a channel_id.")
        if not video_id:
            raise ValueError("Analytics ingestion requires a video_id.")

        now = datetime.now(timezone.utc).isoformat()
        with get_db_connection() as conn:
            cur = conn.execute("""
                INSERT INTO analytics (
                    channel_id, video_id, title, format, views, likes, comments,
                    watch_time_hours, avg_view_duration_sec, avg_view_pct,
                    subscribers_gained, recorded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                channel_id, video_id, title, format_type, views, likes, comments,
                watch_time_hours, avg_view_duration_sec, avg_view_pct,
                subscribers_gained, now
            ))
            conn.commit()
            return cur.lastrowid

    def get_channel_metrics(
        self,
        channel_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Retrieve metrics strictly for the requested channel.
        Zero cross-channel contamination.
        """
        with get_db_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM analytics
                WHERE channel_id = ?
                ORDER BY recorded_at DESC
                LIMIT ?
            """, (channel_id, limit)).fetchall()
            return [dict(r) for r in rows]

    def get_channel_summary(self, channel_id: str) -> Dict[str, Any]:
        """Calculates aggregate performance statistics for a specific channel."""
        with get_db_connection() as conn:
            row = conn.execute("""
                SELECT
                    COUNT(*) as video_count,
                    COALESCE(SUM(views), 0) as total_views,
                    COALESCE(SUM(likes), 0) as total_likes,
                    COALESCE(SUM(comments), 0) as total_comments,
                    COALESCE(SUM(watch_time_hours), 0.0) as total_watch_time,
                    COALESCE(AVG(avg_view_pct), 0.0) as avg_retention_pct,
                    COALESCE(SUM(subscribers_gained), 0) as total_subs
                FROM analytics
                WHERE channel_id = ?
            """, (channel_id,)).fetchone()

            return {
                "channel_id": channel_id,
                "video_count": row["video_count"],
                "total_views": row["total_views"],
                "total_likes": row["total_likes"],
                "total_comments": row["total_comments"],
                "total_watch_time_hours": round(row["total_watch_time"], 2),
                "avg_retention_pct": round(row["avg_retention_pct"], 1),
                "total_subscribers_gained": row["total_subs"]
            }


analytics_manager = AnalyticsManager()
