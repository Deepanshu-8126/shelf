from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .config import env


def _fallback(topic: str, niche: str, format_name: str, angle: str = "",
              research_notes: str = "", source_urls: list[str] | None = None) -> dict[str, Any]:
    short = format_name.lower() in {"short", "shorts", "youtube shorts"}
    documentary = format_name.lower() in {"documentary", "long-form documentary", "documentary long-form"}
    title = topic.strip()[:95] or f"A useful idea in {niche}"
    hook = (angle.strip()[:180] if angle.strip() else f"Most people approach {title.lower()} the hard way. Here's a clearer way to think about it.")
    if documentary:
        script = (
            f"RESEARCH-FIRST DRAFT: {title}.\n\n"
            "Open with the central question and explain why it matters. Establish the background only after checking dates and primary sources. "
            "Build the story around evidence supplied and independently verified by the editor; include a counterpoint, a limitation, and what remains unknown. "
            "Close by separating what the evidence supports from what it does not.\n\n"
            "This local template has not analyzed or verified the supplied source material. Replace this outline with researched narration before production."
        )
        scenes = [
            {"narration": f"The question is: {title}. What can reliable evidence actually tell us?", "visual_brief": "Original question card; no claims or third-party footage.", "seconds": 18},
            {"narration": "First, establish the background. Confirm dates, definitions and geography from primary sources.", "visual_brief": "Original timeline with empty citation placeholders for verified dates.", "seconds": 28},
            {"narration": "Next, examine the strongest evidence and explain how it was collected.", "visual_brief": "Original evidence board; label each item with a source and date after verification.", "seconds": 34},
            {"narration": "A fair account also asks what the evidence cannot show, and what a reasonable counterpoint might be.", "visual_brief": "Two-column evidence and limitations graphic.", "seconds": 30},
            {"narration": "Then connect the evidence to the practical stakes without overstating certainty.", "visual_brief": "Original cause-and-effect diagram with uncertainty markers.", "seconds": 30},
            {"narration": "The conclusion should distinguish verified findings from open questions and invite viewers to inspect the sources.", "visual_brief": "Source-led summary and open-questions card.", "seconds": 20},
        ]
        return {
            "title": title, "hook": hook, "script": script,
            "description": "Research-first documentary outline. Add source citations and complete human verification before publication.",
            "tags": [niche, "documentary", "explainer"], "scenes": scenes,
            "factual_claims": [],
            "research_questions": [
                "What is the central question, and how is it defined?",
                "Which primary sources establish the timeline and key facts?",
                "What evidence contradicts or limits the main interpretation?",
                "What remains unknown or disputed?",
            ],
            "source_urls": list(source_urls or []), "verification_required": True,
            "originality_note": "Template outline only; no third-party video, transcript, footage, or factual claim was copied.",
            "research_notes_received": bool(research_notes.strip()),
        }
    if short:
        script = (
            f"{hook}\n\n"
            f"Start by separating the problem into three parts: what you already know, what is slowing you down, and what one small experiment could test. "
            f"Then try that experiment for a week and compare the result with your starting point.\n\n"
            f"The useful takeaway is not a magic shortcut. It is a repeatable way to learn what works for your situation. "
            f"Save this idea, test it, and keep the part that actually helps."
        )
        scenes = [
            {"narration": hook, "visual_brief": "Original title card; bold kinetic typography, no third-party footage.", "seconds": 5},
            {"narration": "Start by separating the problem into three parts: what you know, what is slowing you down, and what one small experiment could test.", "visual_brief": "Three original numbered cards with simple icons; demonstrate the framework.", "seconds": 9},
            {"narration": "Try that experiment for a week and compare the result with your starting point.", "visual_brief": "Simple one-week timeline and before/after checklist graphic.", "seconds": 7},
            {"narration": "The useful takeaway is not a magic shortcut. It is a repeatable way to learn what works for your situation.", "visual_brief": "Summary card with one memorable takeaway and save prompt.", "seconds": 8},
        ]
    else:
        script = (
            f"In this video, we will examine {title} as a practical problem-solving topic. "
            "First, define the outcome you actually want. Next, identify the bottleneck that keeps getting in the way. "
            "Then run a small, measurable test instead of changing everything at once. Compare the result with your starting point, "
            "keep what helped, and revise what did not. This is a framework, not a promise of a specific result. "
            "Before publishing, add verified sources for any factual or numerical claims and tailor the examples to the audience."
        )
        scenes = [
            {"narration": "In this video, we will examine the topic as a practical problem-solving question.", "visual_brief": "Original opener and question card.", "seconds": 8},
            {"narration": "First, define the outcome you actually want. Next, identify the bottleneck that keeps getting in the way.", "visual_brief": "Goal and bottleneck diagram with original icons.", "seconds": 14},
            {"narration": "Then run a small, measurable test instead of changing everything at once.", "visual_brief": "A/B experiment board; explain one variable at a time.", "seconds": 12},
            {"narration": "Compare the result with your starting point, keep what helped, and revise what did not.", "visual_brief": "Before-and-after scorecard and repeat loop.", "seconds": 12},
        ]
    return {
        "title": title,
        "hook": hook,
        "script": script,
        "description": "Original draft generated in local fallback mode. Verify facts and add sources before publication.",
        "tags": [niche, "explainer", "education"],
        "scenes": scenes,
        "factual_claims": [],
        "research_questions": [],
        "source_urls": list(source_urls or []),
        "verification_required": True,
        "originality_note": "Draft uses a general framework; no third-party video, transcript, or footage was copied.",
        "research_notes_received": bool(research_notes.strip()),
    }


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end < start:
        raise ValueError("LLM response did not contain a JSON object")
    return json.loads(cleaned[start:end + 1])


