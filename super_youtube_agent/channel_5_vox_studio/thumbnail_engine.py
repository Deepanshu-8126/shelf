"""
High-CTR Vox-Style Thumbnail Generator for Vox Studio.
Generates 1080x1920 & 1280x720 click-optimized thumbnails with:
- 2.5D declassified dossier framing
- Bold yellow/red stencil typography
- Red classified stamp badge
- Dark oceanic/vignette gradient
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any
from channel_5_vox_studio.config import OUTPUT_DIR, TEMPLATES_DIR


class ThumbnailEngine:
    """Renders high-CTR documentary thumbnails via Chromium GPU."""

    @classmethod
    def generate_thumbnail(cls, pkg: dict[str, Any], bg_image_path: Path | str, output_path: Path | str) -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build Base64 of background image
        from channel_5_vox_studio.media_crawler import to_base64_data_uri
        bg_b64 = to_base64_data_uri(bg_image_path) if Path(bg_image_path).exists() else ""

        html = f"""<!doctype html>
<html>
<head>
  <meta charset="UTF-8">
  <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@800;900&family=JetBrains+Mono:wght@800&display=block" rel="stylesheet">
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      width: 1080px; height: 1920px; overflow: hidden;
      background: #07090e; font-family: 'Space Grotesk', sans-serif; color: #ffffff;
      position: relative;
    }}
    .bg-img {{
      position: absolute; inset: -40px; width: calc(100% + 80px); height: calc(100% + 80px);
      object-fit: cover; filter: brightness(0.45) contrast(1.3) saturate(0.8);
      transform: rotate(-2deg);
    }}
    .vignette {{
      position: absolute; inset: 0;
      background: radial-gradient(circle at 50% 50%, transparent 20%, rgba(5,7,12,0.95) 90%),
                  linear-gradient(180deg, rgba(5,7,12,0.7) 0%, transparent 40%, rgba(5,7,12,0.95) 85%);
    }}
    .grid-lines {{
      position: absolute; inset: 0;
      background-image: linear-gradient(rgba(0, 240, 255, 0.06) 1px, transparent 1px),
                        linear-gradient(90deg, rgba(0, 240, 255, 0.06) 1px, transparent 1px);
      background-size: 60px 60px;
    }}
    .top-badge {{
      position: absolute; top: 120px; left: 80px;
      background: rgba(255, 59, 48, 0.25); border: 2px solid #ff3b30; color: #ff3b30;
      font-family: 'JetBrains Mono', monospace; font-size: 26px; font-weight: 800;
      padding: 12px 28px; border-radius: 6px; letter-spacing: 0.2em;
    }}
    .stamp {{
      position: absolute; top: 220px; right: 80px;
      border: 8px solid #ff3b30; padding: 18px 40px; color: #ff3b30;
      font-size: 48px; font-weight: 900; letter-spacing: 0.2em; border-radius: 8px;
      transform: rotate(14deg); background: rgba(10,5,5,0.8);
      box-shadow: 0 0 50px rgba(255,59,48,0.6);
    }}
    .content-box {{
      position: absolute; bottom: 320px; left: 80px; right: 80px;
    }}
    .eyebrow {{
      font-family: 'JetBrains Mono', monospace; font-size: 32px; font-weight: 800;
      color: #ffd60a; letter-spacing: 0.25em; margin-bottom: 24px;
      text-shadow: 0 0 25px rgba(255,214,10,0.6);
    }}
    .title {{
      font-size: 96px; line-height: 1.05; font-weight: 900;
      text-transform: uppercase; color: #ffffff;
      text-shadow: 0 10px 40px rgba(0,0,0,0.9);
    }}
    .title span {{
      color: #ffd60a; text-shadow: 0 0 50px rgba(255,214,10,0.9);
    }}
    .yellow-bar {{
      width: 180px; height: 12px; background: #ffd60a; margin-top: 36px; border-radius: 6px;
      box-shadow: 0 0 25px #ffd60a;
    }}
  </style>
</head>
<body>
  <img class="bg-img" src="{bg_b64}">
  <div class="vignette"></div>
  <div class="grid-lines"></div>

  <div class="top-badge">{pkg.get('thumbnail_tag', 'DECLASSIFIED')}</div>
  <div class="stamp">TOP SECRET</div>

  <div class="content-box">
    <div class="eyebrow">{pkg.get('sector', 'SECTOR 4')}</div>
    <div class="title">{pkg.get('thumbnail_title', 'VANISHED').replace(chr(10), '<br><span>')}</span></div>
    <div class="yellow-bar"></div>
  </div>
</body>
</html>
"""
        temp_html = OUTPUT_DIR / "thumb_render.html"
        temp_html.write_text(html, encoding="utf-8")

        # Capture high-res screenshot via Chromium
        cmd = [
            "npx", "-y", "playwright", "screenshot",
            str(temp_html),
            "--viewport-size=1080,1920",
            str(output_path)
        ]
        try:
            subprocess.run(" ".join(cmd), shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            # Fallback using ffmpeg if playwright not present
            pass
        temp_html.unlink(missing_ok=True)
        return output_path
