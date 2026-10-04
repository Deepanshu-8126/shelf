# Meesho Page CSV Exporter

A small Brave/Chrome extension that exports one **currently open Meesho product page** to a CSV row. It reads the page DOM only after you click the extension; it does not visit other pages, call Meesho endpoints, crawl in the background, or bypass page protections.

## Install in Brave

1. Download and extract `meesho-page-csv-exporter.zip`.
2. In Brave, open `brave://extensions`.
3. Turn on **Developer mode**.
4. Click **Load unpacked** and select the extracted `meesho-page-csv-exporter` folder (the one containing `manifest.json`).
5. Open a Meesho product detail page. Let the main product gallery load; scroll the gallery if needed so its image URLs are present in the page.
6. Click the extension icon, then **Extract this page**.
7. Review the CSV preview, then click **Copy CSV** or **Download CSV**.

## Use the CSV in shelf. Studio

Open the CSV in a text editor and copy its contents, or click **Copy CSV**. In the Studio, choose **Import listings**, paste the CSV into the main box, and click **Analyse with Python**. The importer recognizes `product_url`, `ext_id`, `image_url`, `gallery_image_urls`, price, rating, category, and the optional detail fields. It will generate the Meesho affiliate route only when the exact product ID/URL is present.

## Limits

- It exports one active product page per click; it does not crawl recommendations or many products.
- It reads image URLs already in the page DOM. It cannot recover images the page has not loaded or expose data blocked by Meesho.
- Images are filtered to Meesho product-image URLs and are limited to the main page area before customer photos/recommendations when that section marker is found. Review the CSV to remove any unrelated candidates.
- This extension does not produce or guess IDs, prices, images, or affiliate routes. Missing fields remain blank and should stay in review.
- Use only where your account/site terms permit this export.
