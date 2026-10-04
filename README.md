# shelf. Studio — affiliate curation dashboard

A responsive React + Vite public affiliate storefront and private creator studio. Three.js powers the subtle orbit sculpture in the studio hero. The public storefront is no-login; owner edits and Python imports use the FastAPI service plus a shared SQLite catalog.

## Run locally

```bash
npm install
python3 -m pip install -r requirements.txt
cp .env.example .env
# Edit .env: set a strong OWNER_PASSWORD and random SESSION_SECRET.
```

Start the Python API in one terminal, then Vite in another:

```bash
npm run api:dev
npm run dev
```

The Vite server proxies same-origin `/api` requests to FastAPI; browser code does not call localhost directly. Open the site root for the private studio. The no-login shopper page is available at `/?view=storefront` or through **View storefront**.

## What’s inside

- A no-login public shopping page plus a creator dashboard. Production owner writes require a signed session; an explicit `SHELF_OWNER_AUTH_BYPASS=1` switch is available only for a private sandbox preview and must never be enabled on a public deployment. FastAPI serves shared product, collection, and profile data from SQLite.
- Search, marketplace filters for Amazon, Flipkart, Myntra, and Meesho, category and collection filters, sorting, pagination, and interactive product cards.
- Separate **Tops & Tunics**, **Kurtis**, **Ethnic Wear**, **Women Dresses**, **Bottomwear**, and **Innerwear** filters, plus the Winter edit and other lifestyle categories. The paste importer adds searchable subcategory tags such as Full sleeves, Bodycon, Skirts, Palazzos, Bras, and Panties.
- Pinterest-inspired cards with hover tilt, save hearts, listing badges, product-rating chips, and collection hover states.
- **87 unique Meesho listings** across the app and CSV: 18 earlier topwear picks, 8 original listings, the `i0yzat` side-dori listing, 45 supplied recommendation IDs, and 15 curated Women’s Dresses. The full dynamic 1,000+ search catalog is not imported.
- The 15 dress cards are keyed to unique Meesho product IDs: `hhck2a`, `i45j67`, `ae6lv9`, `hpi4lz`, `ibsnwj`, `i3vfc3`, `i96qm1`, `boevl2`, `bg1m56`, `92vpfo`, `b38f6j`, `59w9ha`, `hpi12q`, `gpc4vn`, and `c4jdu0`. Each listing appears once; different product IDs remain separate.
- Only verified product-page rating/review data is shown. Seller/shop scores are omitted. The corrected `hgyhrb` record keeps the confirmed **Vani Arts** brand and **4.3 / 266 product ratings**.
- Meesho product thumbnails are stored locally under `public/images/`; asset sources and the October 3, 2026 snapshot policy are documented in `public/images/ASSET_SOURCES.md`.

The yellow “Stylish Ravishing” snapshot (₹438, 4.2 / 9,707) did not include a matching product ID. It is intentionally not substituted with `hpi4lz`: that ID is a separate maroon listing, observed at ₹433 with a 3.7 / 72 product rating. The linked maroon product is listed as its own pick.

## Private creator studio and public shop

The production studio root asks for the single owner passphrase configured as `OWNER_PASSWORD`. The shopper page is public at `/?view=storefront`; shoppers do not create accounts and see no studio navigation. Product-specific affiliate destinations are required on the public page—untracked marketplace searches are not used as shop buttons.

SQLite at `data/catalog.sqlite3` is the shared catalog for this single API instance. Keep the database and `public/images/` on persistent storage when hosting. Set a long random `SESSION_SECRET`; use `COOKIE_SECURE=1` behind HTTPS. Only for a private sandbox preview, `SHELF_OWNER_AUTH_BYPASS=1` opens the studio without a passphrase; unset it before any public deployment. This SQLite MVP is for one API instance; use a proper shared PostgreSQL deployment before horizontal scaling.

## Fast paste importer

The dashboard’s **Import listings** tab calls the Python API for preview and publishing. It classifies, tags, de-duplicates by Meesho product ID, and generates the supplied `af_invite` route. It does not require adding each card separately to the page.

For a Web Scraper CSV export, normalize it for the dashboard with:

```bash
MEESHO_AFFILIATE_ID=374453404 python3 scripts/prepare_meesho_web_scraper_csv.py raw-export.csv shelf-ready.csv
```

This uses the exact `item_page_link` for each listing, keeps its product-detail gallery, removes duplicate image paths/resolution variants, ignores recommendation-image lists, assigns categories/tags, and generates the creator route. Paste `shelf-ready.csv` into **Import listings** and review it before publishing. The script only transforms the CSV you provide; it does not crawl Meesho. A generated redirect is not proof of commission attribution—verify in Meesho Creator.

