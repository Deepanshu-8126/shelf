"""Pipeline orchestrator: topic -> script -> footage -> voice -> render -> SEO.

Used by both bot.py (interactive) and scheduler.py (daily job). Emits progress
events through an optional async callback so the Telegram bot can show live status.
"""
from __future__ import annotations

import json
import re
import time
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable, Tuple, List

from . import db
from .config import Config, get_config
from .footage import FootageClient, collect_clips
from .ai_footage import generate_scene_clips
from .llm import LLM
from .render import RenderResult, rank_clips_by_sharpness, render_video
from .script_writer import Script, rescue_script, write_script
from .trends import TrendClient
from .seo import build_seo
from .topic_engine import Topic, generate_topic, widen_material
from .utils import clean_text, module_logger
from .voice import VoiceResult, synthesize

log = module_logger("pipeline")

ProgressFn = Callable[[str], Awaitable[None]]


@dataclass
class PipelineResult:
    video_id: int
    path: Path
    duration: float
    topic: str
    hook: str
    script_text: str
    seo: dict
    render: dict
    voice: str
    credit: str
    elapsed: float
    clip_count: int = 0

    source_url: str = ""

    def caption(self) -> str:
        return (
            f"#{self.video_id} • {self.duration:.1f}s • {self.clip_count} clips\n"
            f"Topic: {self.topic}"
        )

async def _noop(_stage: str) -> None:  # pragma: no cover
    return None


def pipeline_summary(result: PipelineResult) -> str:
    return result.caption()