def _gemini(prompt: str) -> str:
    key = env("GEMINI_API_KEY")
    model = env("GEMINI_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{urllib.parse.quote(model)}:generateContent?key={urllib.parse.quote(key)}"
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}],
                       "generationConfig": {"temperature": 0.55, "responseMimeType": "application/json"}}).encode()
    request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=60) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data["candidates"][0]["content"]["parts"][0]["text"]


def _openai_compatible(prompt: str) -> str:
    base = env("LLM_BASE_URL").rstrip("/")
    if not base.endswith("/chat/completions"):
        base += "/chat/completions"
    body = json.dumps({
        "model": env("LLM_MODEL", "gpt-4o-mini"),
        "temperature": 0.55,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": "Return valid JSON only. Do not invent facts or copy other creators."},
            {"role": "user", "content": prompt},
        ],
    }).encode()
    request = urllib.request.Request(base, data=body, headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {env('LLM_API_KEY')}"
    }, method="POST")
    with urllib.request.urlopen(request, timeout=60) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def make_content(topic: str, niche: str, format_name: str,
                 audience: str = "United States, English-speaking", angle: str = "",
                 research_notes: str = "", source_urls: list[str] | None = None) -> tuple[dict[str, Any], str]:
    supplied_urls = list(dict.fromkeys(str(url).strip() for url in (source_urls or []) if str(url).strip()))[:20]
    research_notes = str(research_notes or "")[:12000]
    fallback = _fallback(topic, niche, format_name, angle, research_notes, supplied_urls)
    normalized_format = format_name.lower()
    short = normalized_format in {"short", "shorts", "youtube shorts"}
    documentary = normalized_format in {"documentary", "long-form documentary", "documentary long-form"}
    if short:
        length_note = "Create a 35–55 second YouTube Short, around 90–135 spoken words."
    elif documentary:
        length_note = (
            "Create a research-first, 4–6 minute documentary-style script in 6–9 scenes. "
            "Use a central question, context, evidence, counterpoint/limitations, stakes and a careful conclusion."
        )
    else:
        length_note = "Create a 4–6 minute long-form video outline and spoken script, with clear scene breaks."
    prompt = f"""Create one original YouTube video package for an {audience} audience.
Niche: {niche}
Topic: {topic}
Preferred original angle: {angle or 'Choose one specific, useful perspective'}
Format: {format_name}
{length_note}
EDITOR-SUPPLIED RESEARCH NOTES (unverified; use only as context):
{research_notes or '[none supplied]'}
EDITOR-SUPPLIED SOURCE URLS (starting points only; do not claim you opened or verified them):
{json.dumps(supplied_urls, ensure_ascii=False)}
Return a JSON object with these fields: title (string), hook (string), script (string), description (string), tags (array of strings), scenes (array of objects with narration, visual_brief, seconds), factual_claims (array of concise claims that need checking), research_questions (array of strings), source_urls (array of URLs), verification_required (boolean), originality_note (string).
Rules: Write an original explanation; do not copy, paraphrase, or reconstruct another channel's script/transcript. Do not use copyrighted clips. Never invent statistics, current events, quotes, studies, citations or source URLs. Any returned source_urls must be exact URLs from the editor-supplied list. If a factual claim is not directly supported by the supplied notes, put it in research_questions or omit it. The app does not fetch or validate sources. Keep verification_required=true. No guaranteed income claims. For finance, health, legal or safety topics, stay educational and flag expert review. Use visuals that can be made in-house or separately licensed. Make scenes distinct and useful, not repetitive template cards."""
    if documentary and not research_notes and not supplied_urls:
        prompt += "\nNo research has been supplied: produce a documentary structure and research questions, not asserted factual claims."
    try:
        if env("GEMINI_API_KEY"):
            raw = _gemini(prompt)
            mode = "Gemini"
        elif env("LLM_API_KEY") and env("LLM_BASE_URL"):
            raw = _openai_compatible(prompt)
            mode = "OpenAI-compatible LLM"
        else:
            return fallback, "local template · no LLM key configured"
        payload = _extract_json(raw)
        for key in ("title", "hook", "script", "description", "tags", "scenes"):
            if key not in payload:
                raise ValueError(f"LLM output missing required field: {key}")
        if not isinstance(payload["scenes"], list) or not payload["scenes"]:
            raise ValueError("LLM output needs at least one scene")
        payload.setdefault("factual_claims", [])
        payload.setdefault("research_questions", [])
        # Do not expose URLs invented by a model as citations. These remain editor-supplied,
        # unverified starting points until a human checks and records them.
        payload["source_urls"] = supplied_urls
        payload["verification_required"] = True
        payload.setdefault("originality_note", "Original draft; human review and source checking are still required.")
        payload["research_notes_received"] = bool(research_notes.strip())
        return payload, mode
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, KeyError, ValueError, json.JSONDecodeError) as exc:
        fallback["llm_error"] = f"{type(exc).__name__}: {exc}"
        return fallback, "local fallback · LLM request failed"


