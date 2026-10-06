"""Script drafter: viral shorts structure, pattern interrupts, and Hinglish/English support."""
from __future__ import annotations

import re
from typing import Any

from trendengine.llm.local_writer import LocalWriter


class ScriptDrafter:
    def __init__(self, writer: LocalWriter | None = None) -> None:
        self.writer = writer or LocalWriter()

    async def draft_script(
        self,
        topic: dict[str, Any],
        brand_voice: str = "casual, curious, slightly humorous",
        audience: str = "18-35, Indian + global",
        language: str = "Hinglish",
        hook_style: str = "pattern_interrupt",
        cta_style: str = "loop_curiosity",
    ) -> dict[str, Any]:
        title = topic.get("title", "")
        summary = topic.get("summary", "")
        source = topic.get("source", "trends")
        niche = topic.get("niche", "science")

        lang_instruction = (
            "Write in natural, energetic Hinglish (Hindi + English blend commonly spoken on Indian YouTube/Instagram Shorts). "
            "Example: 'Agar aapko lagta hai ki time hamesha same speed se chalta hai, toh yeh suniye...' "
            if language.lower() == "hinglish"
            else "Write in conversational, punchy English."
        )

        system = (
            "You are a top 1% viral YouTube Shorts scriptwriter. "
            "You turn real trends into addictive, high-retention vertical videos. "
            "Never use clichés like 'Did you know?' or 'In today's fast-paced world'. "
            "Always start with a shocking pattern interrupt."
        )

        prompt = f"""Topic: {title}
Context/Trend: {summary}
Source: {source}
Niche: {niche}
Audience: {audience}
Style: {brand_voice}
Hook Style: {hook_style}
CTA Style: {cta_style}
Language: {lang_instruction}

Write a spoken 120-150 word vertical video story script:
1. 3-second HOOK: Strong pattern interrupt, bold claim, or counter-intuitive paradox.
2. 3 ESCALATING FACTS/BEATS: Each beat more surprising and dramatic than the last.
3. CTA: Smooth, loop-able outro that connects naturally back to the beginning.

Also generate:
- titles: 5 high-CTR title variants
- tags: 10 targeted SEO tags
- description: 2-3 line captivating description
- visual_keywords: 6-8 SPECIFIC B-roll search queries (e.g. 'deep ocean bioluminescence', 'supernova shockwave', NOT generic 'ocean' or 'space')
- sentences: array of 6-8 scene beats with: {{"text": "spoken narration", "keywords": ["query1", "query2"]}}

Return ONLY a JSON object:
{{
  "hook": "...",
  "facts": ["beat 1", "beat 2", "beat 3"],
  "cta": "...",
  "titles": ["title 1", "title 2", "title 3", "title 4", "title 5"],
  "tags": ["tag1", "tag2", ...],
  "description": "...",
  "visual_keywords": ["keyword 1", "keyword 2", ...],
  "sentences": [
    {{"text": "...", "keywords": ["..."]}}
  ]
}}
"""
        data = await self.writer.generate_json(prompt, system)

        # Assemble full text
        hook = data.get("hook", "").strip()
        facts_text = " ".join(data.get("facts", []))
        cta = data.get("cta", "").strip()
        full_text = f"{hook} {facts_text} {cta}".strip()

        # Clean sentences if not provided
        sentences = data.get("sentences", [])
        if not sentences:
            sentences = [{"text": full_text, "keywords": data.get("visual_keywords", [])[:3]}]

        return {
            "hook": hook,
            "body": facts_text,
            "closing": cta,
            "full_text": full_text,
            "word_count": len(full_text.split()),
            "titles": data.get("titles", [title]),
            "best_title": (data.get("titles") or [title])[0],
            "tags": data.get("tags", [niche, "shorts", "viral"]),
            "description": data.get("description", title),
            "visual_keywords": data.get("visual_keywords", []),
            "sentences": sentences,
            "hook_style": hook_style,
            "cta_style": cta_style,
            "niche": niche,
        }
