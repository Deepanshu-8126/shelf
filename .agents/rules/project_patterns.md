# Project Conventions & Learned Behaviors

## 1. Automatic Real Image Engine
- **No Hardcoded Image URLs**: Never hardcode static Unsplash or dummy photo URLs in data files or components.
- **Dynamic Retrieval**: Always use `getRealImage(keyword, niche)` or `<SmartImage keyword={item.name} niche={niche} />`.
- **API Pipeline**: Free Openverse API (600M+ CC photos) with optional RAWG fallback for gaming.
- **Edge CDN**: Format all images through `images.weserv.nl/?url=...&w=800&fit=cover&q=80&output=webp` for instant edge caching and WebP optimization.
- **7-Day Browser Caching**: `localStorage` cached with 7-day TTL (`ud_img_v1_`).
- **Zero Dummy Stock Policy**: If an image returns `null`, render a clean text-first UI with Lucide icons—never show a generic/irrelevant keyboard or stock filler.

## 2. White UI Design System Lock
- **Theme**: Pure White `#FFFFFF` and light off-white `#F8FAFC`.
- **Typography**: `Inter, sans-serif` with high-contrast `#1A2027` text.
- **Cards**: `bg-white border border-[#E5E7EB] rounded-2xl p-5 shadow-xs`.
- **Headings & Prices**: Headings `#111827` bold, price metrics `#B45309` 28px bold.
- **Icons**: Exclusively official SVG `lucide-react` icons (no raw emojis or broken `<img>` boxes).

## 3. Windows Path Execution
- Path contains a semicolon (`d:\affi;ate`). Always run Vite commands directly via `node node_modules/vite/bin/vite.js [command]`.

## 4. Fashion Studio & Media Pipeline Invariants (Zero-Block & Zero-Watermark)
- **Zero Pollinations / Zero Watermark**: Strictly prohibited from using `pollinations.ai` or generating synthetic watermarked media. All fashion images must be clean, commercial-ready 4K photography.
- **Cloud & Mobile-First Execution**: When deployed to Vercel/Render or accessed via mobile, media generation must route via direct cloud REST APIs (`POST /api/studio/generate-photo`), never relying on local desktop GUI browser windows.
- **Multimodal Reference Garment Ingestion**: The studio engine must anchor to reference garment photos (URL/base64) using Gemini Vision (`gemini-2.5-flash`) to preserve neckline, embroidery, fabric drape, and silhouette.
- **8K Natural Optical Super-Sampling**: Portra 400 skin calibration + organic micro-grain (preserving authentic skin pores, zero plastic AI look, zero digital crunch).
