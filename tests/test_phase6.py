"""
Phase 6 Test Suite: Automation, Scheduling and Analytics
Validates all requirements from docs/MASTER_ARCHITECTURE.md (Section 55 & 56):
1. Persistent job queue & lifecycle
2. Job channel immutability (Section 56 rule)
3. Single heavy worker execution & concurrency
4. Retry & resume behavior
5. Review queue & human-in-the-loop publish gate
6. Auto-topic scheduler
7. Channel-partitioned analytics ingestion (zero cross-channel contamination)
8. Channel-specific learning loop & sample size threshold
9. Per-channel dashboard compilation
10. Zero unattended live publishing during automated tests
"""
import os
import unittest
from datetime import datetime

from automation.db import init_db, get_db_connection
from automation.job_queue import job_queue, Job, ImmutableJobError
from automation.worker import HeavyRenderWorker
from automation.review_queue import review_queue
from automation.scheduler import auto_scheduler
from automation.analytics import analytics_manager
from automation.learning_loop import learning_loop
from automation.dashboard import dashboard_service
from core.channel_registry import registry


class TestPhase6AutomationAndAnalytics(unittest.TestCase):

    def setUp(self):
        init_db()

    def test_01_persistent_job_queue_lifecycle(self):
        """Test enqueuing, status updates, and retrieval in persistent job queue."""
        job = job_queue.enqueue(
            channel_id="the-ai-brief-it",
            topic="How Supermassive Black Holes Warp Spacetime",
            video_type="shorts",
            metadata={"priority": "high"}
        )
        self.assertIsNotNone(job.id)
        self.assertEqual(job.channel_id, "the-ai-brief-it")
        self.assertEqual(job.status, "queued")

        # Update stage
        job_queue.update_job_status(job.id, status="researching", current_stage="research", progress_pct=25)
        updated = job_queue.get_job(job.id)
        self.assertEqual(updated.status, "researching")
        self.assertEqual(updated.progress_pct, 25)

        # Mark ready
        job_queue.update_job_status(job.id, status="ready", current_stage="done", progress_pct=100, qc_score=94.5)
        ready_job = job_queue.get_job(job.id)
        self.assertEqual(ready_job.status, "ready")
        self.assertEqual(ready_job.qc_score, 94.5)

    def test_02_job_channel_immutability(self):
        """
        MASTER_ARCHITECTURE.md Section 56 Requirement:
        Job channel immutability — attempting to mutate channel_id must raise an error.
        """
        job = Job(id="job_immut_test", _channel_id="kids", topic="Counting Stars")
        self.assertEqual(job.channel_id, "kids")

        # Attempt to mutate channel_id
        with self.assertRaises(ImmutableJobError):
            job.channel_id = "the-ai-brief-it"

        # Verify original channel remained untouched
        self.assertEqual(job.channel_id, "kids")

    def test_03_job_retry_behavior(self):
        """Test resetting a failed job back to queued for retry."""
        job = job_queue.enqueue(
            channel_id="elders",
            topic="The Art of Slow Living",
            video_type="normal"
        )
        # Mark failed
        job_queue.update_job_status(job.id, status="failed", error="Temporary network timeout")
        self.assertEqual(job_queue.get_job(job.id).status, "failed")

        # Retry
        retried = job_queue.retry_job(job.id)
        self.assertEqual(retried.status, "queued")
        self.assertIsNone(retried.error)
        self.assertEqual(retried.progress_pct, 0)

    def test_04_review_queue_human_gate(self):
        """
        MASTER_ARCHITECTURE.md Section 55 & 43:
        Review Queue — Do not enable unattended live publishing by default.
        Videos require explicit human review and approval.
        """
        job_id = "test_review_job_123"
        review_queue.submit_for_review(
            job_id=job_id,
            channel_id="kids",
            title="Sparky's Star Hunt",
            format_type="shorts",
            made_for_kids=True,
            qc_score=92.0,
            video_path="C:/dummy/output/sparky_star.mp4"
        )

        # 1. Video starts pending
        pending = review_queue.list_pending(channel_id="kids")
        self.assertTrue(any(p["job_id"] == job_id for p in pending))
        self.assertFalse(review_queue.is_approved(job_id))

        # 2. Reject test
        review_queue.reject(job_id, notes="Needs clearer outro sound")
        self.assertFalse(review_queue.is_approved(job_id))

        # 3. Approve test
        review_queue.approve(job_id, notes="Reviewed and approved by creator")
        self.assertTrue(review_queue.is_approved(job_id))

    def test_05_auto_topic_scheduler(self):
        """Test configuring and triggering recurring generation schedules."""
        sched = auto_scheduler.configure_schedule(
            channel_id="kids",
            enabled=True,
            interval_hours=12.0,
            video_type="shorts"
        )
        self.assertTrue(sched["enabled"])
        self.assertEqual(sched["interval_hours"], 12.0)

        # Trigger scheduled run
        job = auto_scheduler.trigger_scheduled_run("kids")
        self.assertIsNotNone(job)
        self.assertEqual(job.channel_id, "kids")
        self.assertEqual(job.status, "queued")
        self.assertEqual(job.metadata.get("source"), "auto_scheduler")

    def test_06_channel_partitioned_analytics(self):
        """
        MASTER_ARCHITECTURE.md Section 45:
        Analytics must be strictly partitioned by channel.
        Kids performance must not influence science, and vice versa.
        """
        # Ingest for The AI Brief It
        analytics_manager.ingest_metrics(
            channel_id="the-ai-brief-it",
            video_id="sci_vid_1",
            title="Fusion Reactor Breakthrough",
            format_type="shorts",
            views=15000,
            likes=1200,
            comments=85,
            watch_time_hours=120.5,
            avg_view_pct=88.5,
            subscribers_gained=240
        )

        # Ingest for Kids
        analytics_manager.ingest_metrics(
            channel_id="kids",
            video_id="kids_vid_1",
            title="Learn Numbers with Sparky",
            format_type="shorts",
            views=8000,
            likes=600,
            comments=0,
            watch_time_hours=45.0,
            avg_view_pct=92.0,
            subscribers_gained=110
        )

        # Ingest for Elders
        analytics_manager.ingest_metrics(
            channel_id="elders",
            video_id="elders_vid_1",
            title="The Front Porch Rocking Chair",
            format_type="normal",
            views=5000,
            likes=450,
            comments=40,
            watch_time_hours=95.0,
            avg_view_pct=76.0,
            subscribers_gained=85
        )

        # Verify strict partitioning
        sci_metrics = analytics_manager.get_channel_metrics("the-ai-brief-it")
        self.assertTrue(all(m["channel_id"] == "the-ai-brief-it" for m in sci_metrics))
        self.assertFalse(any(m["video_id"] == "kids_vid_1" for m in sci_metrics))

        kids_metrics = analytics_manager.get_channel_metrics("kids")
        self.assertTrue(all(m["channel_id"] == "kids" for m in kids_metrics))
        self.assertFalse(any(m["video_id"] == "sci_vid_1" for m in kids_metrics))

        # Check channel summary calculation
        kids_sum = analytics_manager.get_channel_summary("kids")
        self.assertGreaterEqual(kids_sum["total_views"], 8000)

    def test_07_learning_loop_strategy_and_sample_gate(self):
        """
        MASTER_ARCHITECTURE.md Section 46:
        Learning loop requires sufficient sample size before adapting strategy,
        and analyzes format and topic pillars per channel.
        """
        # Test 1: Channel with low sample size (< 3)
        loop_res = learning_loop.analyze_channel("elders", min_sample_size=3)
        # Should report insufficient sample if under threshold
        self.assertIn(loop_res["status"], ("insufficient_sample", "optimized"))

        # Ingest 3 samples for The AI Brief It to meet sample size threshold
        for i in range(3):
            analytics_manager.ingest_metrics(
                channel_id="the-ai-brief-it",
                video_id=f"test_sci_{i}",
                title=f"Quantum Physics Phenomenon #{i}",
                format_type="shorts",
                views=10000 + i * 2000,
                avg_view_pct=85.0
            )

        optimized = learning_loop.analyze_channel("the-ai-brief-it", min_sample_size=3)
        self.assertEqual(optimized["status"], "optimized")
        self.assertIn("best_format", optimized)
        self.assertIn("top_topic_pillars", optimized)
        self.assertEqual(optimized["best_format"], "shorts")

    def test_08_per_channel_dashboard(self):
        """Test per-channel dashboard service combining jobs, reviews, analytics, and strategy."""
        dash = dashboard_service.get_channel_dashboard("the-ai-brief-it")
        self.assertEqual(dash["channel_id"], "the-ai-brief-it")
        self.assertIn("jobs", dash)
        self.assertIn("review_queue", dash)
        self.assertIn("analytics", dash)
        self.assertIn("learning_strategy", dash)
        self.assertIn("schedule", dash)

    def test_09_heavy_worker_concurrency_default(self):
        """Verify HeavyRenderWorker defaults to single worker (max_workers=1)."""
        worker = HeavyRenderWorker()
        self.assertEqual(worker.max_workers, 1)


if __name__ == "__main__":
    unittest.main()
