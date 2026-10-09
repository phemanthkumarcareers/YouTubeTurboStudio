"""
Heavy Render Worker — Single Heavy Worker Engine
Processes persistent queued jobs with a single-worker default to avoid CPU/GPU thrashing.
Updates job stage progress, validates QC, and routes completed videos to the Review Queue.
"""
import time
import threading
from typing import Optional

from automation.job_queue import job_queue, Job
from automation.review_queue import review_queue
from core.channel_registry import registry
from core.pipeline_router import route_and_execute
from core.logger import log_info, log_warn, log_error


class HeavyRenderWorker:
    """Single concurrent background worker for resource-intensive video renders."""

    def __init__(self, max_workers: int = 1):
        self.max_workers = max_workers
        self._stop_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None
        self._is_running = False

    def start(self):
        """Starts the background worker loop."""
        if self._is_running:
            return
        self._stop_event.clear()
        self._is_running = True
        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            daemon=True,
            name="heavy-render-worker-1"
        )
        self._worker_thread.start()
        log_info(f"[WORKER] Heavy Render Worker started (concurrency={self.max_workers}).")

    def stop(self):
        """Stops the worker loop gracefully."""
        self._stop_event.set()
        self._is_running = False
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=3.0)
        log_info("[WORKER] Heavy Render Worker stopped.")

    def _worker_loop(self):
        while not self._stop_event.is_set():
            job = job_queue.get_next_queued_job()
            if job:
                try:
                    self.execute_job_sync(job.id)
                except Exception as e:
                    log_error(f"[WORKER] Unexpected error executing job '{job.id}': {e}")
            else:
                # Sleep briefly before polling queue
                time.sleep(1.5)

    def execute_job_sync(self, job_id: str) -> Job:
        """
        Executes a specific job synchronously to completion.
        Useful for deterministic automated tests and immediate processing.
        """
        job = job_queue.get_job(job_id)
        if not job:
            raise ValueError(f"Job '{job_id}' not found.")

        chan_ctx = registry.get_channel(job.channel_id)
        if not chan_ctx:
            job_queue.update_job_status(job_id, status="failed", error=f"Channel '{job.channel_id}' not found.")
            return job_queue.get_job(job_id)

        try:
            log_info(f"[WORKER] Executing job '{job_id}' for channel '{chan_ctx.name}'...")
            job_queue.update_job_status(job_id, status="researching", current_stage="research", progress_pct=15)

            # Dispatch through pipeline router
            pipeline_thread = route_and_execute(
                channel_context=chan_ctx,
                topic_override=job.topic,
                video_type=job.video_type
            )

            # If background thread returned, await completion
            if pipeline_thread and hasattr(pipeline_thread, "join"):
                pipeline_thread.join(timeout=300.0)

            # Inspect pipeline outcome from state
            from core.state import state
            video_path = state.get("video_path")
            pipeline_err = state.get("error")

            if pipeline_err:
                job_queue.update_job_status(job_id, status="failed", error=pipeline_err)
                return job_queue.get_job(job_id)

            if not video_path:
                job_queue.update_job_status(job_id, status="failed", error="Pipeline finished without output video.")
                return job_queue.get_job(job_id)

            # Determine QC Score
            qc_score = 90.0  # Default good
            qc_rep = state.get("qc_report")
            if qc_rep and isinstance(qc_rep, dict):
                qc_score = float(qc_rep.get("score", 90.0))

            # Update job as ready
            job_queue.update_job_status(
                job_id=job_id,
                status="ready",
                current_stage="done",
                progress_pct=100,
                output_path=video_path,
                qc_score=qc_score
            )

            # Submit to human review queue (do not auto-publish)
            is_made_for_kids = bool(chan_ctx.youtube.get("made_for_kids", False))
            review_queue.submit_for_review(
                job_id=job_id,
                channel_id=chan_ctx.channel_id,
                title=job.topic,
                format_type=job.video_type,
                made_for_kids=is_made_for_kids,
                qc_score=qc_score,
                video_path=video_path
            )

            log_info(f"[WORKER] Job '{job_id}' successfully completed! Video ready for review at '{video_path}'.")
            return job_queue.get_job(job_id)

        except Exception as e:
            import traceback
            err_msg = traceback.format_exc()
            log_error(f"[WORKER] Job '{job_id}' failed: {err_msg}")
            job_queue.update_job_status(job_id, status="failed", error=str(e))
            return job_queue.get_job(job_id)


# Global singleton worker
heavy_worker = HeavyRenderWorker(max_workers=1)