For a batch pasted into the terminal instead:

```bash
python3 scripts/import_meesho_paste.py
# or: npm run import:meesho
```

Paste copied listing text into the terminal and finish with Ctrl+D (Linux/macOS) or Ctrl+Z then Enter (Windows). It extracts prices, ratings, titles, categories, subcategory tags, and—when a single product-detail page is pasted—visible color, fabric, fit, length, sizes, seller, and rating/review counts into `scripts/meesho-paste-review.csv`. On a detail page it reads the main listing and ignores the “People also viewed” section. It does not change the catalog unless run with `--apply`.

Copied product-detail text is valid review input even when it omits product IDs, URLs, and images; such rows remain drafts. A title and price alone cannot identify the exact listing or produce a product-specific affiliate route. If the copied page omits those fields, provide `--links-file` with the exact product URL in the same order; for **new** listings also provide `--images-file` with the real product-image URL from `images.meesho.com`. Existing catalog IDs can update price/category without a new image. The importer never scrapes protected pages or guesses an ID from a generic title.

Example with a saved paste file:

```bash
python3 scripts/import_meesho_paste.py --input copied-page.txt --links-file product-links.txt --images-file product-images.txt --apply
```

## Automatic discovery boundary

The dashboard batch importer runs the Python parser after a paste/export is supplied; it is not a scheduled live crawler. The project has no authorized Meesho product feed/API connected. Direct Meesho page requests returned 403, so the importer will not scrape or bypass those protections. If the supplied text/feed includes image URLs, the API can fetch valid Meesho product images automatically; missing product IDs or images are held for review rather than guessed. An approved CSV/feed may include `gallery_image_urls` as extra `images.meesho.com/images/products/` URLs separated by `|` (up to 8 per listing; keep the primary image in `image_url`). Public product cards auto-advance through genuine supplied gallery images every 3 seconds, with manual arrows/dots and touch swipe. Google Trends/Pinterest may guide trend keywords, but they do not provide the actual retailer product ID, current price, image, or affiliate route.

For hands-off scheduled discovery, connect an authorized marketplace/affiliate product feed or API. The affiliate route is created automatically after the exact Meesho product ID is known.

## Meesho price sync — CSV/feed required

The affiliate URL does not reliably expose the current listing price. The Python workflow **does not scrape Meesho or bypass site protections**. Prices refresh only when supplied current listing data is available from an approved export/feed or another trusted CSV.

1. Copy `scripts/meesho-price-updates.template.csv` to `scripts/meesho-price-updates.csv`.
2. Add one row per listing. `product_url` (or `ext_id`) and `price` are required for an existing product. `old_price` is optional; leave it blank to keep the current old-price value, or set `clear_old_price=true` to clear it. `price_checked_at` can be supplied, otherwise the India-local date is used.
3. Run `npm run sync:meesho`, or deploy with `npm run build` (which runs the Python sync as a `prebuild` step).

The sync upserts by Meesho product ID, removes duplicate IDs, updates the imported JSON and CSV, refreshes the app’s price overrides for existing Meesho seed products, and regenerates `scripts/meesho-products-with-links.csv`. To add a new product, include `product_url`, `price`, `title`, `category`, and `image` as an **existing local path** such as `/images/new-pick.webp`.

If the update CSV is missing, the sync leaves prices unchanged, reports that no feed was supplied, and still checks catalog duplicates/rebuilds the link export. A build therefore does **not** mean prices were fetched live. Python 3 must be available in the build environment.

## Meesho links and attribution

Product cards build the `af_invite/{creator}:youtube_long_form:12492338?ext_id=...` route using the creator ID `374453404`, following the supplied Python pattern. The route generator preserves an existing creator URL supplied in `affiliate_url`. A successful redirect is not proof of commission attribution or account ownership; confirm tracked orders in Meesho Creator.

The Python generator and app default to the source/campaign in the invite URL you supplied: `youtube_long_form:12492338`. If Meesho assigned different values, configure `MEESHO_SOURCE` and `MEESHO_CAMPAIGN_ID` for Python, and `VITE_MEESHO_SOURCE` and `VITE_MEESHO_CAMPAIGN_ID` for the app. The affiliate ID can be overridden with `MEESHO_AFFILIATE_ID` / `VITE_MEESHO_AFFILIATE_ID`.

Batch route generation without a price update:

```bash
python3 scripts/generate_meesho_affiliate_links.py scripts/meesho-products.csv
```

This writes `scripts/meesho-products-with-links.csv`; it builds routes from supplied product URLs and cannot certify tracking. Meesho price, availability, ratings, and images can change after the captured **2026-10-03** snapshot.
