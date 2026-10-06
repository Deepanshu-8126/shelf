/**
 * shelf. Universal 3D Stealth Fashion Clipper & Variation Engine
 * 3D interactive tilt, multi-angle 360 scrubbing, deep variant discovery, auto-scroll & multi-store routing.
 */

let scannedItems = [];
let filteredItems = [];
let selectedIndexes = new Set();
let serverBaseUrl = "http://localhost:8787";
let isServerOnline = false;
let currentPlatform = "meesho";

// Default Fallback Affiliate Parameters
let affiliateConfig = {
  creatorId: "374453404",
  campaignId: "12492338",
  sourceParam: "youtube_long_form",
  amazonTag: "shelfcreator-21",
  wishlinkHandle: "shelf.edit"
};

// ─── 1. SERVER HEALTH & DYNAMIC CONFIG SYNC ──────────────────────────────────
async function syncServerConfig() {
  const statusPill = document.getElementById("server-status-pill");
  const statusText = document.getElementById("server-status-text");
  statusPill.className = "status-pill checking";
  statusText.textContent = "Checking Studio...";

  const testUrls = ["http://localhost:8787", "http://127.0.0.1:8787"];

  for (const url of testUrls) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2000);
      const res = await fetch(`${url}/api/health`, { signal: controller.signal });
      clearTimeout(timeoutId);

      if (res.ok) {
        const data = await res.json();
        serverBaseUrl = url;
        isServerOnline = true;
        statusPill.className = "status-pill online";
        statusText.textContent = `🟢 Online (${data.catalogCount || 0})`;
        statusPill.title = `Connected to ${url}. Click to test connection.`;

        // Fetch dynamic Wishlink/Creator config from server
        try {
          const cfgRes = await fetch(`${url}/api/wishlink/config`);
          if (cfgRes.ok) {
            const cfg = await cfgRes.json();
            if (cfg.creatorId) affiliateConfig.creatorId = cfg.creatorId;
            if (cfg.campaignId) affiliateConfig.campaignId = cfg.campaignId;
            if (cfg.handle) affiliateConfig.wishlinkHandle = cfg.handle;
            chrome.storage?.local?.set({ shelf_affiliate_config: affiliateConfig });
          }
        } catch (_) {}

        checkOfflineQueue();
        return;
      }
    } catch (_) {}
  }

  isServerOnline = false;
  statusPill.className = "status-pill offline";
  statusText.textContent = "🔴 Server Offline";
  statusPill.title = "Studio server (port 8787) is offline. Click to test again.";
  checkOfflineQueue();
}

// ─── 2. OFFLINE QUEUE MANAGER ────────────────────────────────────────────────
async function checkOfflineQueue() {
  if (!chrome.storage?.local) return;
  chrome.storage.local.get(["shelf_offline_queue"], (res) => {
    const queue = res.shelf_offline_queue || [];
    const banner = document.getElementById("offline-banner");
    const text = document.getElementById("offline-text");
    if (queue.length > 0) {
      banner.style.display = "flex";
      text.textContent = `📦 ${queue.length} Outfits Saved in Local Queue`;
    } else {
      banner.style.display = "none";
    }
  });
}

async function syncOfflineQueue() {
  if (!isServerOnline) {
    showToast("Cannot sync: Studio server is offline. Start port 8787 first.", true);
    return;
  }
  chrome.storage.local.get(["shelf_offline_queue"], async (res) => {
    const queue = res.shelf_offline_queue || [];
    if (queue.length === 0) return;

    try {
      const syncBtn = document.getElementById("offline-sync-btn");
      syncBtn.disabled = true;
      syncBtn.textContent = "Syncing...";

      const r = await fetch(`${serverBaseUrl}/api/batch-publish`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ items: queue })
      });
      if (r.ok) {
        chrome.storage.local.set({ shelf_offline_queue: [] });
        checkOfflineQueue();
        showToast(`✓ Flushed and synced ${queue.length} offline outfits to Studio!`, false);
        syncServerConfig();
      }
    } catch (err) {
      showToast(`Queue sync error: ${err.message}`, true);
    }
  });
}

// ─── 3. UNIVERSAL MULTI-STORE ROUTER ─────────────────────────────────────────
function detectPlatform(url = "") {
  const u = url.toLowerCase();
  if (u.includes("meesho.com")) return "meesho";
  if (u.includes("wishlink.com")) return "wishlink";
  if (u.includes("amazon.")) return "amazon";
  if (u.includes("pinterest.") || u.includes("pinimg.com")) return "pinterest";
  if (u.includes("myntra.com")) return "myntra";
  if (u.includes("savana.com") || u.includes("urbanic.")) return "savana";
  if (u.includes("flipkart.com")) return "flipkart";
  return "generic";
}

function buildUniversalAffiliateUrl(rawUrl = "") {
  if (!rawUrl) return "";
  const platform = detectPlatform(rawUrl);

  if (platform === "meesho") {
    const extMatch = rawUrl.match(/\/p\/([a-zA-Z0-9]+)/);
    const extId = extMatch ? extMatch[1] : "item";
    const pidMatch = rawUrl.match(/p_id=(\d+)/);
    const pId = pidMatch ? pidMatch[1] : "542355935";
    const enc = encodeURIComponent(rawUrl);
    return `https://www.meesho.com/af_invite/${affiliateConfig.creatorId}:${affiliateConfig.sourceParam}:${affiliateConfig.campaignId}?p_id=${pId}&ext_id=${extId}&utm_source=${affiliateConfig.sourceParam}&url=${enc}`;
  }

  if (platform === "amazon") {
    try {
      const u = new URL(rawUrl);
      u.searchParams.set("tag", affiliateConfig.amazonTag || "shelfcreator-21");
      return u.toString();
    } catch (_) {
      return rawUrl;
    }
  }

  return rawUrl;
}

