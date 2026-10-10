"""
Universal Humanized Script & CTA Engine.
NOW A THIN WRAPPER around fleet_engines/llm_engine.py.
All logic lives in llm_engine.py - do not duplicate here.
"""
import sys
from pathlib import Path

# Ensure llm_engine is importable
_FLEET_DIR = Path(__file__).resolve().parent
if str(_FLEET_DIR) not in sys.path:
    sys.path.insert(0, str(_FLEET_DIR))

from llm_engine import (  # noqa: F401  (re-exported)
    generate_channel2_script as generate_humanized_script,
    generate_channel3_script,
    sanitize_script,
    BANNED_AI_PHRASES,
    HINDI_SLOP_REPLACEMENTS,
    GROQ_API_KEY,
    llm_complete,
    llm_json,
)

# Backwards-compatible aliases
__all__ = [
    "generate_humanized_script",
    "generate_channel3_script",
    "sanitize_script",
    "BANNED_AI_PHRASES",
    "HINDI_SLOP_REPLACEMENTS",
    "GROQ_API_KEY",
    "llm_complete",
    "llm_json",
]

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    from llm_engine import generate_channel2_script
    sample = generate_channel2_script("The FBI 4-second silence rule", lang="hi")
    print("Title:", sample["title"])
    print("Hook:", sample["hook"])
    print("Script:", sample["script"])
    print("CTA:", sample["cta"])
