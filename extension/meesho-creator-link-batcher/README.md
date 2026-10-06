# Creator Link Batch Helper (Brave / Chrome)

A local browser extension prototype for the current 14 Meesho listings. It reads a selected CSV, uses the **currently open, user-signed-in Creator page**, enters product URLs through its visible form (one-by-one or a visible bulk text/file field), and captures the official links rendered by that page. It never constructs `p_id` or affiliate URLs itself.

## Install

1. Extract `meesho-creator-link-batcher.zip`.
2. In Brave/Chrome open `brave://extensions` or `chrome://extensions`.
3. Enable **Developer mode** → **Load unpacked** → select the extracted `meesho-creator-link-batcher` folder.
4. Sign in to Meesho Creator yourself and open its link-generator page. Set the desired campaign/platform there (for the examples you supplied, Instagram Stories).
5. Open the extension, choose the product CSV, click **Scan page**, select the product URL field and Generate button, then choose the feed mode and click **Run batch**. Keep the extension popup open.
6. Download **Links CSV** after it finishes. It preserves input columns and adds `affiliate_url`, `affiliate_p_id`, and `affiliate_status`. Share that output CSV to have the catalog links replaced in one batch.

## CSV input

The extension auto-detects common URL columns: `product_url`, `item_page_link`, `product_link`, `url`, or `link`. It recognizes `ext_id` or extracts the slug from a Meesho `/p/{slug}` URL. The existing `meesho-creator-bulk-source.csv` has 14 rows and uses `title,ext_id,product_url`.

## Modes

- **Auto**: bulk paste for a textarea; otherwise feed the visible form one product at a time automatically.
- **One-by-one**: repeated use of a single visible URL input and Generate button; no per-product manual work.
- **Bulk text box**: puts all product URLs, one per line, into the selected textarea and submits once.
- **CSV upload**: creates a simple `title,ext_id,product_url` CSV in memory and assigns it to the selected visible file input.

Generated links are accepted as successful only when they contain a numeric `p_id` and the expected `ext_id`. Other responses are retained for review, not presented as verified. The tool adds a small progress banner to the open page. The currently selected campaign is controlled by Meesho Creator, not inferred or fabricated by this extension.

## Important boundaries

- The extension acts only after an explicit click, on the current visible page, in your own signed-in browser session.
- It does not store credentials, call undocumented Meesho endpoints, crawl product pages, evade CAPTCHA, or bypass a confirmation. If a human check or site warning appears, stop and handle it yourself.
- Meesho's page can change. If its visible fields/buttons are not detected, rescan and select them, or share a screenshot of the generator UI (hide account details) so the selectors can be adjusted.
- First test with one product if the Creator screen is unfamiliar. Once confirmed, run the full 14-row CSV.
