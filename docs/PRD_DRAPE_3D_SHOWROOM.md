# Product Requirement Document (PRD)
## Drape — 3D Architectural Walk-Through Fashion Showroom & Spatial Storefront

---

## 1. Document Information
- **Product Name:** Drape (Spatial 3D Fashion Storefront Engine)
- **Version:** 2.0.0
- **Author:** Principal Systems Architect & Senior Product Lead
- **Status:** Approved for Implementation
- **Target Workspaces:** `D:\SHELF_STORE` & `https://shelf-storefront.vercel.app`

---

## 2. Product Overview & Vision
Modern e-commerce catalogs suffer from flat, generic 2D grid fatigue. **Drape** transforms the traditional apparel catalog into a high-craft 3D architectural fashion walkthrough. Customers do not just scroll a grid—they step into curated spatial environments with atmospheric fog, directional spotlights, ceiling-suspended garments that sway with physics, glowing pedestals, and a dual-perspective Mirror Hall for instant try-on.

### 2.1 Goals
1. **Cinematic First Impression:** Immediate "wow factor" within 1.5s via hardware-accelerated WebGL / Three.js without blocking page interactivity.
2. **Visual Fidelity to High-End References:** Replicate the 5 exact visual archetypes provided in user references (Floating Petal Vortex, Cyberpunk Garage Rack, Minimalist Suspension, Peach Studio Lightbox, and Dual Reflection Mirror).
3. **Seamless 3-Layer Design Tokenizer:** Enforce strict CSS variable inheritance across all UI panels, floating pills, and 3D lighting states.
4. **Zero Silent Breakages:** Flawless fallback to 2D responsive grid for lower-spec mobile devices or browsers without WebGL.

### 2.2 Non-Goals (v1)
- Multi-vendor marketplace onboarding.
- Complex physics cloth-tearing simulations.
- Phone webcam AR body tracking (handled via procedural 3D mannequin scaling).

---

## 3. Design System & 3-Layer Tokenizer

```
Layer 1: Primitive Tokens (Raw Colors, Radii, Shadows)
       ↓
Layer 2: Semantic Tokens (Surface, Ink, Canvas, Accents)
       ↓
Layer 3: Component Tokens (Pill Buttons, Floating Cards, 3D Fog, Pedestals)
```

### 3.1 Token Definitions
| Token Name | Token Layer | Value | Purpose |
|---|---|---|---|
| `--color-peach-studio` | Primitive | `#FCEFED` | Warm studio background & volumetric fog |
| `--color-dark-slate` | Primitive | `#14151B` | Techwear & cyberpunk showroom canvas |
| `--color-concrete` | Primitive | `#9AA0A6` | Spotlight architectural gallery floor |
| `--ink-primary` | Semantic | `#111111` | Primary typography, headers, active pills |
| `--ink-muted` | Semantic | `#6B7380` | Breadcrumbs, secondary labels, prices |
| `--accent-blue` | Semantic | `#2F6BFF` | Active category pills, cursor ring expansion, mirror frame |
| `--glow-pedestal` | Component | `#FF7043` | Acrylic lightbox emissive underglow |
| `--radius-pill` | Component | `9999px` | Buttons, category chips, breadcrumbs |
| `--radius-card` | Component | `20px` | Floating bottom product card carousel |
| `--radius-panel` | Component | `24px` | Product focus sheet & modal drawers |

---

## 4. 3D Architectural Showroom Archetypes

```
┌────────────────────────────────────────────────────────────────────────┐
│                        DRAPE 3D SPATIAL ENGINE                         │
├──────────────────┬──────────────────┬──────────────────┬───────────────┤
│ 1. Peach Studio  │ 2. Petal Vortex  │ 3. Cyber Garage  │ 4. Mirror Hall│
│  - Warm Fog      │  - Cone Spot     │  - Rolling Rack  │  - Blue Frame │
│  - Glowing Base  │  - Floating Rose │  - Neon Strips   │  - Back Refl. │
│  - Ceiling Chain │  - Dark Concrete │  - Wet Asphalt   │  - Body Scaler│
└──────────────────┴──────────────────┴──────────────────┴───────────────┘
```

### 4.1 Archetype 1: Warm Peach Studio & Glowing Lightbox Pedestal
- **Reference:** Editorial studio with warm rose-peach horizon.
- **Lighting:** Ambient light `#FFE6E2` (0.8), Key Directional `#FFF9F7` (1.5) with soft shadow mapping.
- **Pedestal:** Frosted acrylic box (`#FFA07A`, emissive `#FF7043`, intensity 2.8) with internal point light casting warm upwards glow on the garment.
- **Suspension:** Aircraft micro-wire drop and dark metal hanger bar.