def suggest_topic(scan: dict[str, Any], recent_topics: list[str] | None = None) -> dict[str, str]:
    """Suggest a fresh topic from market metadata, without copying sampled videos."""
    recent_topics = recent_topics or []
    candidates = scan.get("candidates", [])
    if not candidates:
        raise ValueError("Run a market scan before requesting an agent-picked topic")
    top = candidates[0]
    evidence_titles = [str(e.get("title", "")) for e in top.get("evidence", []) if e.get("title")][:8]
    prompt = f"""Pick ONE original YouTube topic for a channel targeting US viewers.
Niche: {top.get('name','')}
Public-metadata opportunity score: {top.get('score','')}/100 (a screening score, NOT revenue data)
Sampled recent video titles (signals only; do not copy, paraphrase, or closely imitate any): {json.dumps(evidence_titles)}
Recently used topics on this channel (avoid these): {json.dumps(recent_topics[-20:])}
Return raw JSON exactly: {{\"topic\":\"...\",\"angle\":\"...\",\"why_now\":\"...\"}}
The idea must be meaningfully distinct, useful, feasible to research, and not depend on copyrighted clips, breaking claims, or guaranteed-income promises. If facts are needed, flag them for later human source-checking."""
    try:
        if env("GEMINI_API_KEY"):
            payload = _extract_json(_gemini(prompt))
        elif env("LLM_API_KEY") and env("LLM_BASE_URL"):
            payload = _extract_json(_openai_compatible(prompt))
        else:
            import datetime
            variants = [
                ("A beginner's checklist for testing", "Focus on a low-cost, measurable first experiment."),
                ("What to verify before choosing", "Separate useful evidence from marketing claims."),
                ("A simple workflow for evaluating", "Show a repeatable process rather than a shortcut."),
                ("Common mistakes when learning", "Explain how to spot and correct one avoidable mistake."),
                ("A practical comparison framework for", "Compare options using transparent criteria, not unsupported rankings."),
            ]
            start = datetime.date.today().toordinal() % len(variants)
            recent_set = {re.sub(r"\s+", " ", t).strip().lower() for t in recent_topics}
            selected = None
            for offset in range(len(variants)):
                lead, candidate_angle = variants[(start + offset) % len(variants)]
                candidate_topic = f"{lead} {top.get('name','this topic')}"
                if re.sub(r"\s+", " ", candidate_topic).strip().lower() not in recent_set:
                    selected = (candidate_topic, candidate_angle)
                    break
            if selected is None:
                lead, candidate_angle = variants[start]
                selected = (f"{lead} {top.get('name','this topic')} · new example", candidate_angle)
            topic, angle = selected
            return {"topic": topic, "angle": angle,
                    "why_now": "Demo fallback based on the current candidate niche; connect an LLM for richer topic planning."}
        topic = str(payload.get("topic", "")).strip()
        angle = str(payload.get("angle", "")).strip()
        if not topic or not angle:
            raise ValueError("Topic planner returned an incomplete response")
        return {"topic": topic[:180], "angle": angle[:240],
                "why_now": str(payload.get("why_now", "Selected from the current market-scan candidate."))[:500]}
    except Exception as exc:
        return {"topic": f"A practical checklist for evaluating {top.get('name','this topic')}",
                "angle": "Explain a useful test with transparent assumptions; verify any facts before publishing.",
                "why_now": f"Safe fallback after topic-planning error ({type(exc).__name__})."}