// ─── 4. INJECTED STEALTH PAGE SCRAPER WITH FULL VARIATION & LINK DISCOVERY ───
function injectedStealthScraper() {
  const JUNK_KEYWORDS = [
    "banner", "off", "icon", "logo", "badge", "avatar", "profile", "delivery",
    "star", "rating", "svg", "static", "vector", "app_store", "play_store",
    "google", "apple", "get it on", "available on", "footer", "download"
  ];

  function cleanHighRes(url) {
    if (!url || typeof url !== "string") return "";
    let clean = url.trim().split("?")[0].split(" ")[0];
    if (!clean.startsWith("http")) return "";
    if (JUNK_KEYWORDS.some(k => clean.toLowerCase().includes(k))) return "";
    return clean
      .replace(/\/(100|256|360|512)\//, "/1024/")
      .replace(/width=\d+/, "width=1024")
      .replace(/\/236x\//, "/736x/")
      .replace(/\/474x\//, "/736x/");
  }

  const photos = [];
  const seenPhotos = new Set();
  function addPhoto(u) {
    const c = cleanHighRes(u);
    if (c && !seenPhotos.has(c)) {
      seenPhotos.add(c);
      photos.push(c);
    }
  }

  // A. Stealth Next.js Hydration Extraction
  let nextProduct = null;
  const nextDataScript = document.getElementById("__NEXT_DATA__");
  if (nextDataScript) {
    try {
      const parsed = JSON.parse(nextDataScript.textContent || "{}");
      const pageProps = parsed?.props?.pageProps;
      if (pageProps?.product) nextProduct = pageProps.product;
      else if (pageProps?.initialState?.product) nextProduct = pageProps.initialState.product;
      const rawJson = JSON.stringify(pageProps || {});
      const cdnMatches = rawJson.match(/https:\/\/(?:images\.meesho\.com\/images\/products|i\.pinimg\.com)[^\s"'\\]+/g);
      if (cdnMatches) cdnMatches.forEach(addPhoto);
    } catch (_) {}
  }

  // B. JSON-LD Structured Data
  document.querySelectorAll('script[type="application/ld+json"]').forEach(s => {
    try {
      const parsed = JSON.parse(s.textContent || "{}");
      const imgs = parsed.image || (parsed["@graph"] && parsed["@graph"].find(g => g.image)?.image);
      if (Array.isArray(imgs)) imgs.forEach(addPhoto);
      else if (typeof imgs === "string") addPhoto(imgs);
    } catch (_) {}
  });

  // C. Meta Tags
  const ogImg = document.querySelector('meta[property="og:image"], meta[name="og:image"], meta[property="twitter:image"]');
  if (ogImg && ogImg.content) addPhoto(ogImg.content);

  // D. DOM Image Fallback
  Array.from(document.querySelectorAll("img")).forEach(img => {
    const src = img.currentSrc || img.src || img.getAttribute("data-src") || "";
    if (src.includes("images.meesho.com") && src.includes("/products/")) addPhoto(src);
    else if (src.includes("pinimg.com")) addPhoto(src);
    else if (src.includes("media-amazon.com/images/I/")) addPhoto(src);
  });

  // E. DEEP VARIATION SCANNER (Color Swatches, Styles, and Direct Variation URLs)
  const swatches = [];
  const seenSwatchUrls = new Set();
  const swatchSelectors = [
    'div[class*="Swatch" i] img',
    'div[class*="Color" i] img',
    'button[class*="Color" i] img',
    'div[class*="Variant" i] img',
    'a[href*="/p/"] img[class*="Swatch" i]',
    'div[class*="Thumbnail" i] img',
    'div[id*="variation_color_name"] li img',
    'div[class*="colors-container" i] img',
    'div[class*="swatches" i] img',
    'div[class*="ProductVariants" i] img'
  ];

  const swatchElements = Array.from(document.querySelectorAll(swatchSelectors.join(", ")));

  swatchElements.forEach((sImg, sIdx) => {
    const sSrc = cleanHighRes(sImg.currentSrc || sImg.src || sImg.getAttribute("data-src") || "");
    if (!sSrc || seenSwatchUrls.has(sSrc)) return;
    seenSwatchUrls.add(sSrc);

    const sLinkEl = sImg.closest("a") || sImg.closest("button");
    const sHref = sLinkEl?.getAttribute("href") || "";
    const sTitle = sImg.alt || sLinkEl?.getAttribute("aria-label") || sImg.getAttribute("title") || `Colorway ${sIdx + 1}`;

    let resolvedUrl = window.location.href;
    if (sHref) {
      resolvedUrl = sHref.startsWith("http") ? sHref : `${window.location.origin}${sHref}`;
    } else {
      // If variant has an extId or parameter, append color query
      const extMatch = sSrc.match(/products\/([a-zA-Z0-9]+)\//);
      if (extMatch && !window.location.href.includes(extMatch[1])) {
        resolvedUrl = `https://www.meesho.com/s/p/${extMatch[1]}`;
      }
    }

    swatches.push({
      id: `swatch-${sIdx}`,
      colorName: sTitle.split("-")[0].replace(/selected/i, "").trim().slice(0, 24) || `Colorway ${sIdx + 1}`,
      image: sSrc,
      url: resolvedUrl
    });
  });

  // F. Sizes & Stock Status
  const detectedSizes = [];
  document.querySelectorAll('span[class*="Size" i], button[class*="Size" i], div[class*="Size" i], li[id*="size_name"]').forEach(el => {
    const t = (el.innerText || "").trim().toUpperCase();
    if (["XS", "S", "M", "L", "XL", "XXL", "3XL", "FREE SIZE"].includes(t) && !detectedSizes.includes(t)) {
      detectedSizes.push(t);
    }
  });
  const finalSizes = detectedSizes.length > 0 ? detectedSizes : ["S", "M", "L", "XL"];

  // G. Color & Fabric text detection
  const bodyText = document.body.innerText || "";
  let detectedColor = "Trending Multi";
  const colorMatch = bodyText.match(/Color\s*:?\s*([A-Za-z]+)/i);
  if (colorMatch) detectedColor = colorMatch[1].trim();

  let detectedFabric = "Cotton/Satin";
  const fabricMatch = bodyText.match(/Fabric\s*:?\s*([A-Za-z\s]+)/i);
  if (fabricMatch) detectedFabric = fabricMatch[1].trim().split("\n")[0].slice(0, 20);

  // H. RELATED / SIMILAR OUTFIT LINKS ON PAGE
  const relatedLooks = [];
  const seenRelated = new Set();
  const relatedCards = Array.from(document.querySelectorAll('a[href*="/p/"]')).slice(0, 16);
  relatedCards.forEach(rc => {
    const rHref = rc.getAttribute("href") || "";
    if (!rHref || rHref.includes(window.location.pathname)) return;
    const rFull = rHref.startsWith("http") ? rHref : `https://www.meesho.com${rHref}`;
    if (seenRelated.has(rFull)) return;
    seenRelated.add(rFull);

    const rImg = rc.querySelector("img");
    const rImgSrc = cleanHighRes(rImg?.currentSrc || rImg?.src || "");
    const rTitle = (rImg?.alt || rc.innerText || "Related Match").trim().slice(0, 45);
    if (rImgSrc) {
      relatedLooks.push({
        title: rTitle,
        image: rImgSrc,
        url: rFull
      });
    }
  });

  const isProductPage = window.location.href.includes("/p/") || !!document.querySelector('h1, span[class*="ProductTitle" i]');
  const items = [];

  if (isProductPage) {
    let title = nextProduct?.name || nextProduct?.title || "";
    if (!title) {
      const titleEl = document.querySelector('h1, span[class*="ProductTitle" i], div[class*="ProductTitle" i]');
      if (titleEl) title = titleEl.innerText.trim();
      if (!title || title.length < 5) title = document.title.split("|")[0].trim();
    }

    let price = nextProduct?.price || 249;
    const priceMatch = bodyText.match(/₹\s*(\d{2,5})/);
    if (priceMatch) price = parseInt(priceMatch[1], 10);

    const extMatch = window.location.href.match(/\/p\/([a-zA-Z0-9]+)/);
    const extId = extMatch ? extMatch[1] : "prod";
    const primaryImg = photos.length > 0 ? photos[0] : (ogImg?.content || window.location.href);

    const cost = Math.max(120, Math.round(price * 0.58));
    const profit = Math.max(80, price - cost);

    // Build variations list: primary item + swatches
    const finalVariations = swatches.length > 0 ? swatches : [
      { id: "swatch-0", colorName: detectedColor, image: primaryImg, url: window.location.href }
    ];

    items.push({
      id: `p-main-${extId}`,
      ext_id: extId,
      title: title.slice(0, 60),
      subtitle: `${detectedColor} · ${detectedFabric} · ${finalSizes.join(", ")}`,
      price: price,
      oldPrice: Math.round(price * 1.35),
      costPrice: cost,
      estimatedProfit: profit,
      sizes: finalSizes,
      image: primaryImg,
      galleryImages: photos.length > 0 ? photos.slice(0, 8) : [primaryImg],
      variations: finalVariations,
      relatedLooks: relatedLooks.slice(0, 6),
      colors: finalVariations.map(s => s.colorName),
      primaryColor: detectedColor,
      fabric: detectedFabric,
      productUrl: window.location.href,
      category: "Gen Z Aesthetic & Streetwear",
      isTrending: true,
      status: "published"
    });
  } else {
    // Multi-product category / catalog page
    const cards = Array.from(document.querySelectorAll('a[href*="/p/"], div[class*="ProductCard" i]'));
    const seenUrls = new Set();

    cards.forEach((card, idx) => {
      const link = card.getAttribute("href") || (card.querySelector('a[href*="/p/"]') ? card.querySelector('a[href*="/p/"]').getAttribute("href") : "");
      if (!link) return;
      const fullUrl = link.startsWith("http") ? link : `https://www.meesho.com${link}`;
      if (seenUrls.has(fullUrl)) return;
      seenUrls.add(fullUrl);

      const extMatch = fullUrl.match(/\/p\/([a-zA-Z0-9]+)/);
      const extId = extMatch ? extMatch[1] : `item${idx}`;
      const imgEl = card.querySelector("img");
      const cleanImg = cleanHighRes(imgEl?.currentSrc || imgEl?.src || "");
      if (!cleanImg) return;

      const cardText = (card.innerText || "").trim();
      const pMatch = cardText.match(/₹\s*(\d{2,5})/);
      const p = pMatch ? parseInt(pMatch[1], 10) : 299;

      let cardTitle = (imgEl?.alt || "").trim();
      if (!cardTitle || cardTitle.length < 5) {
        const lines = cardText.split("\n").map(l => l.trim()).filter(l => l.length > 5 && !l.startsWith("₹") && !l.startsWith("★"));
        if (lines.length > 0) cardTitle = lines[0];
        else cardTitle = `Trending Fashion Find #${idx + 1}`;
      }

      const cost = Math.max(120, Math.round(p * 0.58));
      const profit = Math.max(80, p - cost);

      items.push({
        id: `p-deep-${extId}`,
        ext_id: extId,
        title: cardTitle.slice(0, 60),
        subtitle: "Verified Sourcing Deal · High Velocity",
        price: p,
        oldPrice: Math.round(p * 1.35),
        costPrice: cost,
        estimatedProfit: profit,
        sizes: ["S", "M", "L", "XL"],
        image: cleanImg,
        galleryImages: [cleanImg],
        variations: [{ id: `swatch-${idx}`, colorName: "Standard", image: cleanImg, url: fullUrl }],
        relatedLooks: [],
        colors: ["Standard"],
        primaryColor: "Standard",
        fabric: "Cotton/Blend",
        productUrl: fullUrl,
        category: "Gen Z Aesthetic & Streetwear",
        isTrending: true,
        status: "published"
      });
    });
  }

  return items;
}

// ─── 5. UI RENDERING & 3D INTERACTIVE CARDS ──────────────────────────────────
function renderBatchGrid() {
  const grid = document.getElementById("batch-grid");
  const countEl = document.getElementById("scan-count");
  const varCountBadge = document.getElementById("variation-count-badge");
  grid.innerHTML = "";

  const itemsToDisplay = filteredItems.length > 0 || document.getElementById("search-filter").value.trim() !== "" 
    ? filteredItems 
    : scannedItems;

  let totalVariationsDiscovered = 0;
  itemsToDisplay.forEach(item => {
    totalVariationsDiscovered += (item.variations?.length || 1);
  });
  if (varCountBadge) {
    varCountBadge.textContent = `${totalVariationsDiscovered} Variations`;
  }

  if (itemsToDisplay.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: span 3; text-align: center; padding: 28px 10px; color: #a1a1aa;">
        <span style="font-size: 26px; display: block; margin-bottom: 6px;">🔍</span>
        <strong style="color: #f4f4f5; font-size: 13.5px;">No outfits detected yet</strong>
        <p style="font-size: 12px; margin-top: 4px; color: #94a3b8;">Click '⚡ Auto-Scroll Scan' below to discover all variations.</p>
      </div>
    `;
    countEl.textContent = "0 products detected";
    updateProfitRadar();
    updatePublishButton();
    return;
  }

  countEl.textContent = `${itemsToDisplay.length} outfits available (${selectedIndexes.size} selected)`;

  itemsToDisplay.forEach((item, index) => {
    const card = document.createElement("div");
    const isSelected = selectedIndexes.has(index);
    card.className = `grid-item ${isSelected ? "selected" : ""}`;
    const angles = item.galleryImages?.length || 1;
    const variants = item.variations || [];

    // Swatches HTML on card
    let swatchesHtml = "";
    if (variants.length > 1) {
      swatchesHtml = `<div class="swatch-bar">`;
      variants.slice(0, 4).forEach((v, vIdx) => {
        const fallbackColors = ["#18181b", "#831843", "#064e3b", "#fda4af", "#2563eb", "#ea580c"];
        const dotBg = fallbackColors[vIdx % fallbackColors.length];
        swatchesHtml += `<div class="swatch-dot" data-img="${v.image}" data-url="${v.url}" title="${v.colorName}" style="background:${dotBg};"></div>`;
      });
      swatchesHtml += `</div>`;
    }

    card.innerHTML = `
      <img src="${item.image}" alt="${item.title}" loading="lazy" />
      <div class="shine-overlay"></div>
      <span class="check">✓</span>
      <span class="angle-badge">1/${angles}</span>
      ${swatchesHtml}

      <!-- Quick 3D & AI Actions -->
      <div class="quick-actions">
        <button class="quick-btn btn-3d" title="Open 3D Web Experience Holo Stage">🧊 3D</button>
        <button class="quick-btn btn-veo" title="Send to Veo 2 Studio">🎬 Veo</button>
        <button class="quick-btn btn-photo" title="Send to Photoshoot Studio">📸 Photo</button>
      </div>

      <div class="meta-tag">
        <span class="price">₹${item.price}</span>
        <span class="profit-tag">+₹${item.estimatedProfit}</span>
      </div>
    `;

    // ─── 3D PERSPECTIVE TILT & HORIZONTAL ANGLE SCRUBBING ───
    card.addEventListener("mousemove", (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const xPct = Math.max(0, Math.min(1, x / rect.width));
      const yPct = Math.max(0, Math.min(1, y / rect.height));

      // Specular reflection shine position
      card.style.setProperty("--shine-x", `${(xPct * 100).toFixed(0)}%`);
      card.style.setProperty("--shine-y", `${(yPct * 100).toFixed(0)}%`);

      // 3D Perspective Tilt Transform
      const rotateX = (0.5 - yPct) * 18;
      const rotateY = (xPct - 0.5) * 18;
      card.style.transform = `perspective(1000px) rotateX(${rotateX.toFixed(1)}deg) rotateY(${rotateY.toFixed(1)}deg) scale3d(1.04, 1.04, 1.04)`;

      // Multi-Angle Horizontal 360 Scrubber
      const gallery = item.galleryImages || [item.image];
      if (gallery.length > 1) {
        const angleIdx = Math.min(gallery.length - 1, Math.floor(xPct * gallery.length));
        const imgEl = card.querySelector("img");
        if (imgEl && imgEl.src !== gallery[angleIdx]) {
          imgEl.src = gallery[angleIdx];
          const badge = card.querySelector(".angle-badge");
          if (badge) badge.textContent = `${angleIdx + 1}/${gallery.length}`;
        }
      }
    });

    card.addEventListener("mouseleave", () => {
      card.style.transform = "perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)";
      const imgEl = card.querySelector("img");
      if (imgEl) imgEl.src = item.image;
      const badge = card.querySelector(".angle-badge");
      if (badge) badge.textContent = `1/${(item.galleryImages || []).length || 1}`;
    });

    // ─── INTERACTIVE SWATCH VARIANT SWITCHING ───
    card.querySelectorAll(".swatch-dot").forEach(dot => {
      dot.addEventListener("click", (e) => {
        e.stopPropagation();
        const newImg = dot.getAttribute("data-img");
        const newUrl = dot.getAttribute("data-url");
        if (newImg) {
          item.image = newImg;
          card.querySelector("img").src = newImg;
        }
        if (newUrl) {
          item.productUrl = newUrl;
          item.affiliateUrl = buildUniversalAffiliateUrl(newUrl);
        }
        showToast(`Switched to variant: ${dot.title || "Selected Swatch"}`, false);
      });
    });

    // ─── OPEN 3D WEB EXPERIENCE HOLO STAGE MODAL ───
    card.querySelector(".btn-3d").addEventListener("click", (e) => {
      e.stopPropagation();
      openThreeDModal(item);
    });

    // Card selection toggle
    card.addEventListener("click", (e) => {
      if (e.target.closest(".quick-btn") || e.target.closest(".swatch-dot")) return;
      if (selectedIndexes.has(index)) {
        selectedIndexes.delete(index);
        card.classList.remove("selected");
      } else {
        selectedIndexes.add(index);
        card.classList.add("selected");
      }
      updateProfitRadar();
      updatePublishButton();
    });

    // 1-Click Veo Reel Action
    card.querySelector(".btn-veo").addEventListener("click", async (e) => {
      e.stopPropagation();
      await directLaunchStudio(item, "veo");
    });

    // 1-Click Photoshoot Action
    card.querySelector(".btn-photo").addEventListener("click", async (e) => {
      e.stopPropagation();
      await directLaunchStudio(item, "photoshoot");
    });

    grid.appendChild(card);
  });

  updateProfitRadar();
  updatePublishButton();
}

function updateProfitRadar() {
  const breakdown = document.getElementById("radar-breakdown");
  const profitTag = document.getElementById("radar-profit-tag");

  let totalCost = 0;
  let totalSell = 0;
  let totalProfit = 0;

  selectedIndexes.forEach(idx => {
    const item = scannedItems[idx];
    if (item) {
      totalCost += (item.costPrice || item.price * 0.58);
      totalSell += item.price;
      totalProfit += (item.estimatedProfit || item.price * 0.42);
    }
  });

  const count = selectedIndexes.size;
  const marginPct = totalSell > 0 ? Math.round((totalProfit / totalSell) * 100) : 62;

  breakdown.textContent = `Selected: ${count} outfits · Wholesale Sourcing: ₹${Math.round(totalCost)}`;
  profitTag.textContent = `+₹${Math.round(totalProfit)} (${marginPct}% Profit)`;
}

function updatePublishButton() {
  const btn = document.getElementById("batch-publish-btn");
  const count = selectedIndexes.size;
  btn.disabled = count === 0;
  btn.innerHTML = `<span>🚀 Ingest Selected (${count} Items) to Storefront</span>`;
}

function showToast(message, isError = false, actionHtml = "") {
  const toast = document.getElementById("toast-box");
  toast.className = `toast-box ${isError ? "error" : "success"}`;
  toast.innerHTML = `<div>${message}</div>${actionHtml}`;
}

// ─── 6. INTERACTIVE 3D WEB EXPERIENCE HOLO STAGE MODAL ───────────────────────
let active3DItem = null;
let stageRotX = 5;
let stageRotY = 0;
let isDraggingStage = false;
let startMouseX = 0;
let startMouseY = 0;
let autoSpinTimer = null;
let currentLightMode = 0; // 0: Studio, 1: Cyber Neon, 2: Noir Gold

function openThreeDModal(item) {
  active3DItem = item;
  const modal = document.getElementById("three-d-modal");
  const stageImg = document.getElementById("stage-img");
  const swatchList = document.getElementById("modal-swatch-list");
  const linksTable = document.getElementById("modal-links-table");

  stageImg.src = item.image;
  stageRotX = 5;
  stageRotY = 0;
  updateStageTransform();

  // Populate Swatches
  const variants = item.variations && item.variations.length > 0 
    ? item.variations 
    : [{ colorName: item.primaryColor || "Standard", image: item.image, url: item.productUrl }];

  swatchList.innerHTML = "";
  variants.forEach((v, idx) => {
    const pill = document.createElement("div");
    pill.className = `modal-swatch-pill ${idx === 0 ? "active" : ""}`;
    pill.innerHTML = `
      <img src="${v.image}" alt="${v.colorName}" />
      <span>${v.colorName}</span>
    `;
    pill.addEventListener("click", () => {
      swatchList.querySelectorAll(".modal-swatch-pill").forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      stageImg.src = v.image;
      item.image = v.image;
      item.productUrl = v.url || item.productUrl;
      item.affiliateUrl = buildUniversalAffiliateUrl(v.url || item.productUrl);
    });
    swatchList.appendChild(pill);
  });

  // Populate Variation Links Table
  linksTable.innerHTML = "";
  variants.forEach((v, idx) => {
    const row = document.createElement("div");
    row.className = "link-row";
    const vAff = buildUniversalAffiliateUrl(v.url || item.productUrl);
    row.innerHTML = `
      <div class="link-row-info">
        <img src="${v.image}" alt="${v.colorName}" />
        <span class="link-title">${v.colorName} · ₹${item.price} (+₹${item.estimatedProfit} Profit)</span>
      </div>
      <div class="link-row-actions">
        <button class="mini-link-btn btn-copy" data-url="${vAff}">📋 Copy Link</button>
        <a class="mini-link-btn" href="${vAff}" target="_blank">↗️ Open</a>
      </div>
    `;
    row.querySelector(".btn-copy").addEventListener("click", (e) => {
      const u = e.currentTarget.getAttribute("data-url");
      navigator.clipboard.writeText(u);
      showToast(`✓ Copied link for ${v.colorName}!`, false);
    });
    linksTable.appendChild(row);
  });

  // Also include related look links if available
  if (item.relatedLooks && item.relatedLooks.length > 0) {
    item.relatedLooks.forEach(r => {
      const row = document.createElement("div");
      row.className = "link-row";
      const rAff = buildUniversalAffiliateUrl(r.url);
      row.innerHTML = `
        <div class="link-row-info">
          <img src="${r.image}" alt="${r.title}" />
          <span class="link-title">🔗 Match: ${r.title}</span>
        </div>
        <div class="link-row-actions">
          <button class="mini-link-btn btn-copy" data-url="${rAff}">📋 Copy Link</button>
          <a class="mini-link-btn" href="${rAff}" target="_blank">↗️ Open</a>
        </div>
      `;
      row.querySelector(".btn-copy").addEventListener("click", (e) => {
        const u = e.currentTarget.getAttribute("data-url");
        navigator.clipboard.writeText(u);
        showToast(`✓ Copied link for ${r.title}!`, false);
      });
      linksTable.appendChild(row);
    });
  }

  modal.classList.add("open");
}

function closeThreeDModal() {
  const modal = document.getElementById("three-d-modal");
  modal.classList.remove("open");
  stopAutoSpin();
}

function updateStageTransform() {
  const card = document.getElementById("stage-card");
  if (card) {
    card.style.transform = `rotateY(${stageRotY}deg) rotateX(${stageRotX}deg)`;
  }
}

function startAutoSpin() {
  if (autoSpinTimer) return;
  const spinBtn = document.getElementById("spin-toggle-btn");
  spinBtn.classList.add("active");
  autoSpinTimer = setInterval(() => {
    stageRotY = (stageRotY + 1.2) % 360;
    updateStageTransform();
  }, 25);
}

function stopAutoSpin() {
  if (autoSpinTimer) {
    clearInterval(autoSpinTimer);
    autoSpinTimer = null;
    const spinBtn = document.getElementById("spin-toggle-btn");
    if (spinBtn) spinBtn.classList.remove("active");
  }
}

// ─── 7. DIRECT LAUNCH IN AI STUDIO ───────────────────────────────────────────
async function directLaunchStudio(item, mode = "veo") {
  showToast(`⏳ Ingesting "${item.title.slice(0, 30)}..." and launching ${mode.toUpperCase()} Studio...`, false);

  item.affiliateUrl = buildUniversalAffiliateUrl(item.productUrl);
  item.status = "published";

  try {
    if (isServerOnline) {
      await fetch(`${serverBaseUrl}/api/batch-publish`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ items: [item] })
      });
    }
    const studioUrl = `${serverBaseUrl}/#studio?mode=${mode}&img=${encodeURIComponent(item.image)}&title=${encodeURIComponent(item.title)}`;
    chrome.tabs.create({ url: studioUrl });
    showToast(`✓ Opened in AI Studio!`, false);
  } catch (err) {
    showToast(`Launch Error: ${err.message}`, true);
  }
}

// ─── 8. AUTO-SCROLL PAGE & VARIATION SCRAPER ROUTINE ─────────────────────────
async function executeAutoScrollAndScan() {
  const hud = document.getElementById("scroll-status-hud");
  const hudText = document.getElementById("scroll-hud-text");
  const hudFill = document.getElementById("scroll-hud-fill");
  const autoBtn = document.getElementById("auto-scroll-btn");

  hud.classList.add("active");
  hudText.textContent = "⚡ Auto-scrolling host page to hydrate swatches & variations...";
  hudFill.style.width = "20%";
  autoBtn.disabled = true;

  const [activeTab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!activeTab?.id) {
    hud.classList.remove("active");
    autoBtn.disabled = false;
    return;
  }

  try {
    hudFill.style.width = "50%";
    const results = await chrome.scripting.executeScript({
      target: { tabId: activeTab.id },
      func: async () => {
        // Smooth progressive human-like scroll down
        const steps = 6;
        for (let i = 1; i <= steps; i++) {
          const scrollDistance = Math.floor(Math.random() * (650 - 450 + 1)) + 450;
          const jitter = Math.floor(Math.random() * (550 - 320 + 1)) + 320;
          window.scrollBy({ top: scrollDistance, behavior: "smooth" });
          await new Promise(r => setTimeout(r, jitter));
        }

        // Smooth scroll back to top
        window.scrollTo({ top: 0, behavior: "smooth" });
        await new Promise(r => setTimeout(r, 500));

        // Execute scraper function
        const fn = injectedStealthScraper;
        return fn();
      },
    });

    hudFill.style.width = "90%";

    if (results?.[0]?.result && results[0].result.length > 0) {
      scannedItems = results[0].result;
      scannedItems.forEach(i => {
        i.affiliateUrl = buildUniversalAffiliateUrl(i.productUrl || activeTab.url);
      });
      selectedIndexes = new Set(scannedItems.map((_, i) => i));
      filteredItems = [...scannedItems];
      renderBatchGrid();
      hudFill.style.width = "100%";
      hudText.textContent = `✓ Auto-Scroll complete! Found ${scannedItems.length} outfits with full variations.`;
      setTimeout(() => { hud.classList.remove("active"); }, 2800);
      showToast(`✓ Auto-Scroll complete! Discovered ${scannedItems.length} outfits and colorways.`, false);
    } else {
      hudText.textContent = "✓ Scan complete.";
      setTimeout(() => { hud.classList.remove("active"); }, 1500);
    }
  } catch (err) {
    hud.classList.remove("active");
    showToast(`Scan Error: ${err.message}`, true);
  } finally {
    autoBtn.disabled = false;
  }
}

// ─── 9. INITIALIZATION & LISTENERS ───────────────────────────────────────────
document.addEventListener("DOMContentLoaded", async () => {
  // Sync Server Health & Config
  syncServerConfig();
  document.getElementById("server-status-pill").addEventListener("click", syncServerConfig);
  document.getElementById("offline-sync-btn").addEventListener("click", syncOfflineQueue);

  // Close 3D Modal listener
  document.getElementById("close-modal-btn").addEventListener("click", closeThreeDModal);

  // 3D Turntable Orbit Dragging Handlers
  const stageWrapper = document.getElementById("stage-wrapper");
  stageWrapper.addEventListener("mousedown", (e) => {
    isDraggingStage = true;
    startMouseX = e.clientX;
    startMouseY = e.clientY;
    stopAutoSpin();
  });

  window.addEventListener("mousemove", (e) => {
    if (!isDraggingStage) return;
    const deltaX = e.clientX - startMouseX;
    const deltaY = e.clientY - startMouseY;
    stageRotY += deltaX * 0.7;
    stageRotX = Math.max(-40, Math.min(40, stageRotX - deltaY * 0.5));
    startMouseX = e.clientX;
    startMouseY = e.clientY;
    updateStageTransform();
  });

  window.addEventListener("mouseup", () => {
    isDraggingStage = false;
  });

  // Auto-Spin Button
  document.getElementById("spin-toggle-btn").addEventListener("click", () => {
    if (autoSpinTimer) stopAutoSpin();
    else startAutoSpin();
  });

  // Lighting Switcher Button
  document.getElementById("light-toggle-btn").addEventListener("click", () => {
    currentLightMode = (currentLightMode + 1) % 3;
    const disk = document.getElementById("stage-disk");
    const lightBtn = document.getElementById("light-toggle-btn");
    if (currentLightMode === 0) {
      lightBtn.textContent = "💡 Studio White";
      disk.style.background = "radial-gradient(ellipse at center, rgba(59, 130, 246, 0.4) 0%, rgba(236, 72, 153, 0.15) 50%, transparent 75%)";
      disk.style.boxShadow = "0 0 25px rgba(59, 130, 246, 0.35)";
    } else if (currentLightMode === 1) {
      lightBtn.textContent = "⚡ Cyber Neon";
      disk.style.background = "radial-gradient(ellipse at center, rgba(236, 72, 153, 0.6) 0%, rgba(56, 189, 248, 0.25) 50%, transparent 75%)";
      disk.style.boxShadow = "0 0 35px rgba(236, 72, 153, 0.5)";
    } else {
      lightBtn.textContent = "🌙 Noir Gold";
      disk.style.background = "radial-gradient(ellipse at center, rgba(245, 158, 11, 0.5) 0%, rgba(234, 88, 12, 0.2) 50%, transparent 75%)";
      disk.style.boxShadow = "0 0 30px rgba(245, 158, 11, 0.45)";
    }
  });

  // Center / Reset Stage Button
  document.getElementById("reset-stage-btn").addEventListener("click", () => {
    stageRotX = 5;
    stageRotY = 0;
    updateStageTransform();
  });

  // Detect Current Tab Platform
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab?.url) {
    currentPlatform = detectPlatform(tab.url);
    const badge = document.getElementById("platform-badge");
    const icons = {
      meesho: "Meesho 📦",
      wishlink: "Wishlink 🔗",
      amazon: "Amazon 🛒",
      pinterest: "Pinterest 📌",
      myntra: "Myntra 👗",
      savana: "Savana ✨",
      flipkart: "Flipkart 🛍️",
      generic: "Web Store 🌐"
    };
    badge.textContent = icons[currentPlatform] || "Web Store 🌐";
  }

  // Auto-scroll Trigger Listeners
  document.getElementById("auto-scroll-btn").addEventListener("click", executeAutoScrollAndScan);
  document.getElementById("auto-discover-btn").addEventListener("click", executeAutoScrollAndScan);

  // AUTOMATIC INITIAL AUTO-SCROLL PASS ("jahibhi use karu uski scroll ho jaey")
  if (tab?.id) {
    executeAutoScrollAndScan();
  }

  // Filter & Search Input
  document.getElementById("search-filter").addEventListener("input", (e) => {
    const q = e.target.value.toLowerCase().trim();
    if (!q) {
      filteredItems = [...scannedItems];
    } else {
      filteredItems = scannedItems.filter(i => 
        (i.title || "").toLowerCase().includes(q) || 
        (i.subtitle || "").toLowerCase().includes(q) || 
        (i.primaryColor || "").toLowerCase().includes(q)
      );
    }
    renderBatchGrid();
  });

  // Toggle Select All
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
    updateProfitRadar();
    updatePublishButton();
  });

  // ACTION: Ingest to Storefront & Studio
  document.getElementById("batch-publish-btn").addEventListener("click", async () => {
    const btn = document.getElementById("batch-publish-btn");
    btn.disabled = true;
    const count = selectedIndexes.size;
    btn.innerHTML = `<span>🚀 Ingesting ${count} Items...</span>`;

    const targetCollection = document.getElementById("target-collection").value;
    const itemsToPublish = Array.from(selectedIndexes).map(i => ({
      ...scannedItems[i],
      collectionId: targetCollection,
      affiliateUrl: scannedItems[i].affiliateUrl || buildUniversalAffiliateUrl(scannedItems[i].productUrl),
      status: "published"
    }));

    if (!isServerOnline) {
      if (chrome.storage?.local) {
        chrome.storage.local.get(["shelf_offline_queue"], (res) => {
          const currentQueue = res.shelf_offline_queue || [];
          const updated = [...currentQueue, ...itemsToPublish];
          chrome.storage.local.set({ shelf_offline_queue: updated });
          checkOfflineQueue();
          showToast(`📦 Server offline: ${itemsToPublish.length} items queued in local storage.`, false);
          btn.innerHTML = `<span>✓ Saved to Local Queue</span>`;
        });
      }
      return;
    }

    try {
      const res = await fetch(`${serverBaseUrl}/api/batch-publish`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ items: itemsToPublish })
      });

      if (!res.ok) {
        const errText = await res.text();
        throw new Error(`HTTP ${res.status}: ${errText.slice(0, 80)}`);
      }

      const data = await res.json();
      const pubCount = data.publishedCount || itemsToPublish.length;
      const studioLink = `<a class="toast-action" href="${serverBaseUrl}/#studio" target="_blank">Open in AI Media Studio (Veo Reel / Photoshoot Ready) ➔</a>`;
      showToast(`✓ Ingested ${pubCount} outfits! (Total Catalog: ${data.totalCatalogSize})`, false, studioLink);
      btn.innerHTML = `<span>✓ Ingested to Storefront!</span>`;
      syncServerConfig();
    } catch (err) {
      showToast(`❌ Ingest Error: ${err.message}`, true);
      btn.disabled = false;
      btn.innerHTML = `<span>🚀 Retry Ingest (${count} Items)</span>`;
    }
  });

  // ACTION: Export Clean CSV
  document.getElementById("export-csv-btn").addEventListener("click", () => {
    if (!scannedItems.length) {
      showToast("No items available to export.", true);
      return;
    }
    const selected = Array.from(selectedIndexes).map(i => scannedItems[i]);
    const rows = [
      ["Title", "Wholesale Price", "Est Reseller Profit", "Sizes", "High-Res Image", "Gallery Images", "Variations Count", "Product URL", "Affiliate URL", "Category"]
    ];

    selected.forEach(item => {
      const galleryStr = (item.galleryImages || [item.image]).join(" | ");
      rows.push([
        `"${(item.title || "").replace(/"/g, '""')}"`,
        `"₹${item.price || 0}"`,
        `"₹${item.estimatedProfit || 0}"`,
        `"${(item.sizes || []).join(", ")}"`,
        `"${item.image || ""}"`,
        `"${galleryStr}"`,
        `"${(item.variations || []).length}"`,
        `"${item.productUrl || ""}"`,
        `"${item.affiliateUrl || ""}"`,
        `"${item.category || ""}"`
      ]);
    });

    const csvContent = "data:text/csv;charset=utf-8," + rows.map(e => e.join(",")).join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `shelf_3d_fashion_scrape_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast(`📥 Exported ${selected.length} items to CSV!`, false);
  });

  // ACTION: Copy Creator Link
  document.getElementById("copy-link-btn").addEventListener("click", async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const url = tab?.url || window.location.href;
    const affLink = buildUniversalAffiliateUrl(url);

    navigator.clipboard.writeText(affLink).then(() => {
      showToast(`🔗 Creator affiliate link copied to clipboard!`, false);
    }).catch(() => {
      showToast("Failed to copy link to clipboard.", true);
    });
  });
});
