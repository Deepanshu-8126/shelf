# Drape — Comprehensive Design Specification (`DESIGN.md`)

## 1. Brand & Design System Identity
- **Name:** Drape — 3D Walk-through Spatial Fashion Store
- **Aesthetic:** Editorial high-fashion, minimal brutalist spatial layouts, seamless cycloramas, tactile floating glassmorphic pills.
- **Copy Standard:** Strictly sentence case (never all-caps headers or buttons).

---

## 2. Global Design Tokens (3-Layer Architecture)

### Layer 1: Primitive Tokens
```css
/* Primitives */
--color-white: #FFFFFF;
--color-black-100: #111111;
--color-grey-500: #6B7380;
--color-grey-300: #C9CED8;
--color-peach-100: #FCEFED;
--color-peach-200: #FFA07A;
--color-peach-glow: #FF7043;
--color-blue-500: #2F6BFF;
--color-slate-900: #14151B;
--color-concrete-400: #9AA0A6;
```

### Layer 2: Semantic Tokens
```css
/* Semantic Surfaces & Ink */
--surface-card: var(--color-white);
--surface-glass: rgba(255, 255, 255, 0.88);
--canvas-peach-studio: var(--color-peach-100);
--canvas-dark-slate: var(--color-slate-900);
--canvas-gallery-concrete: var(--color-concrete-400);

--ink-primary: var(--color-black-100);
--ink-muted: var(--color-grey-500);
--ink-disabled: #9CA3AF;

--accent-blue: var(--color-blue-500);
--border-subtle: rgba(201, 206, 216, 0.45);
--glow-pedestal: var(--color-peach-glow);
```

### Layer 3: Component Tokens
```css
/* Geometry & Elevation */
--radius-pill: 9999px;
--radius-card: 20px;
--radius-panel: 24px;
--radius-swatch: 50%;

--shadow-subtle: 0 2px 8px rgba(0, 0, 0, 0.04);
--shadow-floating: 0 12px 32px -4px rgba(17, 17, 17, 0.12), 0 4px 12px rgba(17, 17, 17, 0.06);
--shadow-glow-pedestal: 0 0 32px rgba(255, 112, 67, 0.45);
--shadow-glow-blue: 0 0 24px rgba(47, 107, 255, 0.35);

/* Typography */
--font-brand: 'Bricolage Grotesque', 'Plus Jakarta Sans', sans-serif;
```

---

## 3. 3D Display & Mannequin Archetypes (Visual Reference Mappings)

### Archetype 1: Floating Petal Vortex (Signature Piece)
- **Reference:** Floating hoodie surrounded by orbiting rose petals (`ENGINEERED FOR PRESENCE DESIGNED FOR PEACE`).
- **Lighting:** Focused overhead cone spotlight (`intensity: 2.8, angle: Math.PI / 6`), dark concrete floor with specular contact reflection.
- **Particle System:** 80 procedural pink petal instances swirling in a parametric spiral path.

### Archetype 2: Cyberpunk Garage & Rolling Pipe Rack
- **Reference:** Industrial rolling pipe racks with 4 caster wheels, floating purple streetwear, neon strip LEDs (`DESIGN FOR SALE`).
- **Floor:** Polished wet asphalt / dark mirror plane (`roughness: 0.12, metalness: 0.8`).
- **Lighting:** Dual neon horizontal strip tubes (electric cyan & purple).

### Archetype 3: Minimalist Ceiling Suspension & Techwear
- **Reference:** Dual aircraft micro-wires dropping straight from ceiling, black wire hangers, neutral cyclorama studio.
- **Mannequin Posture:** Faceless matte dark slate mannequin wearing balaclava / cowl hood techwear.

### Archetype 4: Warm Peach Studio & Glowing Lightbox Pedestal
- **Reference:** Soft studio fog `#FCEFED`, floor roughness `0.22`, acrylic glowing pedestal with warm peach internal point light (`#FF7043`).

### Archetype 5: Dual Mirror Hall (Virtual Try-On)
- **Reference:** Tall electric blue framed mirror (`#2F6BFF`), front mannequin on podium, inverted 180° back reflection behind glass (`θ_ref = π - θ`).
- **Controls:** Body shape selector chips: `Slim` (0.88x), `Regular` (1.0x), `Broad` (1.15x).

---

## 4. UI Layout Hierarchy

### A. Minimalist Topbar
- 56px fixed header with circular back button, breadcrumb pill (`bg-white/70, backdrop-blur-md`), and black pill Cart trigger.

### B. Floating Bottom Card Carousel
- Position: Fixed `bottom: 96px`, horizontal scroll, min-width `190px`, 20px radius cards, color swatch dot, title, price.

### C. Category Switcher (Footer Pills)
- Position: Fixed `bottom: 24px`, center aligned, rounded pill container with `backdrop-blur-md`, active button ink black, inactive transparent with blue hover.

### D. Product Focus & Custom Cursor
- Custom 8px ink dot + 30px ring cursor (desktop only).
- Expanding 54px ring with electric blue accent on clickable targets.
