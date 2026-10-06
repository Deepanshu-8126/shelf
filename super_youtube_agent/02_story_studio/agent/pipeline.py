from __future__ import annotations

import hashlib
import json
import re
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .adapters import distribution_variants
from .config import PACKAGES_DIR, ROOT
from .db import create_job, get_channel
from .llm import make_content


def _timestamp(seconds: int) -> str:
    hours, seconds = divmod(max(0, seconds), 3600)
    minutes, seconds = divmod(seconds, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},000"


def _captions(scenes: list[dict]) -> str:
    parts = []
    cursor = 0
    for idx, scene in enumerate(scenes, start=1):
        narration = re.sub(r"\s+", " ", str(scene.get("narration", "")).strip())
        if not narration:
            continue
        duration = max(2, int(scene.get("seconds", 5)))
        parts.append(f"{idx}\n{_timestamp(cursor)} --> {_timestamp(cursor + duration)}\n{narration}\n")
        cursor += duration
    return "\n".join(parts)


def _clean_source_urls(raw: list[str] | str | None) -> list[str]:
    if isinstance(raw, str):
        values = raw.splitlines()
    elif isinstance(raw, list):
        values = raw
    else:
        values = []
    sources: list[str] = []
    for value in values:
        url = str(value).strip()
        if not url or len(url) > 1000:
            continue
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
            continue
        if url not in sources:
            sources.append(url)
        if len(sources) >= 20:
            break
    return sources


