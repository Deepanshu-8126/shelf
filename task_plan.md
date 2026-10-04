# Task Plan: Premium 3D Web Experience Across Storefront

## Goal
Transform the customer storefront (`shelf-storefront`) into a visually stunning, spatial 3D shopping experience where every visitor can interact with all products in 3D:
1. Micro-spatial 3D tilt + specular lighting + 360-angle horizontal scrubber on all product cards.
2. Direct colorway swatch switcher on cards.
3. Dedicated "🧊 3D Experience" trigger on every card and in the navigation bar.
4. Immersive 3D Turntable Stage inside `ProductDetailModal` (toggle between 2D Editorial & 3D Interactive Turntable).
5. Enhanced `InteractiveShowroomModal` that loads real product imagery, 3D turntable rotation, studio lighting switcher, and instant checkout.

---

## Phases

### Phase 1: Planning & Architectural Inspection
- [x] Inspect existing 3D components (`ProductCard.jsx`, `ProductDetailModal.jsx`, `InteractiveShowroomModal.jsx`, `Storefront.jsx`).
- [x] Identify blockers (e.g. `if (isPublic) return;` suppressing 3D tilt on public cards, missing 3D triggers).
- [x] Create `findings.md` and `progress.md` tracking files.

### Phase 2: Card-Level 3D Experience (`ProductCard.jsx` & CSS)
- [x] Enable smooth 3D perspective tilt (`rotateX`, `rotateY`, `scale3d`) for public storefront visitors.
- [x] Add dynamic specular reflection glare (`shine-overlay`) that follows cursor coordinates.
- [x] Add 360-degree horizontal angle scrubbing on mouse hover and touch swipe.
- [x] Add interactive color swatch pills directly on the card to switch images & active variant live.
- [x] Add floating "🧊 3D View" badge/button on each card to launch 3D stage with 1 click.

### Phase 3: Product Detail 3D Stage (`ProductDetailModal.jsx`)
- [x] Add a `[2D Editorial | 🧊 3D Spatial Turntable]` view mode switcher in `ProductDetailModal`.
- [x] Integrate a responsive 3D card/mannequin turntable stage with drag-to-orbit 360°, auto-spin, and ambient studio glow.
- [x] Support live variation switching in 3D mode.

### Phase 4: Storefront Navigation & Spatial Showroom Integration (`Storefront.jsx` & `InteractiveShowroomModal.jsx`)
- [x] Wire "🧊 3D Showroom" button in top nav bar, mobile drawer, and hero action strip in `Storefront.jsx`.
- [x] Connect `onOpen3DView(product)` from any product card directly to the 3D showroom with that product pre-selected.
- [x] Enhance `InteractiveShowroomModal` to project real 3D cards/fabrics with lighting presets (Ivory, Sage, Sand, Noir).

### Phase 5: Verification & Quality Craft Validation
- [x] Run production build `npm run build` and ensure 0 errors (525ms).
- [x] Test public card interactions, specular reflections, and modal transitions.
- [x] Update `progress.md` and present complete walkthrough to the user.
