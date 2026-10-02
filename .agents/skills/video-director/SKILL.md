---
name: video-director
description: Master agentic video director inspired by OpenMontage and HyperFrames. Orchestrates story hooks, scene pacing, safe zones, visual changes every 1-3s, and zero-copyright audio mixing.
---

# Video Director & Cinema Architecture (OpenMontage + HyperFrames Standard)

## 1. Pacing & Safe Zones (1080x1920 Vertical & 1920x1080 Horizontal)
- **Universal Safe Zone (9:16):** 900x1400px centered.
  - Top Dead Zone: 120px
  - Bottom Dead Zone: 300px (Reserved for Shorts/Reels titles, buttons, engagement UI).
  - All critical subtitles, key quotes, and badges must remain above `y = 1620px`.
- **Pacing Standard:** Visual change every **1.5 to 3.0 seconds**. Never allow a static frame to stay on screen for > 3.5s.

## 2. Pacing Sequence (60s Viral Short / Mini-Doc)
1. **The Pattern Interrupt Hook (0.0s - 3.0s):**
   - High-contrast visual: 3D Tactical Radar sweep, high-stakes question, or sudden declassified stamp.
2. **The Archival Evidence Reveal (3.0s - 8.0s):**
   - Animated Vox-style Newspaper / FBI Dossier Highlighter sweep with felt-tip marker friction SFX.
3. **The Escalation & 2.5D Ken Burns Drift (8.0s - 25.0s):**
   - Real historical public-domain photos with cosine zoom and dark vignette.
4. **The Unsolved Mystery / Cliffhanger (25.0s - end):**
   - High-tension sub-bass drone swell + open loop ending.

## 3. Motion Principles (12 Disney Principles Adapted for Code)
- **Ease Curves:** Always use `cubic-bezier(0.65, 0, 0.35, 1)` or cosine smoothing. Never linear.
- **Anticipation & Overshoot:** Scale elements 10-15% past target, settling back in 4 frames.
- **Staging:** Animate one element at a time; stagger captions and badge reveals by 4-6 frames.
