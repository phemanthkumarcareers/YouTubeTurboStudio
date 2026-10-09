"""
Automation, Scheduling & Analytics Package
Provides persistent job queue, single heavy worker, review queue,
channel-partitioned analytics, per-channel dashboards, and learning loop.
"""
from automation.db import init_db, get_db_connection
from automation.job_queue import Job, JobQueueManager, job_queue, ImmutableJobError
from automation.worker import HeavyRenderWorker, heavy_worker
from automation.review_queue import ReviewQueueManager, review_queue
from automation.scheduler import AutoScheduler, auto_scheduler
from automation.analytics import AnalyticsManager, analytics_manager
from automation.learning_loop import LearningLoop, learning_loop
from automation.dashboard import DashboardService, dashboard_service

__all__ = [
    "init_db",
    "get_db_connection",
    "Job",
    "JobQueueManager",
    "job_queue",
    "ImmutableJobError",
    "HeavyRenderWorker",
    "heavy_worker",
    "ReviewQueueManager",
    "review_queue",
    "AutoScheduler",
    "auto_scheduler",
    "AnalyticsManager",
    "analytics_manager",
    "LearningLoop",
    "learning_loop",
    "DashboardService",
    "dashboard_service"
]
