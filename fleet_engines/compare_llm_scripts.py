import os
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FLEET_DIR = Path(__file__).resolve().parent
if str(FLEET_DIR) not in sys.path:
    sys.path.insert(0, str(FLEET_DIR))

from llm_engine import generate_channel3_script

topic = "अगर चांद अचानक गायब हो जाए, तो 24 घंटे में धरती पर क्या होगा?"

print("=" * 70)
print("🧪 TESTING CHANNEL 3 SCRIPT GENERATOR (MoneyPrinterTurbo Direct Formula)")
print("=" * 70)

t0 = time.time()
data = generate_channel3_script(topic=topic, pillar_name="Mind-Bending What-If Physics", lang="hi", word_count_target=70)
t_dur = time.time() - t0

print(f"✅ Generated via Groq in {t_dur:.2f}s!")
print("-" * 70)
print("TITLE :", data.get("title"))
print("HOOK  :", data.get("hook"))
print("SCRIPT:", data.get("script"))
print("CTA   :", data.get("cta"))
print("-" * 70)
print("WORDS :", len(data.get("script", "").split()))
print("=" * 70)
