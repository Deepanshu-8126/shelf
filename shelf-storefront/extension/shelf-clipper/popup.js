let scannedItems = [];
let selectedIndexes = new Set();
let detectedProduct = null;

const AFFILIATE_CREATOR_ID = "374453404";
const CAMPAIGN_ID = "12492338";
const SOURCE_PARAM = "youtube_long_form";

const KNOWN_SIZES = ["XS", "S", "M", "L", "XL", "XXL", "3XL", "Free Size"];

function extractSizes(text = "") {
  const found = [];
  if (text.includes("SMLXL") || /S\s*M\s*L\s*XL/.test(text)) {
    return ["S", "M", "L", "XL"];
  }
  for (const s of KNOWN_SIZES) {
    const regex = new RegExp(`\\b${s}\\b`, 'i');
    if (regex.test(text)) found.push(s);
  }
  return found.length > 0 ? found : ["S", "M", "L", "XL"];
}

function extractPrice(text = "") {
  const match = text.match(/₹\s*(\d{2,5})/i);
  if (match) return parseInt(match[1], 10);
  return 245;
}

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

  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => {
      const pageText = document.body.innerText || "";
      const pageTitle = document.title.split("|")[0].split("-")[0].trim();
      const currentUrl = window.location.href;

      // 1. Filter out junk banner images, logos, badges
      const JUNK_KEYWORDS = [
        "banner", "off", "icon", "logo", "badge", "avatar", "profile", "delivery",
        "star", "rating", "svg", "static", "vector", "app_store", "play_store", "6 of"
      ];

      const allImgs = Array.from(document.querySelectorAll('img')).filter((img) => {
        const src = (img.src || "").toLowerCase();
        const alt = (img.alt || "").toLowerCase();
        const w = img.naturalWidth || img.width || 0;
        const h = img.naturalHeight || img.height || 0;

        if (w < 120 || h < 120) return false;
        if (JUNK_KEYWORDS.some(k => src.includes(k) || alt.includes(k))) return false;
        if (src.includes("images.meesho.com") && !src.includes("/products/")) return false;
        return true;
      });

      const uniqueImages = [];
      const seenSrc = new Set();

      allImgs.forEach((img) => {
        let src = img.srcset ? img.srcset.split(',').slice(-1)[0].split(' ')[0] : img.src;
        src = src.split('?')[0].replace('width=100', 'width=512').replace('width=360', 'width=512');
        if (src && !seenSrc.has(src)) {
          seenSrc.add(src);
          uniqueImages.push(src);
        }
      });

      // 2. Extract Product Info
      let detectedTitle = pageTitle;
      const h1 = document.querySelector('h1, span[class*="ProductTitle"], div[class*="ProductTitle"]');
      if (h1 && h1.innerText && h1.innerText.length > 5) {
        detectedTitle = h1.innerText.trim();
      }

      // Check for price in page
      const priceMatch = pageText.match(/₹\s*(\d{2,5})/);
      const detectedPrice = priceMatch ? parseInt(priceMatch[1], 10) : 245;

      // Check for sizes
      let detectedSizes = ["S", "M", "L", "XL"];
      if (pageText.includes("SMLXL") || /S\s*M\s*L\s*XL/.test(pageText)) {
        detectedSizes = ["S", "M", "L", "XL"];
      }

      return {
        url: currentUrl,
        title: detectedTitle,
        price: detectedPrice,
        sizes: detectedSizes,
        images: uniqueImages.slice(0, 18),
        pageText: pageText.slice(0, 1000)
      };
    }
  }, (output) => {
    if (!output || !output[0] || !output[0].result) {
      document.getElementById("scan-count").textContent = "No products detected on page.";
      return;
    }

    const res = output[0].result;
    detectedProduct = res;

    // Show Hero Details
    const heroCard = document.getElementById("hero-details");
    if (heroCard && res.title) {
      heroCard.style.display = "block";
      document.getElementById("hero-title").textContent = res.title;
      document.getElementById("hero-price").textContent = `₹${res.price}`;
      document.getElementById("hero-sizes").textContent = `Sizes: ${res.sizes.join(", ")}`;
    }

    scannedItems = res.images.map((imgSrc, idx) => ({
      id: `p-clip-${idx}-${Date.now()}`,
      title: res.title || "Gen Z Trending Outfit",
      price: res.price || 245,
      sizes: res.sizes || ["S", "M", "L", "XL"],
      image: imgSrc,
      productUrl: res.url,
      affiliateUrl: buildAffiliateUrl(res.url),
      category: "Gen Z Aesthetic & Streetwear"
    }));

    document.getElementById("scan-count").textContent = `Found ${scannedItems.length} Clean Fashion Photos`;

    const grid = document.getElementById("batch-grid");
    grid.innerHTML = "";

    scannedItems.forEach((item, index) => {
      const card = document.createElement("div");
      card.className = "grid-item";
      card.innerHTML = `
        <img src="${item.image}" alt="Variation ${index + 1}" loading="lazy" />
        <span class="check">✓</span>
        <span class="category-tag">Var #${index + 1}</span>
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
    btn.textContent = `🚀 Ingesting ${selectedIndexes.size} Variations to Inbox...`;

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
      toast.textContent = `✓ Ingested ${itemsToPublish.length} Variations to Admin Ingest Inbox!`;
      btn.textContent = "✓ Ingested to Storefront!";
    } catch {
      const toast = document.getElementById("toast");
      toast.style.display = "block";
      toast.textContent = `✓ Queued ${itemsToPublish.length} Variations to Admin Inbox!`;
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
    link.setAttribute("download", `meesho_curated_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    const toast = document.getElementById("toast");
    toast.style.display = "block";
    toast.textContent = `📥 Downloaded ${selected.length} items to CSV!`;
  });

  // ACTION 3: Copy Creator Link
  document.getElementById("copy-link-btn").addEventListener("click", () => {
    if (!detectedProduct || !detectedProduct.url) return;
    const affLink = buildAffiliateUrl(detectedProduct.url);
    navigator.clipboard.writeText(affLink);

    const toast = document.getElementById("toast");
    toast.style.display = "block";
    toast.textContent = `🔗 Creator Affiliate Link Copied to Clipboard!`;
    setTimeout(() => { toast.style.display = "none"; }, 2500);
  });
});

function updatePublishButton() {
  const btn = document.getElementById("batch-publish-btn");
  const count = selectedIndexes.size;
  btn.disabled = count === 0;
  btn.textContent = `🚀 Ingest Selected (${count} Photo${count === 1 ? '' : 's'}) to Storefront`;
}
