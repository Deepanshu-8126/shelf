"""Offline checks: no network, no ffmpeg, no API keys."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoclip import captions, hooks, load_profile          # noqa: E402
from autoclip.transform import video_chain                  # noqa: E402

WORDS = [{"word": w, "start": i * 0.45, "end": i * 0.45 + 0.4}
         for i, w in enumerate(
             ("अबे गाली देके गया है ना हां यार दो तीन बार गाली देके गया अब ये गाड़ी "
              "खड़ी सामने पुलिस को बता देते हैं सर ये है गाड़ी नंबर भाई देखो "
              "कितना बड़ा झगड़ा हो गया यहां पर").split())]


def test_hooks():
    picked = hooks.lexicon_select(WORDS, n=1, genre="reality", lo=5, hi=30)
    assert picked and picked[0]["end"] > picked[0]["start"], "no clip picked"
    print(f"  hooks        ok  -> {picked[0]['start']:.1f}-{picked[0]['end']:.1f}s "
          f"score={picked[0]['score']}")


def test_captions():
    with tempfile.TemporaryDirectory() as td:
        p = captions.build(WORDS, Path(td) / "a.ass", width=1080, height=1920,
                           font="Noto Sans Devanagari ExtraBold", margin_v=600)
        txt = p.read_text(encoding="utf-8")
        assert "Dialogue:" in txt and r"\k" in txt, "no karaoke events"
        assert captions.to_srt(WORDS).startswith("1\n")
        print(f"  captions     ok  -> {txt.count('Dialogue:')} events")


def test_placement():
    mv = captions.auto_margin_v(1080, 1920, 1280, 720, True)
    assert mv > int(1920 * 0.17), "captions would sit under the Shorts UI"
    print(f"  placement    ok  -> margin_v={mv}")


def test_transform_levels():
    for lvl in range(4):
        chain, p = video_chain(1080, 1920, lvl, [[1, 3]])
        assert "[base]" in chain
        assert ("hflip" in chain) == p["mirror"]
    print("  transform    ok  -> levels 0-3")


def test_profiles():
    cfg = load_profile(None)
    for k in ("width", "height", "caption_font", "title_font", "emoji_dir"):
        assert k in cfg, f"profile missing {k}"
    assert Path(cfg["title_font"]).exists(), "bundled font missing"
    print("  profiles     ok  -> default.json + assets present")


ROOT = Path(__file__).resolve().parent.parent


def test_caption_box():
    """A plate must switch BorderStyle to 3 and keywords must get their colour."""
    from autoclip import captions
    import tempfile
    w = [{"word": "this", "start": 0.0, "end": 0.3},
         {"word": "insane", "start": 0.3, "end": 0.8},
         {"word": "thing", "start": 0.8, "end": 1.2}]
    d = Path(tempfile.mkdtemp())
    plain = captions.build(w, d / "a.ass", width=1080, height=1920,
                           font="Arial", style="hormozi")
    boxed = captions.build(w, d / "b.ass", width=1080, height=1920,
                           font="Arial", style="hormozi", box=True)
    ps = [l for l in plain.read_text().splitlines() if l.startswith("Style: Pop")][0]
    bs = [l for l in boxed.read_text().splitlines() if l.startswith("Style: Pop")][0]
    assert ps.split(",")[15] == "1", ps
    assert bs.split(",")[15] == "3", bs
    assert "&H005CF0FF" in plain.read_text(), "keyword 'insane' was not coloured"
    print("  caption_box   ok  -> BorderStyle 1->3, keyword coloured")


def test_disk():
    """The silent killer: a full /tmp stalls yt-dlp instead of erroring.

    Guards two things that cost a whole 70-minute run once already -- the work
    dir must not sit on a tiny tmpfs, and an oversized source must step the
    height down rather than be attempted and die with an empty log.
    """
    import shutil
    from autoclip.pipeline import DEFAULT_WORKDIR
    from autoclip.sources import fit_height

    work = Path(DEFAULT_WORKDIR)
    work.mkdir(parents=True, exist_ok=True)
    free_gb = shutil.disk_usage(work).free / 1e9
    assert free_gb > 3, f"workdir {work} has only {free_gb:.1f} GB free"

    # A source twice the size of the free space must not come back as 1080p.
    too_big = free_gb * 1000 * 2
    assert fit_height(4200, work, 1080, known_mb=too_big) < 1080
    # A small one must be left alone.
    assert fit_height(480, work, 1080, known_mb=73) == 1080
    print(f"  disk         ok  -> {work} {free_gb:.0f} GB free, step-down works")


def test_cli():
    """--help must parse: argparse errors only surface at runtime, and a
    duplicate kwarg once shipped a CLI that could not even start."""
    import subprocess
    import sys
    r = subprocess.run([sys.executable, "-m", "autoclip.cli", "--help"],
                       capture_output=True, text=True, cwd=str(ROOT))
    assert r.returncode == 0, r.stderr[-400:]
    for flag in ("--caption-style", "--height", "--crf", "--clips"):
        assert flag in r.stdout, f"{flag} missing from --help"
    print(f"  cli          ok  -> --help parses, {len(r.stdout.splitlines())} lines")


if __name__ == "__main__":
    print("autoclip offline tests")
    for fn in (test_hooks, test_captions, test_placement, test_transform_levels,
               test_profiles, test_caption_box, test_disk, test_cli):
        fn()
    print("all passed")