def create_package(channel_id: str, topic: str, format_name: str = "Shorts", angle: str = "",
                   auto_generated: bool = False, scan: dict | None = None,
                   research_notes: str = "", source_urls: list[str] | str | None = None) -> dict[str, Any]:
    channel = get_channel(channel_id)
    if not channel:
        raise ValueError("Unknown channel slot")
    topic = (topic or "").strip()
    if not topic:
        raise ValueError("Add a specific topic before generating a package")
    research_notes = str(research_notes or "")[:12000]
    source_urls = _clean_source_urls(source_urls)
    content, llm_mode = make_content(
        topic, channel["niche"], format_name,
        audience=f"{channel['audience_country']} audience, {channel['language']}",
        angle=angle, research_notes=research_notes, source_urls=source_urls,
    )
    job_id = uuid.uuid4().hex[:12]
    package_dir = PACKAGES_DIR / job_id
    package_dir.mkdir(parents=True, exist_ok=True)
    claims = [str(claim).strip() for claim in content.get("factual_claims", []) if str(claim).strip()][:100]
    questions = [str(question).strip() for question in content.get("research_questions", []) if str(question).strip()][:100]
    claim_ledger = [
        {"claim": claim, "status": "unverified", "source_urls": [],
         "review_instruction": "Attach a reliable source and human-check wording, date and context."}
        for claim in claims
    ]
    source_log = {
        "status": "editor-supplied; not fetched or checked by CreatorOps",
        "sources": [{"url": url, "status": "not independently verified", "claim_ids": []} for url in source_urls],
        "note": "A source URL is not proof that a claim is supported. Assign each source to claims during human review.",
    }
    manifest = {
        "job_id": job_id,
        "channel_id": channel_id,
        "created_by": "CreatorOps local agent",
        "content_origin": "newly generated script; no third-party video downloaded",
        "rights_status": "uncleared",
        "rights_evidence": "",
        "visual_assets": [],
        "voiceover_status": "not_generated",
        "verification_required": True,
        "source_urls": source_urls,
        "source_status": "editor-supplied-unverified",
        "human_review_required": True,
        "llm_mode": llm_mode,
        "auto_generated_topic": auto_generated,
        "publish_allowed": False,
        "notes": "Add only visuals/audio you own or have a commercial license to use. Source links and LLM text are not independently verified. The system blocks upload until rights and review gates are complete.",
    }
    data = {
        "content": content,
        "llm_mode": llm_mode,
        "format": format_name,
        "angle": angle,
        "auto_generated": auto_generated,
        "scan_id": (scan or {}).get("id", ""),
        "why_now": (scan or {}).get("why_now", ""),
        "market_signals": (scan or {}).get("market_signals", {}),
        "fact_check_status": "needs_review",
        "research_source_count": len(source_urls),
        "research_notes_supplied": bool(research_notes.strip()),
        "script_sha256": hashlib.sha256(content.get("script", "").encode("utf-8")).hexdigest(),
        "renderer": {},
    }
    (package_dir / "content.json").write_text(json.dumps(content, indent=2, ensure_ascii=False), encoding="utf-8")
    (package_dir / "script.md").write_text(
        f"# {content.get('title', topic)}\n\n## Hook\n{content.get('hook','')}\n\n## Script / narration draft\n{content.get('script','')}\n\n## Draft status\nNeeds human source review, fact-check, asset-rights confirmation, final-render review, and approval before upload.\n",
        encoding="utf-8")
    (package_dir / "shotlist.json").write_text(json.dumps(content.get("scenes", []), indent=2, ensure_ascii=False), encoding="utf-8")
    (package_dir / "timeline.json").write_text(json.dumps([
        {"scene": i, "start_seconds": sum(max(2, int(s.get("seconds", 5))) for s in content.get("scenes", [])[:i - 1]),
         "duration_seconds": max(2, int(scene.get("seconds", 5))),
         "narration": scene.get("narration", ""), "visual_brief": scene.get("visual_brief", "")}
        for i, scene in enumerate(content.get("scenes", []), start=1)
    ], indent=2, ensure_ascii=False), encoding="utf-8")
    metadata = {
        "title": content.get("title", topic), "description": content.get("description", ""),
        "tags": content.get("tags", []), "language": channel["language"],
        "target_country": channel["audience_country"], "format": format_name,
        "source_urls": source_urls, "source_urls_status": "editor-supplied-unverified",
    }
    (package_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    (package_dir / "market_signals.json").write_text(json.dumps(data.get("market_signals", {}), indent=2, ensure_ascii=False), encoding="utf-8")
    (package_dir / "captions.srt").write_text(_captions(content.get("scenes", [])), encoding="utf-8")
    (package_dir / "rights_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (package_dir / "source_log.json").write_text(json.dumps(source_log, indent=2, ensure_ascii=False), encoding="utf-8")
    source_lines = "\n".join(f"- {url} — supplied by editor; not fetched or verified" for url in source_urls) or "- No source URLs supplied."
    (package_dir / "source_log.md").write_text(
        "# Source log\n\n" + source_lines + "\n\n"
        "CreatorOps does not fetch these pages. A URL is a research starting point, not evidence that a particular claim is supported.\n",
        encoding="utf-8")
    (package_dir / "claims.json").write_text(json.dumps({
        "status": "unverified draft claims",
        "claims": claim_ledger,
        "research_questions": questions,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    notes_block = research_notes.strip() or "No editor research notes supplied."
    research_brief = (
        f"# Research brief · {content.get('title', topic)}\n\n"
        "## Status\nDraft only. CreatorOps did not browse, fetch, authenticate or verify the supplied material.\n\n"
        "## Editor-supplied notes\n" + notes_block + "\n\n"
        "## Research questions to resolve\n" + ("\n".join(f"- {q}" for q in questions) or "- Confirm scope, dates, geography, primary sources, counterevidence and limitations.") + "\n\n"
        "## Source links\n" + source_lines + "\n"
    )
    (package_dir / "research_brief.md").write_text(research_brief, encoding="utf-8")
    (package_dir / "distribution.json").write_text(
        json.dumps(distribution_variants(content, format_name), indent=2, ensure_ascii=False), encoding="utf-8")
    media_manifest = {
        "status": "preview plan only",
        "visual_assets": [],
        "scene_count": len(content.get("scenes", [])),
        "aspect_ratio": "9:16" if format_name.lower() in {"short", "shorts", "youtube shorts"} else "16:9",
        "render_note": "Generated shape/text storyboard is not a finished documentary or a substitute for licensed, evidence-matched visuals.",
        "voiceover": "not generated during package creation",
    }
    (package_dir / "media_manifest.json").write_text(json.dumps(media_manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (package_dir / "review_checklist.md").write_text(
        "# Human QA checklist\n\n- [ ] Script is original and adds a specific point of view.\n"
        "- [ ] Every factual/current claim is matched to a reliable source and checked in context.\n"
        "- [ ] Source dates, geography, methods, limitations and counterevidence are represented fairly.\n"
        "- [ ] Every image, video, sound, voice, and font has commercial-use rights.\n"
        "- [ ] No copied creator footage, unlicensed music, or misleading earnings claims.\n"
        "- [ ] Captions, spelling, pacing, title, thumbnail, disclosures and audience fit are reviewed.\n"
        "- [ ] Final video has a clear voice track and passes platform review.\n",
        encoding="utf-8")
    package_rel = str(package_dir.relative_to(ROOT))
    job = {
        "id": job_id, "channel_id": channel_id, "title": content.get("title", topic),
        "topic": topic, "niche": channel["niche"], "format": format_name,
        "status": "draft", "stage": "script_ready", "package_path": package_rel,
        "rights_status": "uncleared", "data": data,
    }
    return create_job(job)


def package_contents(job: dict) -> dict[str, Any]:
    package_dir = (ROOT / job["package_path"]).resolve()
    if ROOT not in package_dir.parents:
        raise ValueError("Invalid package path")
    result = {"files": [], "content": job.get("data", {}).get("content", {})}
    names = (
        "script.md", "shotlist.json", "timeline.json", "metadata.json", "captions.srt", "captions.ass",
        "rights_manifest.json", "review_checklist.md", "market_signals.json", "research_brief.md",
        "source_log.md", "source_log.json", "claims.json", "distribution.json", "media_manifest.json",
        "render_manifest.json", "storyboard_preview.mp4", "final_with_voice.mp4", "voiceover.mp3",
        "gaming_clip_manifest.json", "gaming_clip.mp4", "hindi_voiceover.mp3",
    )
    for name in names:
        path = package_dir / name
        if path.exists():
            result["files"].append({"name": name, "url": f"/packages/{job['id']}/{name}"})
    return result
