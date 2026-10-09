# Product Requirements Document (PRD) for SHEF

## 1. Brand Identity
SHEF is a premium fashion reseller and affiliate platform that combines the ultra-minimal, luxurious aesthetic of high-end brands like Zara with the affiliate/reseller mechanics of Meesho and Wishlink. The brand embodies an "Antigravity" UI ethos—airy, floating, fluffy, and extremely premium—avoiding the cluttered look of typical Indian e-commerce sites. The target audience is fashion-conscious urban Indians aged 18-35 who seek curated, high-quality fashion discoveries with seamless earning opportunities.

## 2. Core Modules
### Storefront
- Primary consumer-facing shopping experience
- Features hero banners, category grids, and trending product carousels
- Minimalist product cards with antigravity effects (glassmorphism, soft shadows, subtle hover lifts)
- Seamless navigation to product detail pages (built as Astro islands if interactivity needed)

### Affiliate Hub (Wishlink/Meesho Style)
- Reseller/dashboard for earning commissions
- Displays total earnings, withdrawal options, and product catalog with commission visibility
- Each product card shows "Your Commission: ₹XXX" and action buttons for copying/sharing affiliate links
- Category filters for Flipkart, Myntra, Zara, etc.

### Admin Dashboard
- Backend for platform management
- Sidebar navigation (Dashboard, Products, Orders, Affiliates)
- Top stats cards (Revenue, Orders, Active Affiliates, Payouts) using antigravity card design
- Revenue line chart placeholder
- Recent orders table with status badges

## 3. Target Audience
- Primary: Urban Indian youth (18-35) interested in fashion and side-income opportunities
- Secondary: Fashion influencers, micro-entrepreneurs, and affiliate marketers
- Tertiary: Budget-conscious shoppers seeking premium aesthetics at accessible prices

## 4. Tech Stack
- **Framework:** Astro (static site builder with zero-JS by default, interactive islands only where necessary)
- **Styling:** Tailwind CSS (via CDN for prototype, with custom config for antigravity design system)
- **Typography:** 
  - Headings/Logo: Playfair Display (Google Fonts)
  - Body/UI: Inter (Google Fonts)
- **Images:** High-quality Unsplash fashion placeholders
- **Additional:** 
  - Google Fonts CDN for typography
  - Tailwind CSS CDN for styling (to be replaced with PostCSS/Tailwind in production)
  - Semantic HTML5, accessible ARIA labels, mobile-first responsive design

## 5. Design System: "Antigravity"
- **Vibe:** Minimalist, luxurious, airy, high whitespace, glassmorphism
- **Color Palette:**
  - Background: `#FAFAF9` (Stone-50 / Off-white)
  - Text: `#0C0A09` (Stone-950 / Soft Black)
  - Accents: `#B49B67` (Muted Premium Gold) & `#A8A29E` (Stone-400)
- **UI Effects:**
  - Cards: `bg-white/80 backdrop-blur-md border border-stone-100`
  - Shadows: Soft, diffused shadows (`0 20px 40px -10px rgba(0, 0, 0, 0.05)`)
  - Interactions: Subtle hover lifts (`hover:-translate-y-1`), smooth 300ms transitions
  - Borders: 1px hairline borders, no heavy outlines
- **Typography Scale:** Fluid and responsive based on REM units

## 6. Success Metrics
- User engagement: Average session duration > 3 minutes
- Conversion rate: Storefront to affiliate sign-up > 15%
- Affiliate activation: > 30% of sign-ups share at least one link
- Performance: Lighthouse score > 90 for performance, accessibility, and best practices