### 4.2 Archetype 2: Floating Rose Petal Vortex (Signature Piece)
- **Reference:** White hoodie suspended in mid-air surrounded by orbiting rose petals (*"ENGINEERED FOR PRESENCE DESIGNED FOR PEACE"*).
- **Lighting:** Focused overhead cone spotlight (`angle: Math.PI / 6`, `penumbra: 0.4`, `intensity: 3.2`), dark moody ambient.
- **Floor:** Polished dark architectural concrete with specular contact reflections.
- **Particle System:** 80 procedural pink rose petals drifting in a parametric Archimedean spiral with subtle turbulence.

### 4.3 Archetype 3: Cyberpunk Garage & Rolling Industrial Rack
- **Reference:** Underground garage showroom with rolling caster rack and neon tubes (*"DESIGN FOR SALE"*).
- **Fixtures:** Heavy-duty matte black and chrome pipe rack on 4 caster wheels.
- **Lighting:** Dual neon horizontal strip tubes (Electric Cyan `#00E5FF` & Cyber Magenta `#FF0055`).
- **Floor:** Wet asphalt / dark mirror plane (`roughness: 0.12, metalness: 0.8`).

### 4.4 Archetype 4: Minimalist Rail & Techwear Suspension
- **Reference:** High-end Scandinavian/Japanese editorial photography (NABR Studios / MKI MIYUKI ZOKU).
- **Fixtures:** Clean matte black horizontal suspension rod, garments hung with natural shoulder drop.
- **Environment:** Seamless infinite cyclorama with ultra-soft diffused contact shadows.

### 4.5 Archetype 5: Dual Mirror Hall (Virtual Try-On)
- **Reference:** Tall electric blue frame (`#2F6BFF`), front mannequin on podium.
- **Optics:** Real-time inverted duplicate behind glass (`rotation_back = Math.PI - rotation_front`).
- **Body Shapes:** Slim (0.88x width), Regular (1.0x width), Broad (1.15x width).

---

## 5. UI Layout & Component Blueprints

### 5.1 Minimalist Header
- Fixed 56px topbar.
- Left: Brand wordmark `"drape."` with circular 40px back button.
- Center: Floating breadcrumb pill (`bg-white/80`, `backdrop-blur-md`).
- Right: Black pill button for Bag / Cart (`#111111`, text `#FFFFFF`, radius `9999px`, hover `#2F6BFF`).

### 5.2 Floating Bottom Card Carousel
- Position: Fixed `bottom: 96px`, horizontal drag/swipe.
- Card geometry: Min-width `190px`, background `#FFFFFF`, radius `20px`, padding `16px`.
- Card content: Color swatch dot (14px circle), product title, price tag (`₹`). Hover triggers blue border transition.

### 5.3 Category Switcher (Footer Pills)
- Position: Fixed `bottom: 24px`, center aligned.
- Container: Rounded pill container with `backdrop-blur-md`, `bg-white/85`.
- Items: `Warm Peach`, `Petal Vortex`, `Cyber Garage`, `Minimalist Rail`, `Mirror Hall`.

### 5.4 Custom Cursor
- Center dot: 8px solid `#111111`.
- Outer ring: 30px ring, 1px border.
- Hover state: Expands smoothly to 54px, switches to `#2F6BFF` with translucent blue fill.
- Automatically disabled on touch / mobile devices.

---

## 6. Functional Acceptance Criteria (Given / When / Then)

### Scenario 1: Switching Showroom Archetypes
- **Given** the customer is inside the Drape 3D Showroom,
- **When** they click "Petal Vortex" in the footer pills,
- **Then** the canvas smoothly transitions to the dark concrete gallery with the overhead cone spotlight and 80 orbiting rose petals within 200ms.

### Scenario 2: Selecting Body Shape in Mirror Hall
- **Given** the customer has navigated to the Mirror Hall,
- **When** they tap the "Broad" body shape chip,
- **Then** both front and back reflected mannequins smoothly scale horizontally to 1.15x without texture distortion.

### Scenario 3: Swatch Recoloring
- **Given** an apparel piece is focused in 3D,
- **When** the customer clicks a color swatch dot,
- **Then** the procedural 3D garment mesh lerps its material color to the target hex code in under 150ms.

---

## 7. Performance & Quality Benchmarks
- **Frame Rate:** Constant 60 FPS on desktop; minimum 45 FPS on mid-tier mobile.
- **Pixel Ratio:** Capped at `Math.min(window.devicePixelRatio, 1.8)` to prevent GPU throttling.
- **Resource Cleanup:** All Three.js geometries, materials, and textures cleanly disposed upon unmount (`renderer.dispose()`).
