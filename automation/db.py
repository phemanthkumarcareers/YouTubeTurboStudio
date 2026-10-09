"""
Automation Database — SQLite Persistent Store
Stores persistent jobs, review queue, schedules, channel-partitioned analytics,
and learning loop insights in runtime/studio.db.
"""
import os
import sqlite3
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

RUNTIME_DIR = Path(__file__).resolve().parent.parent / "runtime"
DB_PATH = RUNTIME_DIR / "studio.db"
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)


def get_db_connection() -> sqlite3.Connection:
    """Return a thread-safe connection to the persistent database."""
    conn = sqlite3.connect(str(DB_PATH), timeout=20.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes tables and indexes for Phase 6 automation entities."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 1. Persistent Jobs Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                channel_id TEXT NOT NULL,
                video_type TEXT NOT NULL DEFAULT 'shorts',
                topic TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'queued',
                current_stage TEXT NOT NULL DEFAULT 'queued',
                progress_pct INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                output_path TEXT,
                qc_score REAL,
                error TEXT,
                metadata_json TEXT DEFAULT '{}'
            );
        """)

        # 2. Review Queue Table (Human-in-the-loop before publishing)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS review_queue (
                job_id TEXT PRIMARY KEY,
                channel_id TEXT NOT NULL,
                title TEXT NOT NULL,
                format TEXT NOT NULL DEFAULT 'shorts',
                made_for_kids INTEGER NOT NULL DEFAULT 0,
                qc_score REAL NOT NULL DEFAULT 0.0,
                video_path TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                submitted_at TEXT NOT NULL,
                reviewed_at TEXT,
                review_notes TEXT,
                FOREIGN KEY (job_id) REFERENCES jobs (id)
            );
        """)

        # 3. Channel Schedules Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedules (
                id TEXT PRIMARY KEY,
                channel_id TEXT NOT NULL UNIQUE,
                enabled INTEGER NOT NULL DEFAULT 0,
                cron_expression TEXT DEFAULT '0 10 * * *',
                interval_hours REAL DEFAULT 24.0,
                last_run TEXT,
                next_run TEXT,
                video_type TEXT DEFAULT 'shorts',
                auto_publish INTEGER DEFAULT 0
            );
        """)

        # 4. Channel-Partitioned Analytics Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT NOT NULL,
                video_id TEXT NOT NULL,
                title TEXT NOT NULL,
                format TEXT NOT NULL DEFAULT 'shorts',
                views INTEGER NOT NULL DEFAULT 0,
                likes INTEGER NOT NULL DEFAULT 0,
                comments INTEGER NOT NULL DEFAULT 0,
                watch_time_hours REAL NOT NULL DEFAULT 0.0,
                avg_view_duration_sec REAL NOT NULL DEFAULT 0.0,
                avg_view_pct REAL NOT NULL DEFAULT 0.0,
                subscribers_gained INTEGER NOT NULL DEFAULT 0,
                recorded_at TEXT NOT NULL
            );
        """)

        # 5. Learning Loop Strategy Insights
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_insights (
                channel_id TEXT NOT NULL,
                insight_key TEXT NOT NULL,
                data_json TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (channel_id, insight_key)
            );
        """)

        # 6. Content History Table (Content Family + Originality + Governance)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content_history (
                content_id TEXT PRIMARY KEY,
                channel_id TEXT NOT NULL,
                content_family_id TEXT NOT NULL,
                content_type TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                parent_content_id TEXT,
                topic TEXT NOT NULL,
                concept TEXT NOT NULL,
                hook TEXT NOT NULL,
                hook_type TEXT DEFAULT 'question',
                script TEXT NOT NULL,
                script_fingerprint TEXT NOT NULL,
                story_structure TEXT DEFAULT '',
                visual_plan TEXT DEFAULT '',
                scene_signatures TEXT DEFAULT '[]',
                animation_actions TEXT DEFAULT '[]',
                assets_used TEXT DEFAULT '[]',
                music_used TEXT DEFAULT '',
                voice_profile TEXT DEFAULT '',
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                production_quality_score REAL DEFAULT 0.0,
                originality_score REAL DEFAULT 0.0,
                technical_qc_result TEXT DEFAULT 'PASS',
                compliance_result TEXT DEFAULT 'PASS',
                channel_validator_result TEXT DEFAULT 'PASS',
                kids_safety_result TEXT DEFAULT 'N/A',
                educational_accuracy_result TEXT DEFAULT 'N/A',
                asset_provenance_result TEXT DEFAULT 'PASS',
                readiness_status TEXT DEFAULT 'PENDING',
                youtube_video_id TEXT,
                youtube_url TEXT,
                publish_timestamp TEXT,
                analytics_snapshots TEXT DEFAULT '{}',
                created_at TEXT NOT NULL
            );
        """)

        # Create indexes for fast lookup
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_channel ON jobs (channel_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs (status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_channel ON analytics (channel_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_review_channel ON review_queue (channel_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_channel ON content_history (channel_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_family ON content_history (content_family_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_parent ON content_history (parent_content_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_type ON content_history (content_type);")

        conn.commit()


# Initialize database automatically on import
init_db()
