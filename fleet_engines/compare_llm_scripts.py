import os
import sys
import time
import json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FLEET_DIR = Path(__file__).resolve().parent
if str(FLEET_DIR) not in sys.path:
    sys.path.insert(0, str(FLEET_DIR))

from llm_engine import generate_channel3_script, _COSMIC_SYSTEM, sanitize_script

load_dotenv("d:/facts_yt/.env")

openai_key = os.getenv("OPENAI_API_KEY")
groq_key = os.getenv("GROQ_API_KEY")
topic = "अगर चांद अचानक गायब हो जाए, तो 24 घंटे में धरती पर क्या होगा?"

print("=" * 70)
print("🧪 TESTING LLM ENGINES & NATURAL SPOKEN HINDI GENERATION")
print("=" * 70)

# 1. Test OpenAI
print("\n[1] Testing OpenAI (platform.openai.com)...")
try:
    o_client = OpenAI(api_key=openai_key)
    t0 = time.time()
    chat_o = o_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": _COSMIC_SYSTEM},
            {"role": "user", "content": f"Topic: {topic}\nTarget Length: 75 words in spoken Devanagari Hindi."}
        ],
        response_format={"type": "json_object"},
        timeout=15,
    )
    t_o = time.time() - t0
    data_o = json.loads(chat_o.choices[0].message.content)
    clean_script = sanitize_script(data_o.get("script", ""))
    print(f"✅ OpenAI Status: WORKING! (Speed: {t_o:.2f}s)")
    print(f"Title: {data_o.get('title')}")
    print(f"Script: {clean_script}")
    print(f"Words: {len(clean_script.split())}")
except Exception as e:
    print(f"❌ OpenAI Status: FAILED ({e})")
    print("👉 Note: OpenAI account has 0 credits (credit_balance_exhausted).")

# 2. Test Groq via Central Engine (openai/gpt-oss-120b)
print("\n[2] Testing Groq (120-Billion Parameter Model via llm_engine)...")
try:
    t0 = time.time()
    data_g = generate_channel3_script(topic=topic, pillar_name="Mind-Bending What-If Physics", lang="hi", word_count_target=75)
    t_g = time.time() - t0
    print(f"✅ Groq Status: ACTIVE & WORKING! (Speed: {t_g:.2f}s)")
    print(f"Title: {data_g.get('title')}")
    print(f"Hook:  {data_g.get('hook')}")
    print(f"Script: {data_g.get('script')}")
    print(f"CTA:   {data_g.get('cta')}")
    print(f"Words: {len(data_g.get('script', '').split())}")
except Exception as e:
    print(f"❌ Groq Error: {e}")

print("=" * 70)
