from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import ROOT, env
from .db import get_channel


def publish_blockers(job: dict[str, Any], automated: bool = False) -> list[str]:
    blockers: list[str] = []
    fact_status = job.get("data", {}).get("fact_check_status", "needs_review")
    if fact_status != "verified_by_human":
        blockers.append("Human fact-check is incomplete. Add a review note/source links before upload.")
    if job.get("rights_status") not in {"owned", "licensed"}:
        blockers.append("Rights are not cleared. Mark assets as owned or commercially licensed and add a note.")
    if not job.get("rights_evidence", "").strip():
        blockers.append("Rights evidence/note is missing.")
    game_clip = job.get("data", {}).get("gaming_clip")
    if job.get("format") == "Game Clip" and not isinstance(game_clip, dict):
        blockers.append("Game Clip metadata is missing. Build GTA VI clips only through the rights-gated Gaming Clips workflow.")
    if isinstance(game_clip, dict):
        if job.get("rights_status") != "licensed":
            blockers.append("GTA VI clips require licensed status; owning the recording alone does not clear Rockstar/Take-Two game IP for monetized use.")
        if len(str(game_clip.get("commercial_license_reference", "")).strip()) < 8:
            blockers.append("Case-specific written commercial permission from Rockstar/Take-Two is not documented. Creator permission or source credit alone is not enough.")
        if game_clip.get("source_kind") == "licensed_creator_clip" and len(str(game_clip.get("creator_permission_reference", "")).strip()) < 8:
            blockers.append("The creator's written permission for the source footage is missing.")
        if not game_clip.get("original_commentary_in_render_confirmed"):
            blockers.append("Human review has not confirmed meaningful original Hindi/Hinglish commentary or analysis in the final clip.")
        if not game_clip.get("game_audio_rights_confirmed"):
            blockers.append("Human review has not confirmed commercial rights for game audio, music and all other audible elements.")
        if not game_clip.get("no_leaked_or_prohibited_content_confirmed"):
            blockers.append("Human review has not confirmed the clip contains no leaked footage, prohibited spoilers or restricted in-game content.")
    if not job.get("human_approved"):
        blockers.append("Human content and fact-check approval is required.")
    video_path = job.get("video_path", "")
    if not video_path or not Path(video_path).is_file():
        blockers.append("A final rendered video file is missing.")
    if not job.get("has_audio"):
        blockers.append("The current render has no voice/audio track; silent storyboard drafts cannot be uploaded by this workflow.")
    renderer = job.get("data", {}).get("renderer", {})
    if not renderer.get("visual_reviewed"):
        blockers.append("Final video visual/audio QA has not been attested. Review the rendered file before upload.")
    channel = get_channel(job.get("channel_id", ""))
    if not channel:
        blockers.append("Channel slot is missing.")
    else:
        token = ROOT / "secrets" / "tokens" / f"{channel['id']}.json"
        if not token.exists():
            blockers.append(f"YouTube OAuth is not connected for {channel['name']}.")
    if automated and env("AUTO_PUBLISH_ENABLED", "false").lower() != "true":
        blockers.append("AUTO_PUBLISH_ENABLED is false. Enable only after testing private uploads and reviewing platform rules.")
    return blockers


def safe_privacy(requested: str | None = None) -> str:
    # Public autopublishing requires two explicit opt-ins; private is the default.
    requested = (requested or env("DEFAULT_PRIVACY", "private")).lower()
    if requested == "public":
        if env("AUTO_PUBLISH_ENABLED", "false").lower() != "true" or env("ALLOW_PUBLIC_UPLOAD", "false").lower() != "true":
            return "private"
        return "public"
    if requested == "unlisted":
        return "unlisted"
    return "private"
