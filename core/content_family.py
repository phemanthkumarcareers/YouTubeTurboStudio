"""
Content Family & Content Relationship Architecture
Maintains the shared Content Family hierarchy above rendering engines:
- Long Video (Parent or Standalone)
- Standalone Shorts (Zero parent relationship, zero parent URL)
- Linked Shorts (Derived from an eligible active-channel Long video)
Strictly enforces cross-channel isolation and parent validation server-side.
"""
import uuid
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from automation.db import get_db_connection
from core.logger import log_info, log_warn, log_error


def generate_fingerprint(text: str) -> str:
    """Generate normalized text fingerprint for similarity matching."""
    if not text:
        return ""
    # Normalize lower case and alphanumeric tokens
    tokens = [w.strip() for w in text.lower().split() if w.strip()]
    normalized = " ".join(tokens)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class ContentFamilyError(Exception):
    """Raised when content family relationship rules are violated."""
    pass


class CrossChannelLinkingError(ContentFamilyError):
    """Raised when a Short attempts to link to a Long video from a different channel."""
    pass


class ContentFamilyManager:
    """Manages content history, parent-child lineages, and eligibility rules."""

    def register_content(
        self,
        channel_id: str,
        topic: str,
        content_type: str = "LONG",            # 'LONG' | 'SHORT'
        relationship_type: str = "STANDALONE",  # 'STANDALONE' | 'PARENT' | 'DERIVED'
        parent_content_id: Optional[str] = None,
        concept: str = "",
        hook: str = "",
        hook_type: str = "question",
        script: str = "",
        story_structure: str = "",
        visual_plan: str = "",
        scene_signatures: Optional[List[str]] = None,
        animation_actions: Optional[List[str]] = None,
        assets_used: Optional[List[str]] = None,
        music_used: str = "",
        voice_profile: str = "",
        title: str = "",
        description: str = "",
        production_quality_score: float = 0.0,
        originality_score: float = 0.0,
        technical_qc_result: str = "PASS",
        compliance_result: str = "PASS",
        channel_validator_result: str = "PASS",
        kids_safety_result: str = "N/A",
        educational_accuracy_result: str = "N/A",
        asset_provenance_result: str = "PASS",
        readiness_status: str = "PENDING",
        youtube_video_id: Optional[str] = None,
        youtube_url: Optional[str] = None,
        publish_timestamp: Optional[str] = None,
        analytics_snapshots: Optional[Dict[str, Any]] = None,
        content_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates and persists a ContentRecord in content_history.
        Enforces channel isolation and family inheritance rules.
        """
        content_type = content_type.upper().strip()
        relationship_type = relationship_type.upper().strip()
        c_id = content_id or f"cnt_{uuid.uuid4().hex[:12]}"

        # Validate parent relationship
        parent_rec = None
        if relationship_type == "DERIVED":
            if not parent_content_id:
                raise ContentFamilyError("Derived Shorts require a valid parent_content_id.")
            valid, err, parent_rec = self.validate_parent(child_channel_id=channel_id, parent_content_id=parent_content_id)
            if not valid:
                raise ContentFamilyError(f"Parent validation failed: {err}")
            content_family_id = parent_rec["content_family_id"]
        elif relationship_type == "PARENT" or content_type == "LONG":
            # For parents, content_family_id originates with themselves
            content_family_id = c_id
            relationship_type = "PARENT"
        else:
            # Standalone shorts
            content_family_id = c_id
            relationship_type = "STANDALONE"
            parent_content_id = None

        now = datetime.now(timezone.utc).isoformat()
        fingerprint = generate_fingerprint(script or topic)

        record = {
            "content_id": c_id,
            "channel_id": channel_id,
            "content_family_id": content_family_id,
            "content_type": content_type,
            "relationship_type": relationship_type,
            "parent_content_id": parent_content_id,
            "topic": topic,
            "concept": concept or topic,
            "hook": hook,
            "hook_type": hook_type,
            "script": script,
            "script_fingerprint": fingerprint,
            "story_structure": story_structure,
            "visual_plan": visual_plan,
            "scene_signatures": json.dumps(scene_signatures or []),
            "animation_actions": json.dumps(animation_actions or []),
            "assets_used": json.dumps(assets_used or []),
            "music_used": music_used,
            "voice_profile": voice_profile,
            "title": title or topic,
            "description": description,
            "production_quality_score": float(production_quality_score),
            "originality_score": float(originality_score),
            "technical_qc_result": technical_qc_result,
            "compliance_result": compliance_result,
            "channel_validator_result": channel_validator_result,
            "kids_safety_result": kids_safety_result,
            "educational_accuracy_result": educational_accuracy_result,
            "asset_provenance_result": asset_provenance_result,
            "readiness_status": readiness_status,
            "youtube_video_id": youtube_video_id,
            "youtube_url": youtube_url,
            "publish_timestamp": publish_timestamp,
            "analytics_snapshots": json.dumps(analytics_snapshots or {}),
            "created_at": now
        }

        with get_db_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO content_history (
                    content_id, channel_id, content_family_id, content_type, relationship_type,
                    parent_content_id, topic, concept, hook, hook_type, script, script_fingerprint,
                    story_structure, visual_plan, scene_signatures, animation_actions, assets_used,
                    music_used, voice_profile, title, description, production_quality_score,
                    originality_score, technical_qc_result, compliance_result, channel_validator_result,
                    kids_safety_result, educational_accuracy_result, asset_provenance_result,
                    readiness_status, youtube_video_id, youtube_url, publish_timestamp,
                    analytics_snapshots, created_at
                ) VALUES (
                    :content_id, :channel_id, :content_family_id, :content_type, :relationship_type,
                    :parent_content_id, :topic, :concept, :hook, :hook_type, :script, :script_fingerprint,
                    :story_structure, :visual_plan, :scene_signatures, :animation_actions, :assets_used,
                    :music_used, :voice_profile, :title, :description, :production_quality_score,
                    :originality_score, :technical_qc_result, :compliance_result, :channel_validator_result,
                    :kids_safety_result, :educational_accuracy_result, :asset_provenance_result,
                    :readiness_status, :youtube_video_id, :youtube_url, :publish_timestamp,
                    :analytics_snapshots, :created_at
                )
            """, record)
            conn.commit()

        log_info(f"[CONTENT FAMILY] Registered '{c_id}' ({content_type}/{relationship_type}) for channel '{channel_id}'.")
        return record

    def get_content(self, content_id: str) -> Optional[Dict[str, Any]]:
        """Fetch content record by ID."""
        with get_db_connection() as conn:
            row = conn.execute("SELECT * FROM content_history WHERE content_id = ?", (content_id,)).fetchone()
            if not row:
                return None
            return dict(row)

    def list_eligible_parents(self, channel_id: str) -> List[Dict[str, Any]]:
        """
        List all eligible Long videos for linked Shorts within the given channel.
        Strictly filtered to the active channel only.
        """
        if not channel_id:
            return []
        with get_db_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM content_history
                WHERE channel_id = ? AND content_type = 'LONG'
                ORDER BY created_at DESC
            """, (channel_id,)).fetchall()
            return [dict(r) for r in rows]

    def validate_parent(self, child_channel_id: str, parent_content_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Server-side validation for parent linkage.
        Rejects cross-channel linking, non-existent parent, or non-Long parent.
        """
        parent = self.get_content(parent_content_id)
        if not parent:
            return False, f"Parent video '{parent_content_id}' does not exist.", None

        if parent["channel_id"] != child_channel_id:
            msg = (
                f"Cross-channel linking prohibited: child channel '{child_channel_id}' "
                f"cannot link to parent from channel '{parent['channel_id']}'."
            )
            log_error(f"[CONTENT GUARD] {msg}")
            raise CrossChannelLinkingError(msg)

        if parent["content_type"] != "LONG":
            return False, f"Parent video '{parent_content_id}' must be a Long video, got '{parent['content_type']}'.", parent

        return True, "Parent relationship valid.", parent

    def resolve_parent_url(self, parent_content_id: Optional[str]) -> Optional[str]:
        """
        Resolves real YouTube URL for parent video.
        Returns None if parent does not exist or has not yet been published.
        NEVER fabricates a fake URL.
        """
        if not parent_content_id:
            return None
        parent = self.get_content(parent_content_id)
        if not parent:
            return None
        url = (parent.get("youtube_url") or "").strip()
        if url and (url.startswith("http://") or url.startswith("https://")):
            return url
        return None

    def build_short_description(
        self,
        base_description: str,
        relationship_type: str,
        parent_content_id: Optional[str] = None,
        cta_text: str = "Watch the full video"
    ) -> str:
        """
        Constructs the final Short description:
        - Standalone Short: NEVER appends parent URL or CTA.
        - Linked Short with published parent: injects real parent URL and contextual CTA.
        - Linked Short with unpublished parent: leaves URL out (never fabricates fake URL).
        """
        relationship_type = relationship_type.upper().strip()
        desc = (base_description or "").strip()

        if relationship_type != "DERIVED" or not parent_content_id:
            # Standalone Shorts must not accidentally inherit a parent URL or content-family CTA
            return desc

        parent_url = self.resolve_parent_url(parent_content_id)
        if parent_url:
            cta_block = f"\n\n📺 {cta_text}: {parent_url}"
            return desc + cta_block

        # If parent URL does not yet exist: never fabricate one
        return desc

    def update_youtube_publish(
        self,
        content_id: str,
        youtube_video_id: str,
        youtube_url: str
    ) -> bool:
        """Record real YouTube publication details."""
        now = datetime.now(timezone.utc).isoformat()
        with get_db_connection() as conn:
            cur = conn.execute("""
                UPDATE content_history
                SET youtube_video_id = ?, youtube_url = ?, publish_timestamp = ?
                WHERE content_id = ?
            """, (youtube_video_id, youtube_url, now, content_id))
            conn.commit()
            return cur.rowcount > 0

    def list_channel_history(self, channel_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch past records for originality comparison."""
        with get_db_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM content_history
                WHERE channel_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (channel_id, limit)).fetchall()
            return [dict(r) for r in rows]


# Global singleton
content_family_mgr = ContentFamilyManager()
