"""
HyperFrames 2.5D Motion Graphics Template Engine for Vox Studio.
Features:
- Full-Screen Real Satellite Nautical Map with Animated Coordinates & Triangle Vector
- 3D Floating Archival Newspaper Clipping with Synchronized Highlighter Wipe
- Real Historical Photo / Video Ken Burns with HUD Tracking Pins
- Kinetic Glowing Pop-up Word-by-Word Captions (Karaoke Style)
"""
from pathlib import Path
from typing import Any
from vox_studio.media_crawler import to_base64_data_uri


def generate_vox_html(pkg: dict[str, Any], media_kit: dict[str, list[Path]], has_video: bool = False) -> str:
    """Generates the self-contained HTML/CSS/GSAP composition with Base64 embedded assets."""
    
    # 1. Map Image
    map_b64 = ""
    if media_kit["maps"]:
        map_b64 = to_base64_data_uri(media_kit["maps"][0])
    
    # 2. Document / Newspaper Image
    doc_b64 = ""
    if media_kit["documents"]:
        doc_b64 = to_base64_data_uri(media_kit["documents"][0])
    elif media_kit["photos"]:
        doc_b64 = to_base64_data_uri(media_kit["photos"][0])
        
    # 3. Historical Photo
    photo_b64 = ""
    if media_kit["photos"]:
        photo_b64 = to_base64_data_uri(media_kit["photos"][-1])
    elif media_kit["documents"]:
        photo_b64 = to_base64_data_uri(media_kit["documents"][-1])

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{pkg.get('headline', 'Vox Studio')}</title>
  <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@600;700;800;900&family=JetBrains+Mono:wght@500;700;800&family=Playfair+Display:ital,wght@0,700;0,900;1,700&display=block" rel="stylesheet">
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    html, body {{
      width: 1080px; height: 1920px; overflow: hidden;
      background: #06080d; font-family: 'Space Grotesk', sans-serif; color: #ffffff;
    }}
    #root {{
      width: 1080px; height: 1920px; position: relative; overflow: hidden; perspective: 1400px;
      background: #06080d;
    }}

    /* FILM GRAIN & VIGNETTE OVERLAY */
    .film-overlay {{
      position: absolute; inset: 0;
      background: radial-gradient(circle at 50% 50%, transparent 45%, rgba(0,0,0,0.85) 100%),
                  repeating-linear-gradient(0deg, rgba(0,0,0,0.12) 0px, rgba(0,0,0,0.12) 2px, transparent 2px, transparent 4px);
      pointer-events: none; z-index: 100;
    }}

    /* GLOBAL TOP HUD */
    .global-hud {{
      position: absolute; top: 80px; left: 60px; right: 60px;
      display: flex; justify-content: space-between; align-items: center;
      padding: 16px 28px; background: rgba(8, 12, 20, 0.85); backdrop-filter: blur(14px);
      border: 1px solid rgba(255, 255, 255, 0.15); border-left: 5px solid #ff3b30;
      z-index: 90; font-family: 'JetBrains Mono', monospace; font-size: 20px; letter-spacing: 0.16em;
    }}
    .hud-title {{ color: #ffffff; font-weight: 700; }}
    .hud-badge {{
      padding: 6px 14px; background: rgba(255, 59, 48, 0.25); border: 1px solid #ff3b30;
      color: #ff3b30; font-weight: 800; border-radius: 4px; font-size: 16px;
    }}

    /* COMMON SCENE CONTAINER */
    .scene {{
      position: absolute; inset: 0; width: 1080px; height: 1920px; opacity: 0; visibility: hidden;
    }}

    /* ========================================================
       SCENE 1: FULL-SCREEN 2.5D REAL GEOGRAPHIC MAP & VECTOR
       ======================================================== */
    #scene1 {{ background: #070a10; }}
    .map-bg-wrapper {{
      position: absolute; inset: -60px;
      transform-origin: center center;
      overflow: hidden;
    }}
    .map-real-img {{
      width: 100%; height: 100%; object-fit: cover;
      filter: brightness(0.65) contrast(1.25) saturate(0.85);
    }}
    .map-grid-overlay {{
      position: absolute; inset: 0;
      background-image: linear-gradient(rgba(0, 240, 255, 0.08) 1px, transparent 1px),
                        linear-gradient(90deg, rgba(0, 240, 255, 0.08) 1px, transparent 1px);
      background-size: 80px 80px;
    }}
    .map-svg-layer {{
      position: absolute; inset: 0; width: 1080px; height: 1920px; z-index: 20;
    }}
    .geo-pin {{
      position: absolute; transform: translate(-50%, -50%); z-index: 30;
      display: flex; flex-direction: column; align-items: center; gap: 8px;
    }}
    .pin-pulse {{
      width: 22px; height: 22px; border-radius: 50%; background: #ffd60a;
      box-shadow: 0 0 25px #ffd60a, 0 0 50px rgba(255, 214, 10, 0.6);
    }}
    .pin-label {{
      background: rgba(8, 12, 20, 0.9); padding: 6px 14px; border: 1px solid rgba(255, 214, 10, 0.5);
      font-size: 20px; font-weight: 800; color: #ffd60a; letter-spacing: 0.1em;
      border-radius: 4px; white-space: nowrap;
    }}
    .stamp-classified {{
      position: absolute; top: 340px; left: 50%; transform: translate(-50%, -50%) rotate(-10deg) scale(2.0);
      border: 8px solid #ff3b30; padding: 18px 50px; color: #ff3b30;
      font-size: 50px; font-weight: 900; letter-spacing: 0.25em; border-radius: 8px;
      background: rgba(10, 5, 5, 0.85);
      box-shadow: 0 0 45px rgba(255, 59, 48, 0.7), inset 0 0 25px rgba(255, 59, 48, 0.4);
      opacity: 0; z-index: 50;
    }}

    /* ========================================================
       SCENE 2: REAL ARCHIVAL NEWSPAPER + HIGHLIGHTER WIPE
       ======================================================== */
    #scene2 {{ background: #0c0d12; }}
    .paper-desk {{
      position: absolute; top: 720px; left: 50%;
      transform: translate(-50%, -50%) rotateX(12deg) rotateY(-8deg) rotateZ(2deg);
      transform-style: preserve-3d; width: 940px; height: 1180px;
      box-shadow: 0 50px 120px rgba(0,0,0,0.95);
      border-radius: 8px; overflow: hidden;
      border: 1px solid rgba(255,255,255,0.18);
      background: #dfd5c6;
    }}
    .newspaper-img {{
      width: 100%; height: 100%; object-fit: cover;
      filter: contrast(1.15) brightness(0.95);
    }}
    .highlighter-strip {{
      position: absolute; top: 460px; left: 80px; width: 780px; height: 64px;
      background: rgba(255, 230, 0, 0.85); mix-blend-mode: multiply;
      transform: scaleX(0); transform-origin: left center;
      border-radius: 4px; box-shadow: 0 0 20px rgba(255, 230, 0, 0.5);
    }}

    /* ========================================================
       SCENE 3: REAL ARCHIVAL EVIDENCE KEN BURNS + HUD
       ======================================================== */
    #scene3 {{ background: #07090e; }}
    .evidence-frame {{
      position: absolute; top: 700px; left: 50%; transform: translate(-50%, -50%);
      width: 940px; height: 980px; border: 3px solid rgba(255,255,255,0.2); overflow: hidden;
      box-shadow: 0 45px 120px rgba(0,0,0,0.95); border-radius: 8px;
    }}
    .evidence-img {{
      width: 100%; height: 100%; object-fit: cover; transform: scale(1.0);
    }}
    .evidence-tag-top {{
      position: absolute; top: 220px; left: 90px; padding: 12px 26px;
      background: rgba(0, 240, 255, 0.2); border: 2px solid #00f0ff; color: #00f0ff;
      font-size: 24px; font-weight: 800; backdrop-filter: blur(12px); border-radius: 6px; opacity: 0;
    }}
    .evidence-tag-bottom {{
      position: absolute; bottom: 220px; right: 90px; padding: 12px 26px;
      background: rgba(255, 214, 10, 0.2); border: 2px solid #ffd60a; color: #ffd60a;
      font-size: 24px; font-weight: 800; backdrop-filter: blur(12px); border-radius: 6px; opacity: 0;
    }}

    /* ========================================================
       SCENE 4: CLIMAX QUESTION & KINETIC HOOK
       ======================================================== */
    #scene4 {{ background: radial-gradient(circle at 50% 50%, #1c102a 0%, #06040a 85%); }}
    .climax-box {{
      position: absolute; top: 740px; left: 70px; right: 70px; transform: translateY(-50%); text-align: center;
    }}
    .climax-tag {{
      font-family: 'JetBrains Mono', monospace; font-size: 26px; letter-spacing: 0.3em;
      color: #ff3b30; margin-bottom: 28px; font-weight: 800;
    }}
    .climax-text {{
      font-size: 68px; line-height: 1.15; font-weight: 900;
      text-transform: uppercase; color: #ffffff;
    }}
    .climax-gold {{
      color: #ffd60a; text-shadow: 0 0 45px rgba(255, 214, 10, 0.9), 0 0 90px rgba(255, 214, 10, 0.4);
    }}

    /* ========================================================
       DYNAMIC GLOWING POP-UP CAPTIONS (KARAOKE POP EFFECT)
       ======================================================== */
    .caption-wrapper {{
      position: absolute; bottom: 200px; left: 50px; right: 50px;
      background: rgba(6, 9, 15, 0.92); backdrop-filter: blur(20px);
      border: 2px solid rgba(255, 255, 255, 0.18); border-radius: 16px;
      padding: 32px 36px; text-align: center; z-index: 95;
      box-shadow: 0 20px 60px rgba(0,0,0,0.8);
    }}
    .caption-content {{
      font-size: 46px; font-weight: 800; line-height: 1.32; color: #ffffff;
      letter-spacing: -0.01em;
    }}
    .cap-active {{
      color: #ffd60a; text-shadow: 0 0 30px rgba(255, 214, 10, 0.9);
      display: inline-block; transform: scale(1.08); transition: all 0.15s ease;
    }}
  </style>
</head>
<body>
  <div id="root" data-composition-id="main" data-start="0" data-duration="15.0" data-width="1080" data-height="1920">
    <div class="film-overlay"></div>

    <!-- GLOBAL HUD -->
    <div class="global-hud">
      <div class="hud-title">{pkg.get('sector', 'SECTOR // ATLANTIC 25°N 71°W')}</div>
      <div class="hud-badge">CLASSIFIED FILE</div>
    </div>

    <!-- SCENE 1: FULL-SCREEN REAL MAP WITH TRIANGLE VECTOR -->
    <div id="scene1" class="scene">
      <div class="map-bg-wrapper" id="s1-mapwrap">
        <img class="map-real-img" id="s1-mapimg" src="{map_b64}">
        <div class="map-grid-overlay"></div>
      </div>
      
      <!-- SVG Animated Triangle Vector -->
      <svg class="map-svg-layer" viewBox="0 0 1080 1920">
        <!-- Triangle Glow Area -->
        <polygon id="tri-poly" points="260,620 840,460 520,1180" 
                 fill="rgba(255, 59, 48, 0.15)" stroke="none" opacity="0"/>
        <!-- Animated Triangle Lines -->
        <path id="tri-line" d="M 260 620 L 840 460 L 520 1180 Z" 
              fill="none" stroke="#ff3b30" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"
              stroke-dasharray="2500" stroke-dashoffset="2500"/>
      </svg>

      <!-- Geographic Coordinates Pins -->
      <div class="geo-pin" id="pin-miami" style="top: 620px; left: 260px; opacity: 0;">
        <div class="pin-pulse"></div>
        <div class="pin-label">MIAMI, FL</div>
      </div>
      <div class="geo-pin" id="pin-bermuda" style="top: 460px; left: 840px; opacity: 0;">
        <div class="pin-pulse"></div>
        <div class="pin-label">BERMUDA</div>
      </div>
      <div class="geo-pin" id="pin-sanjuan" style="top: 1180px; left: 520px; opacity: 0;">
        <div class="pin-pulse"></div>
        <div class="pin-label">SAN JUAN, PR</div>
      </div>

      <!-- Stamp -->
      <div class="stamp-classified" id="s1-stamp">{pkg.get('stamp', 'TOP SECRET // NAVAL LOG')}</div>
    </div>

    <!-- SCENE 2: REAL NEWSPAPER + HIGHLIGHTER WIPE -->
    <div id="scene2" class="scene">
      <div class="paper-desk" id="s2-paper">
        <img class="newspaper-img" src="{doc_b64}">
        <div class="highlighter-strip" id="s2-marker"></div>
      </div>
    </div>

    <!-- SCENE 3: REAL ARCHIVAL EVIDENCE KEN BURNS + HUD -->
    <div id="scene3" class="scene">
      <div class="evidence-frame" id="s3-frame">
        <img class="evidence-img" id="s3-img" src="{photo_b64}">
        <div class="evidence-tag-top" id="s3-tag1">{pkg.get('badge1', 'FLIGHT 19 // TBM AVENGER')}</div>
        <div class="evidence-tag-bottom" id="s3-tag2">{pkg.get('badge2', '5 BOMBERS DISAPPEARED')}</div>
      </div>
    </div>

    <!-- SCENE 4: CLIMAX QUESTION -->
    <div id="scene4" class="scene">
      <div class="climax-box">
        <div class="climax-tag">THE UNRESOLVED EVIDENCE</div>
        <div class="climax-text">
          {pkg.get('climax_q1', 'WHERE ARE THE WRECKS?')}<br>
          <span class="climax-gold">{pkg.get('climax_q2', 'OR WERE THEY NEVER LOST AT SEA?')}</span>
        </div>
      </div>
    </div>

    <!-- GLOWING POP-UP CAPTION CARD -->
    <div class="caption-wrapper">
      <div class="caption-content" id="captionBox">
        <span class="cap-active" id="capWord">{pkg['subtitles'][0]}</span>
      </div>
    </div>
  </div>

  <script>
    window.__timelines = window.__timelines || {{}};
    const tl = gsap.timeline({{ paused: true }});

    // -------------------------------------------------------------
    // SCENE 1: (0.0s - 4.5s) Full-Screen Map Zoom + Triangle Vector Draw
    // -------------------------------------------------------------
    tl.set("#scene1", {{ autoAlpha: 1 }}, 0.0);
    tl.fromTo("#s1-mapwrap", 
      {{ scale: 1.0, rotation: 0 }}, 
      {{ scale: 1.25, rotation: -2, duration: 4.5, ease: "power1.out" }}, 0.0);
    
    // Draw Triangle Vector
    tl.to("#tri-line", {{ strokeDashoffset: 0, duration: 1.8, ease: "power2.out" }}, 0.6);
    tl.to("#tri-poly", {{ opacity: 0.6, duration: 1.0, ease: "power1.out" }}, 1.8);
    
    // Pop Pins
    tl.to(["#pin-miami", "#pin-bermuda", "#pin-sanjuan"], {{ opacity: 1, scale: 1.1, stagger: 0.35, ease: "back.out(2)" }}, 0.8);

    // Stamp Slam
    tl.to("#s1-stamp", {{ opacity: 1, scale: 1.0, rotation: -12, duration: 0.25, ease: "power4.out" }}, 0.6);

    // -------------------------------------------------------------
    // SCENE 2: (4.5s - 8.5s) 3D Newspaper Fold & Highlighter Wipe
    // -------------------------------------------------------------
    tl.to("#scene1", {{ autoAlpha: 0, duration: 0.35 }}, 4.5);
    tl.set("#scene2", {{ autoAlpha: 1 }}, 4.5);
    tl.fromTo("#s2-paper",
      {{ y: 300, scale: 0.8, rotateX: 25, opacity: 0 }},
      {{ y: 0, scale: 1.0, rotateX: 10, opacity: 1, duration: 1.0, ease: "power3.out" }}, 4.5);
    tl.to("#s2-marker", {{ scaleX: 1.0, duration: 1.4, ease: "power2.inOut" }}, 5.2);

    // -------------------------------------------------------------
    // SCENE 3: (8.5s - 12.0s) Historical Photo Ken Burns + Evidence Pins
    // -------------------------------------------------------------
    tl.to("#scene2", {{ autoAlpha: 0, duration: 0.35 }}, 8.5);
    tl.set("#scene3", {{ autoAlpha: 1 }}, 8.5);
    tl.fromTo("#s3-img",
      {{ scale: 1.0, x: 0 }},
      {{ scale: 1.3, x: -30, duration: 3.5, ease: "power1.inOut" }}, 8.5);
    tl.to("#s3-tag1", {{ opacity: 1, x: 15, duration: 0.4, ease: "power2.out" }}, 9.0);
    tl.to("#s3-tag2", {{ opacity: 1, x: -15, duration: 0.4, ease: "power2.out" }}, 9.8);

    // -------------------------------------------------------------
    // SCENE 4: (12.0s - 15.0s) Climax Question
    // -------------------------------------------------------------
    tl.to("#scene3", {{ autoAlpha: 0, duration: 0.35 }}, 12.0);
    tl.set("#scene4", {{ autoAlpha: 1 }}, 12.0);
    tl.fromTo(".climax-box",
      {{ scale: 0.85, opacity: 0 }},
      {{ scale: 1.0, opacity: 1, duration: 0.6, ease: "back.out(1.5)" }}, 12.0);

    // -------------------------------------------------------------
    // CAPTION SYNCHRONIZATION
    // -------------------------------------------------------------
    const captions = {pkg['subtitles_json']};
    captions.forEach(c => {{
      tl.call(() => {{
        const el = document.getElementById("capWord");
        if (el) {{
          el.innerText = c.text;
          el.style.transform = "scale(1.15)";
          setTimeout(() => {{ el.style.transform = "scale(1.0)"; }}, 160);
        }}
      }}, null, c.time);
    }});

    window.__timelines["main"] = tl;
  </script>
</body>
</html>
"""
    return html