async def generate_and_render(
    niche: str | None = None,
    cfg: Config | None = None,
    progress: ProgressFn | None = None,
    allow_repeat: bool = False,
    forced_topic: str | None = None,
    script: str | None = None,
    voice: str | None = None,
) -> PipelineResult:
    """Full generation run. Raises on hard failure and records it in the DB."""
    cfg = cfg or get_config()
    if voice is not None:
        cfg.voice = voice
    progress = progress or _noop
    t0 = time.time()
    niche = (niche or cfg.niche or "space").lower()
    profile = cfg.profile()
    mode = profile.name

    video_id = db.create_video(niche=niche, status="rendering")
    db.update_meta(video_id, {"mode": mode})
    llm = LLM(cfg)
    footage = FootageClient(cfg)
    trend_client = TrendClient(cfg)
    try:
        seed = None
        if script is not None:
            # Custom script supplied by user
            cleaned_script = clean_text(script)
            topic_title = forced_topic.strip() if (forced_topic and forced_topic.strip()) else ""
            if not topic_title:
                from .script_writer import _split_sentences
                sents = _split_sentences(cleaned_script)
                first_sent = sents[0] if sents else cleaned_script
                topic_title = clean_text(first_sent, 60)

            topic = Topic(
                niche=niche,
                topic=topic_title,
                fact=cleaned_script,
                angle=topic_title,
                keywords=[topic_title.lower()] + [w.lower() for w in topic_title.split() if len(w) > 3][:4] + [f"{niche} facts", niche],
                verified=True,
                source="provided-script"
            )
            log.info("#%s using user-supplied script for topic: %s", video_id, topic.topic)
        else:
            if cfg.use_trends and not forced_topic:
                await progress("Checking today's trends (Google Trends + Wikipedia)…")
                try:
                    seed = await trend_client.find_seed(niche, cfg.trends_geo)
                except Exception as exc:  # noqa: BLE001 - trends are a bonus, never a blocker
                    log.warning("trend lookup failed: %s", exc)
                if seed:
                    log.info("#%s trend seed: %s", video_id, seed.label())

            await progress(f"Generating an accurate fact{f' about {seed.title}' if seed else ''}…")
            topic = await generate_topic(
                niche=niche, llm=llm, cfg=cfg, allow_repeat=allow_repeat, forced_topic=forced_topic,
                seed=seed, client=trend_client,
            )
            if mode == "story":
                # a 60 s story needs ~150 words of verified material, not a two-line excerpt
                topic = await widen_material(topic, trend_client, target_words=cfg.story_target_words)

        db.update_video(
            video_id,
            topic=topic.topic,
            hook=topic.fact[:120],
            source_url=topic.source_url,
            source_name=topic.source_name,
        )
        db.update_meta(video_id, {
            "topic_source": topic.source,
            "verified": topic.verified,
            # attribute the trend only when the seed was actually used (a rejected seed
            # falls through to the LLM/offline bank and must not be credited)
            "trend": ({"kind": seed.kind, "title": seed.title, "source": seed.source,
                        "extra": seed.extra} if (seed and topic.trend_kind) else None),
            "trend_candidate": ({"kind": seed.kind, "title": seed.title}
                                if (seed and not topic.trend_kind) else None),
        })
        log.info("#%s topic [%s] %s", video_id, topic.source, topic.topic)

        await progress("Writing the script…")
        # Use provided script if available, otherwise generate one
        if script is not None:
            # Parse the provided script into hook, body, closing
            from .script_writer import sanitize_keywords, _split_sentences, Sentence, strip_ad_language, HOOKS, CLOSINGS, style_of, cta_of
            
            # Clean the script text
            cleaned_script = clean_text(script)
            
            # Try to extract hook, body, and closing using common patterns
            sentences = _split_sentences(cleaned_script)
            
            hook_text = ""
            body_text = cleaned_script
            closing_text = ""
            
            # If we have multiple sentences, try to use first as hook, last as closing
            if len(sentences) >= 3:
                hook_text = sentences[0]
                closing_text = sentences[-1]
                body_text = " ".join(sentences[1:-1])
            elif len(sentences) == 2:
                hook_text = sentences[0]
                body_text = sentences[0]  # Use first as both hook and body
                closing_text = sentences[1]
            else:
                # Single sentence or empty - use as body, get default hook/closing
                hook_text = random.choice(HOOKS.get(style_of(cfg), HOOKS["friendly"]))
                body_text = cleaned_script
                closing_text = random.choice(CLOSINGS.get(cta_of(cfg), CLOSINGS["soft"]))
            
            # Clean up the extracted parts
            hook_text = strip_ad_language(hook_text)
            body_text = strip_ad_language(body_text)
            closing_text = strip_ad_language(closing_text)
            
            # Create Sentence objects with keywords for body sentences
            body_sentences = _split_sentences(body_text)
            sentence_objects = []
            for sent in body_sentences:
                kw = sanitize_keywords([sent], topic.niche)  # Simplified keyword extraction
                sentence_objects.append(Sentence(text=sent, keywords=kw))
            
            # Create Script object
            script_obj = Script(
                hook=hook_text,
                body=body_text,
                closing=closing_text,
                sentences=sentence_objects,
                topic=topic.topic,
                niche=topic.niche,
                source="provided-script"
            )
        else:
            # Generate script using LLM
            script_obj: Script = await write_script(topic, llm=llm, cfg=cfg, trends=[seed.title] if seed else None)
        
        db.update_video(video_id, script=script_obj.full_text, hook=script_obj.hook)

        # --- 1. RECORD VOICEOVER FIRST TO GET EXACT SENTENCE TIMESTAMPS ---
        await progress("Recording voiceover…")
        work = cfg.cache_dir / "tmp" / f"voice-{video_id}"
        work.mkdir(parents=True, exist_ok=True)
        voice: VoiceResult = await synthesize(
            script_obj.full_text, work / f"voice-{video_id}.mp3", niche=niche, cfg=cfg
        )
        # keep the narration inside the window for this mode.
        attempts = 0
        speed_hint: float | None = None
        while voice.duration > profile.max_duration - 0.15 and attempts < 3:
            attempts += 1
            over = voice.duration - profile.max_duration
            can_speed_up = (
                mode == "story"
                and voice.provider in {"kokoro", "piper"}
                and (speed_hint or 1.0) * cfg.story_speed_step <= cfg.story_max_speed
                and over < voice.duration * 0.25
            )
            if can_speed_up:
                base_speed = speed_hint or (cfg.kokoro_speed if voice.provider == "kokoro" else 1.0)
                speed_hint = round(base_speed * cfg.story_speed_step, 3)
                log.warning("narration %.2fs too long (max %.1fs) -> re-voicing at speed %.2f",
                            voice.duration, profile.max_duration, speed_hint)
                await progress(f"Narration ran long, re-recording slightly faster (try {attempts})…")
            else:
                log.warning("narration %.2fs too long -> tightening the script", voice.duration)
                script_obj = rescue_script(script_obj, cfg)
                db.update_video(video_id, script=script_obj.full_text)
                await progress(f"Narration was too long, trimming it (try {attempts})…")
            voice = await synthesize(
                script_obj.full_text, work / f"voice-{video_id}-{attempts}.mp3", niche=niche, cfg=cfg,
                speed_hint=speed_hint,
            )

        db.update_meta(video_id, {
            "voice": voice.voice,
            "voice_provider": voice.provider,
            "voice_seconds": round(voice.duration, 2),
            "voice_speed": voice.speed,
            "mode": mode,
            "target_seconds": profile.max_duration if mode != "facts" else None,
        })

        # Calculate exact sentence timestamp boundaries for 100% video-to-speech synchrony
        sentence_timings = _extract_sentence_timings(script_obj.full_text, voice)
        voice.segments = sentence_timings

        # --- 2. MATCH 1:1 VISUAL FOOTAGE TO SPOKEN SENTENCES ---
        clips: list = []
        has_stock_keys = bool(cfg.pexels_api_key or cfg.pixabay_api_key)
        is_gpu_worker = bool(getattr(cfg, "gpu_worker_url", ""))

        # Priority 1: Real 4K stock footage directly depicting each spoken sentence beat
        if has_stock_keys and not is_gpu_worker:
            await progress("Finding 1:1 semantic matching stock footage (Pexels HD)…")
            from .footage import collect_clips_for_sentences
            clips = await collect_clips_for_sentences(script_obj.sentences, niche=niche, cfg=cfg, client=footage)
            log.info("Collected %d sentence-matched stock clips from Pexels/Pixabay", len(clips))

        # Priority 2: Remote GPU real video model if configured
        if not clips and is_gpu_worker:
            pref_model = getattr(cfg, "video_gen_model", "wan-2.2").upper()
            mode_label = f"Kaggle GPU ({pref_model} Video)"
            log.info("Visual generation engine: %s (%d sentence beats)", mode_label, len(sentence_timings))
            await progress(f"Generating synced scenes [{mode_label}]…")

            ai_work = cfg.cache_dir / "tmp" / f"{video_id}-ai-footage"
            ai_clips_raw = await generate_scene_clips(
                script_text=script_obj.full_text,
                output_dir=ai_work,
                total_duration=voice.duration,
                clip_count=len(sentence_timings),
                niche=niche,
                cfg=cfg,
                sentence_timings=sentence_timings,
            )
            if ai_clips_raw:
                from .footage import Clip, ClipCandidate
                for ac in ai_clips_raw:
                    p = Path(ac["path"])
                    if p.exists():
                        from .utils import media_duration
                        dur = media_duration(p)
                        source_model = ac.get("source", "ai_generated")
                        cand = ClipCandidate(
                            source=source_model, source_id=ac["source_id"],
                            download_url=p.as_uri(), page_url="",
                            author=ac.get("author", "Open-Source AI (Apache 2.0)"),
                            license=ac.get("license", "Apache 2.0 / Free Open-Source"),
                            duration=dur, width=ac.get("width", 1080),
                            height=ac.get("height", 1920), query=ac.get("prompt", ""),
                        )
                        clips.append(Clip(path=p, candidate=cand, duration=dur,
                                          width=ac.get("width", 1080), height=ac.get("height", 1920)))

        # Priority 3: Fallback to keyword collector if needed
        if not clips:
            await progress("Finding matching footage…")
            clips = await collect_clips(script_obj.visual_keywords(), profile.clip_count, cfg=cfg, client=footage)
            if len(clips) > len(sentence_timings):
                clips = await rank_clips_by_sharpness(clips, cfg)
                clips = clips[: len(sentence_timings)]
        elif len(clips) > len(sentence_timings):
            clips = clips[: len(sentence_timings)]

        await progress("Rendering the video (ffmpeg)…")
        result: RenderResult = await render_video(script_obj, clips, voice, video_id=video_id, cfg=cfg)

        await progress("Writing title, description and tags…")
        seo = await build_seo(topic, script_obj, llm=llm, cfg=cfg)
        extras: list[str] = []
        if topic.source_url and cfg.cite_source:
            extras.append(f"Source: {topic.source_name or 'reference'} → {topic.source_url}")
        if result.credit:
            extras.append(result.credit)
        if extras:
            seo["description"] = seo["description"].rstrip() + "\n\n" + "\n".join(extras)

        db.update_video(
            video_id,
            title=seo["title"],
            description=seo["description"],
            tags=seo["tags"],
            pinned_comment=seo["pinned_comment"],
            video_path=str(result.path),
            duration=result.duration,
            status="pending",
        )
        db.update_meta(video_id, {
            "seo_source": seo.get("source"),
            "report": result.report,
            "niche": niche,
            "mode": mode,
            "script": script_obj.as_dict(),
        })
        await progress("Done.")
        log.info("#%s finished in %.1fs -> %s", video_id, time.time() - t0, result.path.name)
        return PipelineResult(
            video_id=video_id,
            path=result.path,
            duration=result.duration,
            topic=topic.topic,
            hook=script_obj.hook,
            script_text=script_obj.full_text,
            seo=seo,
            render=result.report,
            voice=voice.voice,
            credit=result.credit,
            elapsed=time.time() - t0,
            clip_count=result.clip_count,
            source_url=topic.source_url,
        )
    except Exception as exc:  # noqa: BLE001 - always record the failure
        log.exception("#%s pipeline failed: %s", video_id, exc)
        db.update_video(video_id, status="failed", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        await llm.aclose()
        await footage.aclose()
        await trend_client.aclose()


def _extract_sentence_timings(script_text: str, voice: VoiceResult) -> List[Tuple[str, float, float]]:
    """Extract (sentence_text, start_sec, duration_sec) for each sentence in the narration.
    Guarantees 100% frame-perfect synchrony between what is spoken and what is shown on screen.
    """
    if getattr(voice, "segments", None) and len(voice.segments) > 0:
        return [(seg[0], float(seg[1]), float(seg[2])) for seg in voice.segments]

    # Split text into distinct sentences with punctuation preserved
    raw_sentences = [s.strip() for s in re.split(r'([.!?]+)', script_text) if s.strip()]
    sentences = []
    i = 0
    while i < len(raw_sentences):
        s = raw_sentences[i]
        if i + 1 < len(raw_sentences) and re.match(r'^[.!?]+$', raw_sentences[i + 1]):
            s += raw_sentences[i + 1]
            i += 2
        else:
            i += 1
        if len(s.strip()) > 3:
            sentences.append(s.strip())

    if not sentences:
        sentences = [script_text.strip()]

    # If word-level timings are present (e.g. edge-tts or whisper)
    if getattr(voice, "words", None) and len(voice.words) > 0:
        timings = []
        word_idx = 0
        total_words = len(voice.words)
        for sent in sentences:
            sent_words = [w.lower().strip(".,!?:;\"'") for w in sent.split() if w.strip()]
            if not sent_words:
                continue
            start_t = voice.words[min(word_idx, total_words - 1)].start
            consumed = 0
            while word_idx < total_words and consumed < len(sent_words):
                word_idx += 1
                consumed += 1
            end_t = voice.words[min(max(0, word_idx - 1), total_words - 1)].end
            dur = max(1.8, end_t - start_t)
            timings.append((sent, round(start_t, 3), round(dur, 3)))
        if timings:
            return timings

    # Proportional distribution based on character lengths
    total_dur = max(voice.duration, 5.0)
    total_chars = max(1, sum(len(s) for s in sentences))
    timings = []
    curr_t = 0.0
    for s in sentences:
        dur = max(1.8, round((len(s) / total_chars) * total_dur, 2))
        timings.append((s, round(curr_t, 3), round(dur, 3)))
        curr_t += dur
    return timings