import sys
from pathlib import Path

# Add fleet_engines to path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "channel_2"))

from channel_2.run_channel_2 import render_short

if __name__ == "__main__":
    print("🎬 Testing Channel 2 (Vox Noir) - 10 Second 100% Real 4K Clip...")
    script = "Four seconds of absolute silence can break any human mind. When federal agents interrogate a suspect, they never argue. They just stare."
    out_video = render_short(
        pillar_id=2,
        topic="The FBI 4-second silence rule that exposes lies",
        lang="en",
        custom_script=script,
        custom_title="The FBI 4-Second Silence Rule"
    )
    print(f"\n🎉 DONE! Generated 4K Noir Video:\n{out_video}")
