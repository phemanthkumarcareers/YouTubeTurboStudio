"""
Per-Channel Dashboards & Aggregates
Aggregates job statuses, review queue backlogs, analytics, and strategy insights
for real-time dashboard presentation.
"""
from typing import Dict, Any, Optional

from automation.job_queue import job_queue
from automation.review_queue import review_queue
from automation.analytics import analytics_manager
from automation.learning_loop import learning_loop
from automation.scheduler import auto_scheduler
from core.channel_registry import registry


class DashboardService:
    """Consolidates channel health, automation queues, and metrics into a unified dashboard."""

    def get_channel_dashboard(self, channel_id: str) -> Dict[str, Any]:
        """Compile complete operational dashboard for the requested channel."""
        chan_ctx = registry.get_channel(channel_id)
        chan_name = chan_ctx.name if chan_ctx else channel_id

        # 1. Job Queue Stats
        channel_jobs = job_queue.list_jobs(channel_id=channel_id, limit=100)
        queued_count = sum(1 for j in channel_jobs if j.status == "queued")
        running_count = sum(1 for j in channel_jobs if j.status in ("researching", "scripting", "rendering", "qc"))
        ready_count = sum(1 for j in channel_jobs if j.status == "ready")
        failed_count = sum(1 for j in channel_jobs if j.status == "failed")

        # 2. Review Queue Stats
        pending_reviews = review_queue.list_pending(channel_id=channel_id)

        # 3. Channel Analytics Summary
        analytics_summary = analytics_manager.get_channel_summary(channel_id)

        # 4. Learning Loop Strategy
        strategy = learning_loop.get_strategy_recommendation(channel_id)

        # 5. Scheduling Status
        schedule = auto_scheduler.get_schedule(channel_id)

        return {
            "channel_id": channel_id,
            "channel_name": chan_name,
            "engine": chan_ctx.engine if chan_ctx else "media_video",
            "jobs": {
                "total": len(channel_jobs),
                "queued": queued_count,
                "running": running_count,
                "ready": ready_count,
                "failed": failed_count,
                "recent": [j.to_dict() for j in channel_jobs[:5]]
            },
            "review_queue": {
                "pending_count": len(pending_reviews),
                "items": pending_reviews[:5]
            },
            "analytics": analytics_summary,
            "learning_strategy": strategy,
            "schedule": schedule
        }


dashboard_service = DashboardService()
