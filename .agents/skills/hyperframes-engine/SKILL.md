---
name: hyperframes-engine
description: Agent-native video engine by HeyGen. Uses HTML, CSS, Three.js, GSAP, and WebGL to render Blender/After Effects grade 2D/3D motion graphics directly to 60fps MP4 via Chrome and FFmpeg.
---

# HyperFrames Agent-Native Video Engine

## Core Concept
Instead of rendering slow heavy Blender projects, HyperFrames renders code-based web scenes (HTML, CSS, GSAP, Three.js, WebGL) deterministically into broadcast-quality MP4/WebM.

## CLI Commands
- `npx hyperframes preview`: Starts the live preview studio in the browser.
- `npx hyperframes render -o out.mp4`: Renders the composition frame-by-frame via headless Chrome + FFmpeg.
- `npx hyperframes render --format webm -o out.webm`: Renders transparent alpha overlays.
- `npx hyperframes beats`: Analyzes audio tracks and exports beat timestamps.

## Creative Capabilities (Blender-Grade Without Blender)
1. **Three.js 3D Scenes:** 3D spinning globes, wireframe architectural blueprints, underwater ancient ruins.
2. **GSAP Kinetic Typography:** Words scaling, rotating, and tracking with elastic physics.
3. **Tactical UI / HUDs:** Holographic radar sweeps, military telemetry, latitude/longitude grids.
