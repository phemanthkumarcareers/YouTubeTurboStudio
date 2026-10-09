"""
Channel-Specific Learning Loop
Optimizes channel strategy based on historical channel performance without cross-channel bleeding.
Requires sufficient sample size before adapting recommendations and uses normalized metrics.
"""
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from automation.db import get_db_connection
from automation.analytics import analytics_manager
from core.logger import log_info, log_warn


class LearningLoop:
    """Analyzes historical metrics to dynamically adapt topic and formatting strategies."""

    def analyze_channel(
        self,
        channel_id: str,
        min_sample_size: int = 3
    ) -> Dict[str, Any]:
        """
        Runs strategy analysis over channel metrics.
        Requires minimum sample size before altering strategy recommendations.
        """
        metrics = analytics_manager.get_channel_metrics(channel_id, limit=100)

        if len(metrics) < min_sample_size:
            return {
                "channel_id": channel_id,
                "status": "insufficient_sample",
                "sample_count": len(metrics),
                "min_required": min_sample_size,
                "message": f"Requires at least {min_sample_size} published videos before adjusting strategy."
            }

        # 1. Performance by Format (Shorts vs Normal)
        format_views = {}
        format_counts = {}
        for m in metrics:
            fmt = m.get("format", "shorts")
            format_views[fmt] = format_views.get(fmt, 0) + m.get("views", 0)
            format_counts[fmt] = format_counts.get(fmt, 0) + 1

        avg_by_format = {
            fmt: round(format_views[fmt] / float(format_counts[fmt]), 1)
            for fmt in format_views
        }

        # Best performing format
        best_format = max(avg_by_format, key=avg_by_format.get) if avg_by_format else "shorts"

        # 2. Topic Keyword / Pillar Analysis
        # Simple token frequency weighted by view counts
        word_scores = {}
        for m in metrics:
            title = m.get("title", "")
            views = max(1, m.get("views", 0))
            words = [w.lower().strip(":,!?") for w in title.split() if len(w) > 3]
            for w in words:
                word_scores[w] = word_scores.get(w, 0) + views

        top_pillars = sorted(word_scores.keys(), key=lambda k: word_scores[k], reverse=True)[:5]

        # 3. Retention-based Pacing Insight
        avg_retention = sum(m.get("avg_view_pct", 0) for m in metrics) / float(len(metrics))

        strategy = {
            "channel_id": channel_id,
            "status": "optimized",
            "sample_count": len(metrics),
            "best_format": best_format,
            "avg_views_by_format": avg_by_format,
            "overall_avg_retention": round(avg_retention, 1),
            "top_topic_pillars": top_pillars,
            "pacing_recommendation": "Maintain unhurried scenes (retention healthy)" if avg_retention >= 70.0 else "Consider faster scene transitions"
        }

        # Store strategy insight in DB
        now = datetime.now(timezone.utc).isoformat()
        with get_db_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO learning_insights (
                    channel_id, insight_key, data_json, updated_at
                ) VALUES (?, 'strategy_recommendation', ?, ?)
            """, (channel_id, json.dumps(strategy), now))
            conn.commit()

        log_info(f"[LEARNING LOOP] Updated strategy for '{channel_id}': best_format='{best_format}', pillars={top_pillars[:3]}")
        return strategy

    def get_strategy_recommendation(self, channel_id: str) -> Dict[str, Any]:
        """Fetch latest learned strategy recommendation for a channel."""
        with get_db_connection() as conn:
            row = conn.execute("""
                SELECT data_json FROM learning_insights
                WHERE channel_id = ? AND insight_key = 'strategy_recommendation'
            """, (channel_id,)).fetchone()
            if row:
                try:
                    return json.loads(row["data_json"])
                except Exception:
                    pass

        # If not cached yet, analyze fresh
        return self.analyze_channel(channel_id, min_sample_size=3)


learning_loop = LearningLoop()
