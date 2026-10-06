"""Transformation chain — reframe, grade, and optional fingerprint-breaking tweaks.

READ THIS before trusting `safe_level`:
  * Content ID claims are NOT copyright strikes, and claims alone don't hurt the channel
    (support.google.com/youtube/answer/6013276). But a Short of 1-3 minutes with an
    active claim gets BLOCKED, so claims matter a lot for this format.
  * Mirroring / zoom / speed / grading lower the chance of a *video* fingerprint match.
    AUDIO is matched separately and is far harder to defeat — a music bed will usually
    still be caught. These tricks are mitigation, not immunity.
  * The real risk for clip channels is the reused-content policy, which is judged on
    whether you ADD value (commentary, edits, captions, reaction). It applies to the
    whole channel and is independent of copyright/permission.
      -> So: keep captions + titles + your own commentary track. Those also happen to be
         the strongest fingerprint breakers.
"""
from __future__ import annotations

SAFE = {
    0: dict(zoom=1.00, mirror=False, speed=1.00, hue=0, sat=1.00, con=1.00, grain=0),
    1: dict(zoom=1.03, mirror=False, speed=1.00, hue=0, sat=1.12, con=1.05, grain=0),
    2: dict(zoom=1.06, mirror=False, speed=1.03, hue=3, sat=1.18, con=1.08, grain=2),
    3: dict(zoom=1.10, mirror=True, speed=1.05, hue=6, sat=1.22, con=1.10, grain=4),
}


def video_chain(width: int, height: int, level: int = 1, punches: list | None = None,
                punch_zoom: float = 1.14, blur_bg: bool = True,
                extra: str = "") -> tuple[str, dict]:
    """Return (filter_complex_prefix producing [base], params used).

    The source is cropped (punch-ins + safe zoom), graded, fitted to w:h over a blurred
    backdrop. Mirroring is applied LAST on the composed frame so captions stay readable.
    """
    p = SAFE[max(0, min(3, level))]
    z_terms = [f"{p['zoom']:.3f}"]
    for a, b in (punches or []):
        z_terms.append(f"{punch_zoom - 1:.3f}*between(t,{a:.2f},{b:.2f})")
    z = "+".join(z_terms)

    grade = (f"eq=contrast={p['con']:.3f}:saturation={p['sat']:.3f}:brightness=0.012,"
             f"unsharp=5:5:0.5")
    if p["hue"]:
        grade = f"hue=h={p['hue']}," + grade
    if p["grain"]:
        grade += f",noise=alls={p['grain']}:allf=t"
    if extra:
        grade += "," + extra

    parts = []
    if blur_bg:
        # Blurring at full 1080x1920 is the single most expensive filter in the chain.
        # Downscale 4x, blur cheaply, upscale back: visually identical, ~3x faster.
        bw, bh = width // 4, height // 4
        parts.append(f"[0:v]scale={bw}:{bh}:force_original_aspect_ratio=increase,"
                     f"crop={bw}:{bh},gblur=sigma=7,eq=brightness=-0.08,"
                     f"scale={width}:{height}:flags=bilinear[bg]")
        parts.append(f"[0:v]crop=w='iw/({z})':h='ih/({z})':x='(iw-ow)/2':y='(ih-oh)/2',"
                     f"scale={width}:-2:force_original_aspect_ratio=decrease,{grade}[fg]")
        parts.append(f"[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1[base0]")
    else:
        parts.append(f"[0:v]crop=w='iw/({z})':h='ih/({z})':x='(iw-ow)/2':y='(ih-oh)/2',"
                     f"scale={width}:{height}:force_original_aspect_ratio=increase,"
                     f"crop={width}:{height},{grade},setsar=1[base0]")
    parts.append(f"[base0]{'hflip' if p['mirror'] else 'null'}[base]")
    return ";".join(parts), p


def audio_chain(level: int = 1) -> str:
    """Pitch-preserved speed-up; also shifts the audio fingerprint slightly."""
    p = SAFE[max(0, min(3, level))]
    if p["speed"] == 1.0:
        return "anull"
    return f"atempo={p['speed']:.3f}"


def speed_of(level: int) -> float:
    return SAFE[max(0, min(3, level))]["speed"]
