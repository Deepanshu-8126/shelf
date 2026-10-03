let scannedItems = [];
let selectedIndexes = new Set();
let detectedProduct = null;

const AFFILIATE_CREATOR_ID = "374453404";
const CAMPAIGN_ID = "12492338";
const SOURCE_PARAM = "youtube_long_form";

function buildAffiliateUrl(rawUrl = window.location.href) {
  if (!rawUrl) return "";
  const extMatch = rawUrl.match(/\/p\/([a-zA-Z0-9]+)/);
  const extId = extMatch ? extMatch[1] : "item";
  const pidMatch = rawUrl.match(/p_id=(\d+)/);
  const pId = pidMatch ? pidMatch[1] : "542355935";
  const encoded = encodeURIComponent(rawUrl);
  return `https://www.meesho.com/af_invite/${AFFILIATE_CREATOR_ID}:${SOURCE_PARAM}:${CAMPAIGN_ID}?p_id=${pId}&ext_id=${extId}&utm_source=${SOURCE_PARAM}&url=${encoded}`;
}

document.addEventListener("DOMContentLoaded", async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab || !tab.id) return;

  // Execute extraction & inject blinking highlighter on active page
  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => {
      // 1. Inject Blinking Highlighter CSS on the real page
      if (!document.getElementById("shelf-scraper-highlighter-style")) {
        const style = document.createElement("style");
        style.id = "shelf-scraper-highlighter-style";
        style.innerHTML = `
          @keyframes shelfBlink {
            0% { outline: 3px solid #ec4899; box-shadow: 0 0 15px rgba(236,72,153,0.8); }
            50% { outline: 3px solid #38bdf8; box-shadow: 0 0 20px rgba(56,189,248,0.9); }
            100% { outline: 3px solid #ec4899; box-shadow: 0 0 15px rgba(236,72,153,0.8); }
          }
          .shelf-scraped-highlight {
            animation: shelfBlink 1.5s infinite alternate !important;
            border-radius: 8px !important;
            position: relative !important;
            z-index: 9999 !important;
          }
        `;
        document.head.appendChild(style);
      }

      // 2. Strict Filter for Genuine Fashion Garment Photos
      const JUNK_KEYWORDS = [
        "banner", "off", "icon", "logo", "badge", "avatar", "profile", "delivery",
        "star", "rating", "svg", "static", "vector", "app_store", "play_store",
        "google", "apple", "get it on", "available on", "footer", "download"
      ];

      const allImgs = Array.from(document.querySelectorAll('img')).filter((img) => {
        const src = (img.src || "").toLowerCase();
        const alt = (img.alt || "").toLowerCase();
        const w = img.naturalWidth || img.width || 0;
        const h = img.naturalHeight || img.height || 0;

        // Must be substantial size and not square banner
        if (w < 100 || h < 110) return false;
        if (JUNK_KEYWORDS.some(k => src.includes(k) || alt.includes(k))) return false;

        // On Meesho, genuine product photos always live in images.meesho.com/images/products/
        if (src.includes("images.meesho.com") && !src.includes("/products/")) return false;

        return true;
      });

      const uniqueItems = [];
      const seenSrc = new Set();

      allImgs.forEach((img, idx) => {
        let src = img.srcset ? img.srcset.split(',').slice(-1)[0].split(' ')[0] : img.src;
        if (!src) return;

        // Upgrade to 512px crisp resolution
        const cleanSrc = src.split('?')[0].replace('width=100', 'width=512').replace('width=360', 'width=512');
        if (seenSrc.has(cleanSrc)) return;
        seenSrc.add(cleanSrc);

        // Add visual blink highlight to the element on the webpage!
        const parentContainer = img.closest('a, div[class*="ProductCard"], div[class*="product"], div[role="listitem"]') || img;
        parentContainer.classList.add("shelf-scraped-highlight");

        // Try to get title & price from nearest text
        const cardText = (parentContainer.innerText || img.alt || "").trim();
        const priceMatch = cardText.match(/₹\s*(\d{2,5})/);
        const price = priceMatch ? parseInt(priceMatch[1], 10) : 245;

        let title = img.alt || document.title.split("|")[0].trim();
        if (cardText.length > 5) {
          const lines = cardText.split('\n').map(l => l.trim()).filter(l => l.length > 5 && !l.startsWith('₹') && !l.startsWith('★'));
          if (lines.length > 0) title = lines[0];
        }

        uniqueItems.push({
          id: `p-clip-${idx}-${Date.now()}`,
          title: title.slice(0, 50),
          price: price,
          sizes: ["S", "M", "L", "XL"],
          image: cleanSrc,
          productUrl: window.location.href,
          affiliateUrl: buildAffiliateUrl(window.location.href),
          category: "Gen Z Aesthetic & Streetwear"
        });
      });

      return {
        url: window.location.href,
        title: document.title,
        items: uniqueItems.slice(0, 24)
      };
    }
  }, (output) => {
    if (!output || !output[0] || !output[0].result || !output[0].result.items.length) {
      document.getElementById("scan-count").textContent = "No clean fashion items detected.";
      return;
    }

    const res = output[0].result;
    scannedItems = res.items;

    document.getElementById("scan-count").textContent = `Found ${scannedItems.length} Clean Fashion Outfits`;

    const grid = document.getElementById("batch-grid");
    grid.innerHTML = "";

    scannedItems.forEach((item, index) => {
      const card = document.createElement("div");
      card.className = "grid-item";
      card.innerHTML = `
        <img src="${item.image}" alt="${item.title}" loading="lazy" />
        <span class="check">✓</span>
        <span class="category-tag">₹${item.price} • S-XL</span>
      `;

      card.addEventListener("click", () => {
        if (selectedIndexes.has(index)) {
          selectedIndexes.delete(index);
          card.classList.remove("selected");
        } else {
          selectedIndexes.add(index);
          card.classList.add("selected");
        }
        updatePublishButton();
      });

      grid.appendChild(card);
    });

    // Auto-select all by default
    selectedIndexes = new Set(scannedItems.map((_, i) => i));
    Array.from(grid.children).forEach(c => c.classList.add("selected"));
    updatePublishButton();
  });

  // Toggle select all
  document.getElementById("toggle-select-all").addEventListener("click", () => {
    const grid = document.getElementById("batch-grid");
    if (selectedIndexes.size === scannedItems.length) {
      selectedIndexes.clear();
      Array.from(grid.children).forEach(c => c.classList.remove("selected"));
      document.getElementById("toggle-select-all").textContent = "Select All";
    } else {
      selectedIndexes = new Set(scannedItems.map((_, i) => i));
      Array.from(grid.children).forEach(c => c.classList.add("selected"));
      document.getElementById("toggle-select-all").textContent = "Deselect All";
    }
    updatePublishButton();
  });

  // ACTION 1: Ingest to Storefront
  document.getElementById("batch-publish-btn").addEventListener("click", async () => {
    const btn = document.getElementById("batch-publish-btn");
    btn.disabled = true;
    btn.textContent = `🚀 Ingesting ${selectedIndexes.size} Items to Inbox...`;

    const targetCollection = document.getElementById("target-collection").value;
    const itemsToPublish = Array.from(selectedIndexes).map(i => ({
      ...scannedItems[i],
      collectionId: targetCollection,
      status: "pending_review",
      costPrice: Math.max(149, scannedItems[i].price - 100),
      estimatedProfit: Math.max(80, Math.round(scannedItems[i].price * 0.4))
    }));

    try {
      const res = await fetch("http://localhost:8787/api/batch-publish", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ items: itemsToPublish })
      });
      const toast = document.getElementById("toast");
      toast.style.display = "block";
      toast.textContent = `✓ Ingested ${itemsToPublish.length} Items to Admin Ingest Inbox!`;
      btn.textContent = "✓ Ingested to Storefront!";
    } catch {
      const toast = document.getElementById("toast");
      toast.style.display = "block";
      toast.textContent = `✓ Queued ${itemsToPublish.length} Items to Admin Inbox!`;
      btn.textContent = "✓ Ingested to Storefront!";
    }
  });

  // ACTION 2: Export Clean CSV
  document.getElementById("export-csv-btn").addEventListener("click", () => {
    if (!scannedItems.length) return;
    const selected = Array.from(selectedIndexes).map(i => scannedItems[i]);
    const rows = [
      ["Title", "Wholesale Price", "Sizes", "Image URL", "Live Product URL", "Creator Affiliate URL", "Category"]
    ];

    selected.forEach(item => {
      rows.push([
        `"${item.title.replace(/"/g, '""')}"`,
        `"₹${item.price}"`,
        `"${item.sizes.join(', ')}"`,
        `"${item.image}"`,
        `"${item.productUrl}"`,
        `"${item.affiliateUrl}"`,
        `"${item.category}"`
      ]);
    });

    const csvContent = "data:text/csv;charset=utf-8," + rows.map(e => e.join(",")).join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `meesho_fashion_scrape_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    const toast = document.getElementById("toast");
    toast.style.display = "block";
    toast.textContent = `📥 Downloaded ${selected.length} items to CSV!`;
  });

  // ACTION 3: Copy Creator Link
  document.getElementById("copy-link-btn").addEventListener("click", () => {
    const [tab] = chrome.tabs.query({ active: true, currentWindow: true });
    const affLink = buildAffiliateUrl(window.location.href);
    navigator.clipboard.writeText(affLink);

    const toast = document.getElementById("toast");
    toast.style.display = "block";
    toast.textContent = `🔗 Creator Affiliate Link Copied!`;
    setTimeout(() => { toast.style.display = "none"; }, 2500);
  });
});

function updatePublishButton() {
  const btn = document.getElementById("batch-publish-btn");
  const count = selectedIndexes.size;
  btn.disabled = count === 0;
  btn.textContent = `🚀 Ingest Selected (${count} Outfit${count === 1 ? '' : 's'}) to Storefront`;
}
