import os
import json
import sys
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

system_prompt = """You are a world-class viral YouTube Shorts scriptwriter specializing in r/pettyrevenge and r/EntitledPeople drama.
Your scripts consistently achieve 90%+ retention and thousands of comments because they follow a strict 4-stage formula:

1. [0:00 - 0:03s] EXPLOSIVE HOOK: Line 1 drops the viewer straight into high-stakes conflict (starts with 'I...'). Zero filler throat-clearing.
2. [0:03 - 0:30s] DRAMATIC TENSION: Punchy, spoken dialogue under 12 words per sentence. Relatable human outrage.
3. [0:30 - 0:40s] SATISFYING PAYOFF: Bad actor gets caught, humiliated, or outsmarted. Fast mic-drop victory.
4. [0:40 - 0:45s] PROVOCATIVE CTA ENDING: Final sentence MUST be a compelling question that sparks fierce debate in the comments.
   (Examples: 'Did I take it too far, or did he deserve every bit of it? Drop your thoughts below.' | 'Would you have done the exact same thing? Let me know below.')

Strict Constraints:
- Length: Exactly between 120 and 135 words (perfect for ~42 seconds of speech).
- Language: 100% natural, crisp, conversational English.
- Output JSON format strictly: {"question": "...", "story": "..."}"""

few_shots = [
    {
        "role": "user",
        "content": "Theme: A toxic boss demands unpaid overtime on an employee's milestone day, but the employee uses company policy for revenge."
    },
    {
        "role": "assistant",
        "content": json.dumps({
            "question": "What's the pettiest revenge you've ever pulled on a toxic boss?",
            "story": "My manager told me: 'If you refuse unpaid overtime, turn in your laptop right now.' So I did. What he forgot was that I was the sole administrator of their cloud database. On Monday morning, their entire checkout system went pitch black. When he called me screaming that the store was losing ten thousand dollars an hour, I answered calmly: 'My freelance emergency rate is two hundred dollars an hour, paid upfront.' He wired the money in three minutes flat. Did I take it too far, or did he deserve every bit of it? Drop your thoughts below."
        })
    },
    {
        "role": "user",
        "content": "Theme: An arrogant roommate secretly steals groceries and lies to everyone's face, so the victim sets an undeniable visual trap."
    }
]

res = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "system", "content": system_prompt}] + few_shots,
    response_format={"type": "json_object"},
    temperature=0.8
)

data = json.loads(res.choices[0].message.content)
print(f"QUESTION: {data['question']}")
print(f"STORY ({len(data['story'].split())} words):\n{data['story']}")
