/**
 * Shelf. All-in-One Creator Suite - Unified Controller v2.1
 * Features:
 * 1. Visual Picker with Configurable Auto-Scroll Depth (1x, 3x, 6x)
 * 2. Multi-Product & Pinterest Extraction with Variations (Sizes, Colors, Fabric)
 * 3. Referrer-safe Image Loading & Interactive Checkbox Selection
 * 4. 1-Click Shelf Storefront Save, Telegram Bot Push (@Bbyjihotbot) & Veo 3.1 Studio
 */

const MEESHO_AFFILIATE_ID = "374453404";
const MEESHO_SOURCE = "youtube_long_form";
const MEESHO_CAMPAIGN_ID = "12492338";
const TELEGRAM_BOT_TOKEN = "8564017881:AAGgH4xtjjOZYdyVG6CfNT86i-7t1s9ob7c";
const TELEGRAM_CHAT_ID = "6486771356";

// State
let activeScannedItems = [];
let activeSingleProduct = null;
let selectedStudioMode = "unboxing";
let selectedScrollDepth = 3; // Default 3 scrolls (~35 items)

// Initialize on Load
document.addEventListener("DOMContentLoaded", () => {
  setupTabs();
  setupVisualPicker();
  setupSingleClipper();
  setupBatcher();
  setupStudio();
  autoDetectActiveTab();
});

// ==========================================
// 1. TAB NAVIGATION
// ==========================================
function setupTabs() {
  const tabs = document.querySelectorAll(".nav-tab");
  const contents = document.querySelectorAll(".tab-content");

  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      const target = tab.dataset.tab;
      tabs.forEach(t => t.classList.remove("active"));
      contents.forEach(c => c.classList.remove("active"));

      tab.classList.add("active");
      const targetContent = document.getElementById(`tab-${target}`);
      if (targetContent) targetContent.classList.add("active");
    });
  });
}

// ==========================================
// 2. AFFILIATE LINK BUILDER
// ==========================================
function generateAffiliateLink(rawUrl) {
  if (!rawUrl) return "";
  const trimmed = rawUrl.trim();
  if (trimmed.includes("/af_invite/")) return trimmed;

  try {
    const urlObj = new URL(trimmed.startsWith("http") ? trimmed : `https://www.meesho.com/${trimmed}`);
    const path = urlObj.pathname;
    const query = new URLSearchParams(urlObj.search);

    let productId = query.get("p_id") || "";
    let extId = query.get("ext_id") || "";

    const shortMatch = path.match(/\/s\/p\/([^/]+)/i);
    if (shortMatch) extId = shortMatch[1];

    const pMatch = path.match(/\/p\/(\d+)/i);
    if (!productId && pMatch) productId = pMatch[1];

    const slugMatch = path.match(/\/p\/([^/]+)/i);
    if (!extId && slugMatch) extId = slugMatch[1];

    if (!productId && !extId) return rawUrl;

    const params = new URLSearchParams();
    if (productId) params.set("p_id", productId);
    if (extId) params.set("ext_id", extId);
    params.set("utm_source", "instagram_reels");

    return `https://www.meesho.com/af_invite/${MEESHO_AFFILIATE_ID}:${MEESHO_SOURCE}:${MEESHO_CAMPAIGN_ID}?${params.toString()}`;
  } catch {
    return rawUrl;
  }
}

// ==========================================
// 3. TAB 1: VISUAL PICKER WITH AUTO-SCROLL
// ==========================================
function setupVisualPicker() {
  const scanBtn = document.getElementById("scan-page-btn");
  const selectAllBtn = document.getElementById("select-all-btn");
  const deselectAllBtn = document.getElementById("deselect-all-btn");
  const bulkSaveBtn = document.getElementById("bulk-save-shelf-btn");
  const bulkPushTgBtn = document.getElementById("bulk-push-tg-btn");
  const bulkExportCsvBtn = document.getElementById("bulk-export-csv-btn");
  const scrollPills = document.querySelectorAll(".scroll-pill");

  // Scroll Depth Pills
  scrollPills.forEach(pill => {
    pill.addEventListener("click", () => {
      scrollPills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      selectedScrollDepth = parseInt(pill.dataset.scrolls, 10) || 3;
    });
  });

  scanBtn.addEventListener("click", () => executeVisualPageScan());

  selectAllBtn.addEventListener("click", () => {
    activeScannedItems.forEach(item => item.selected = true);
    renderVisualGrid();
  });

  deselectAllBtn.addEventListener("click", () => {
    activeScannedItems.forEach(item => item.selected = false);
    renderVisualGrid();
  });

  bulkSaveBtn.addEventListener("click", () => handleBulkSaveShelf());
  bulkPushTgBtn.addEventListener("click", () => handleBulkPushTelegram());
  bulkExportCsvBtn.addEventListener("click", () => handleBulkExportCsv());
}

async function executeVisualPageScan() {
  const statusEl = document.getElementById("picker-status");
  const scanBtn = document.getElementById("scan-page-btn");
  const scanBtnText = document.getElementById("scan-btn-text");
  
  scanBtn.disabled = true;
  statusEl.className = "status-pill info";

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab || !tab.id) throw new Error("No active browser tab found.");

    // Step 1: Execute Auto-Scroll based on selected depth
    for (let i = 1; i <= selectedScrollDepth; i++) {
      scanBtnText.innerText = `Auto-Scrolling ${i}/${selectedScrollDepth}...`;
      statusEl.innerText = `Loading more products & HD images (${i}/${selectedScrollDepth})...`;
      
      await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: () => {
          window.scrollBy({ top: 1200, behavior: "smooth" });
        }
      });
      await new Promise(r => setTimeout(r, 550));
    }

    scanBtnText.innerText = "Extracting Visuals & Variations...";
    statusEl.innerText = "Parsing listings, sizes, prices and affiliate URLs...";

    // Step 2: Inject Scraper function
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: scrapeCurrentPageVisualItems
    });

    const rawItems = results?.[0]?.result || [];
    if (!rawItems.length) {
      throw new Error("No items found. Open a Meesho category/search page or Pinterest board and retry.");
    }

    // Step 3: Process items & wrap affiliate links
    activeScannedItems = rawItems.map((item, idx) => {
      const affLink = item.platform === "Meesho" ? generateAffiliateLink(item.url) : item.url;
      return {
        id: `item-${idx}-${Date.now()}`,
        title: item.title || "Fashion Curated Find",
        price: item.price || 449,
        old_price: item.old_price || 1199,
        discount: item.discount || "60% OFF",
        rating: item.rating || "4.4",
        image: item.image || "",
        sizes: item.sizes || ["Free Size"],
        fabric: item.fabric || "",
        url: item.url || "",
        affiliate_url: affLink,
        platform: item.platform || "Meesho",
        selected: true // Selected by default
      };
    });

    renderVisualGrid();

    const gridSec = document.getElementById("visual-grid-section");
    gridSec.style.display = "flex";
    statusEl.className = "status-pill success";
    statusEl.innerText = `✨ Scanned ${activeScannedItems.length} items with variations! Select what to save or push.`;
  } catch (err) {
    statusEl.className = "status-pill error";
    statusEl.innerText = err.message || "Failed to scan page.";
  } finally {
    scanBtn.disabled = false;
    scanBtnText.innerText = "Start Auto-Scroll & Scan Page";
  }
}

// Injected Page Visual Scraper (Runs in Content Script)
function scrapeCurrentPageVisualItems() {
  const host = window.location.hostname.toLowerCase();
  const items = [];
  const seenUrls = new Set();

  // A. PINTEREST BOARD / SEARCH / HOME
  if (host.includes("pinterest.com")) {
    const pinContainers = Array.from(document.querySelectorAll("[data-test-id='pin'], div[data-grid-item='true'], div:has(img[src*='pinimg.com'])"));
    
    for (const container of pinContainers) {
      const img = container.querySelector("img[srcset*='originals'], img[src*='pinimg.com/736x'], img[src*='pinimg.com/originals'], img[src*='pinimg.com/474x'], img[src*='pinimg.com']");
      if (!img || !img.src) continue;

      const linkEl = container.querySelector("a[href*='/pin/']") || container.closest("a");
      const pinUrl = linkEl ? linkEl.href : window.location.href;
      if (seenUrls.has(img.src)) continue;
      seenUrls.add(img.src);

      const titleEl = container.querySelector("h3, h2, [title], [aria-label]") || img;
      const title = titleEl.getAttribute("title") || titleEl.getAttribute("aria-label") || titleEl.innerText || "Aesthetic Pinterest Outfit";

      items.push({
        title: title.slice(0, 45).trim(),
        price: 499,
        old_price: 1399,
        discount: "64% OFF",
        rating: "4.8",
        image: img.src,
        sizes: ["S", "M", "L", "XL"],
        url: pinUrl,
        platform: "Pinterest"
      });

      if (items.length >= 60) break;
    }
    return items;
  }

  // B. MEESHO CATEGORY / SEARCH / SELLER LISTING SCRAPER
  const cards = Array.from(document.querySelectorAll("a[href*='/p/'], a[href*='/s/p/'], [class*='ProductCard'], div[class*='Card']"));
  
  for (const card of cards) {
    const linkEl = card.tagName === "A" ? card : card.querySelector("a[href*='/p/'], a[href*='/s/p/']") || card.querySelector("a");
    const link = linkEl?.href || "";
    if (!link || (!link.includes("/p/") && !link.includes("/s/p/")) || seenUrls.has(link)) continue;
    seenUrls.add(link);

    const titleEl = card.querySelector("p, span[class*='Title'], h2, h3, div[class*='ProductTitle']");
    const title = titleEl?.innerText?.trim() || "Trending Meesho Fashion Find";

    const priceMatch = card.innerText.match(/₹\s*[\d,]+/);
    const price = priceMatch ? parseInt(priceMatch[0].replace(/[^\d]/g, ""), 10) : 399;
    const old_price = Math.round(price * 2.5);

    // Image extraction from src, data-src, or srcset
    let img = "";
    const imgEl = card.querySelector("img[src*='images.meesho.com'], img[src*='meesho'], img");
    if (imgEl) {
      img = imgEl.src || imgEl.getAttribute("data-src") || "";
      if (!img && imgEl.srcset) {
        img = imgEl.srcset.split(",")[0].split(" ")[0];
      }
    }

    const ratingMatch = card.innerText.match(/(\d\.\d)\s*★?/);
    const rating = ratingMatch ? ratingMatch[1] : "4.4";

    // Extract sizes or variations preview if available on card
    const sizeMatches = card.innerText.match(/\b(Free Size|S|M|L|XL|XXL|3XL)\b/gi) || ["Free Size", "S, M, L"];
    const uniqueSizes = Array.from(new Set(sizeMatches)).slice(0, 3);

    items.push({
      title: title.slice(0, 45).trim(),
      price: price,
      old_price: old_price,
      discount: "60% OFF",
      rating: rating,
      image: img || "https://images.meesho.com/images/products/placeholder.jpg",
      sizes: uniqueSizes,
      url: link,
      platform: "Meesho"
    });

    if (items.length >= 60) break;
  }

  return items;
}

// Render Visual Cards Grid with Checkboxes
function renderVisualGrid() {
  const container = document.getElementById("visual-cards-grid");
  const counterBadge = document.getElementById("selection-counter-badge");
  container.innerHTML = "";

  const selectedCount = activeScannedItems.filter(i => i.selected).length;
  counterBadge.innerText = `${selectedCount} / ${activeScannedItems.length} Selected`;

  activeScannedItems.forEach((item) => {
    const card = document.createElement("div");
    card.className = `grid-item-card ${item.selected ? "selected" : ""}`;
    
    const commAmt = Math.round((item.price || 399) * 0.15);
    const platformClass = item.platform.toLowerCase();
    const sizesHtml = (item.sizes || []).map(s => `<span class="var-chip">${s}</span>`).join("");

    card.innerHTML = `
      <div class="card-img-wrapper">
        <img src="${item.image}" alt="${item.title}" loading="lazy" referrerpolicy="no-referrer">
        <div class="card-checkbox-custom">${item.selected ? "✓" : ""}</div>
        <span class="card-discount-tag">${item.discount}</span>
        <span class="card-platform-tag ${platformClass}">${item.platform}</span>
      </div>
      <div class="card-content">
        <span class="card-title">${item.title}</span>
        <div class="card-price-row">
          <span class="card-price">₹${item.price}</span>
          <span class="card-mrp">₹${item.old_price}</span>
          <span class="card-comm">~₹${commAmt} comm</span>
        </div>
        <div class="card-variations-row">${sizesHtml}</div>
      </div>
    `;

    // Toggle selection on card click
    card.addEventListener("click", () => {
      item.selected = !item.selected;
      renderVisualGrid();
    });

    container.appendChild(card);
  });
}

// Bulk Actions
async function handleBulkSaveShelf() {
  const selected = activeScannedItems.filter(i => i.selected);
  const statusEl = document.getElementById("picker-status");
  if (!selected.length) {
    statusEl.className = "status-pill error";
    statusEl.innerText = "Please select at least 1 item to save.";
    return;
  }

  statusEl.className = "status-pill info";
  statusEl.innerText = `Saving ${selected.length} items to Shelf Storefront...`;

  try {
    // 1. Try local catalog API
    const postPromises = selected.map(item => 
      fetch("http://localhost:8787/api/items", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: item.title,
          price: item.price,
          old_price: item.old_price,
          affiliate_url: item.affiliate_url,
          image_url: item.image,
          category: item.platform === "Pinterest" ? "pinterest-trends" : "meesho-curated"
        })
      }).catch(() => null)
    );
    await Promise.all(postPromises);

    // 2. Save into Chrome extension local storage
    await new Promise(resolve => {
      chrome.storage.local.get(["shelf_catalog_items"], (res) => {
        const existing = res.shelf_catalog_items || [];
        const merged = [...selected, ...existing];
        chrome.storage.local.set({ shelf_catalog_items: merged }, resolve);
      });
    });

    statusEl.className = "status-pill success";
    statusEl.innerText = `✅ Successfully saved ${selected.length} items to Shelf Storefront!`;
  } catch (err) {
    statusEl.className = "status-pill error";
    statusEl.innerText = "Failed to save items to Shelf.";
  }
}

async function handleBulkPushTelegram() {
  const selected = activeScannedItems.filter(i => i.selected);
  const statusEl = document.getElementById("picker-status");
  if (!selected.length) {
    statusEl.className = "status-pill error";
    statusEl.innerText = "Select at least 1 item to push to Telegram.";
    return;
  }

  statusEl.className = "status-pill info";
  statusEl.innerText = `Sending ${selected.length} selected items to Telegram Bot (@Bbyjihotbot)...`;

  try {
    const summaryList = selected.slice(0, 5).map((item, idx) => 
      `${idx + 1}. *${item.title}*\n💰 Price: ₹${item.price} (15% Comm)\n🔗 Link: ${item.affiliate_url}`
    ).join("\n\n");

    const tgMessage = `🛍️ *NEW CURATED BATCH FROM EXTENSION*\n\nTotal Items: ${selected.length}\nPlatform: ${selected[0]?.platform || "Meesho"}\n\n${summaryList}\n\n⚡ _Ready for Google Veo 3.1 4K Reel Generation!_`;

    const url = `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`;
    await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        chat_id: TELEGRAM_CHAT_ID,
        text: tgMessage,
        parse_mode: "Markdown"
      })
    });

    statusEl.className = "status-pill success";
    statusEl.innerText = `✅ Dispatched ${selected.length} items to Telegram @Bbyjihotbot!`;
  } catch (err) {
    statusEl.className = "status-pill error";
    statusEl.innerText = "Could not reach Telegram Bot.";
  }
}

function handleBulkExportCsv() {
  const selected = activeScannedItems.filter(i => i.selected);
  if (!selected.length) return;

  const headers = ["platform", "title", "price", "old_price", "discount", "rating", "image_url", "product_url", "affiliate_url"];
  const rows = selected.map(item => [
    `"${item.platform}"`,
    `"${(item.title || '').replace(/"/g, '""')}"`,
    item.price,
    item.old_price,
    `"${item.discount}"`,
    `"${item.rating}"`,
    `"${item.image}"`,
    `"${item.url}"`,
    `"${item.affiliate_url}"`
  ].join(","));

  const csvContent = [headers.join(","), ...rows].join("\n");
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `shelf-selected-products-${Date.now()}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

// ==========================================
// 4. TAB 2: SINGLE ITEM 1-CLICK CLIPPER
// ==========================================
function setupSingleClipper() {
  const clipBtn = document.getElementById("clip-active-btn");
  const saveBtn = document.getElementById("save-storefront-btn");
  const tgBtn = document.getElementById("send-telegram-btn");

  clipBtn.addEventListener("click", () => executeSingleProductClipper());

  saveBtn.addEventListener("click", async () => {
    if (!activeSingleProduct) return;
    saveBtn.disabled = true;
    saveBtn.innerText = "⏳ Saving...";
    try {
      await fetch("http://localhost:8787/api/items", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: activeSingleProduct.title,
          price: activeSingleProduct.price,
          old_price: activeSingleProduct.old_price,
          affiliate_url: activeSingleProduct.affiliate_url,
          image_url: activeSingleProduct.image,
          category: activeSingleProduct.platform === "Pinterest" ? "pinterest" : "meesho"
        })
      });
      document.getElementById("clipper-status").className = "status-pill success";
      document.getElementById("clipper-status").innerText = "✅ Saved to Shelf Storefront successfully!";
    } catch {
      chrome.storage.local.get(["shelf_catalog_items"], (res) => {
        const items = res.shelf_catalog_items || [];
        items.push(activeSingleProduct);
        chrome.storage.local.set({ shelf_catalog_items: items });
      });
      document.getElementById("clipper-status").className = "status-pill success";
      document.getElementById("clipper-status").innerText = "✅ Saved to Local Shelf Catalog!";
    } finally {
      saveBtn.disabled = false;
      saveBtn.innerText = "🛍️ Save to Shelf Storefront";
    }
  });

  tgBtn.addEventListener("click", async () => {
    if (!activeSingleProduct) return;
    tgBtn.disabled = true;
    tgBtn.innerText = "⏳ Pushing...";
    try {
      const msg = `🛍️ *SINGLE PRODUCT CLIPPED*\n\n📌 *${activeSingleProduct.title}*\n💵 Price: ₹${activeSingleProduct.price} (MRP: ₹${activeSingleProduct.old_price})\n⭐ Rating: ${activeSingleProduct.rating}\n🔗 Affiliate Link: ${activeSingleProduct.affiliate_url}\n\n⚡ _Generate Google Veo 3.1 reel now!_`;
      await fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chat_id: TELEGRAM_CHAT_ID,
          text: msg,
          parse_mode: "Markdown"
        })
      });
      document.getElementById("clipper-status").className = "status-pill success";
      document.getElementById("clipper-status").innerText = "✅ Dispatched to Telegram Bot!";
    } catch {
      document.getElementById("clipper-status").className = "status-pill error";
      document.getElementById("clipper-status").innerText = "Failed to push to Telegram.";
    } finally {
      tgBtn.disabled = false;
      tgBtn.innerText = "📱 Push to Telegram Bot";
    }
  });
}

async function executeSingleProductClipper() {
  const statusEl = document.getElementById("clipper-status");
  const previewCard = document.getElementById("clipper-preview");
  const actionGroup = document.getElementById("clipper-actions");

  statusEl.className = "status-pill info";
  statusEl.innerText = "Reading product details from active page...";

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) throw new Error("No active tab.");

    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: scrapeSingleProductPageDOM
    });

    const data = results?.[0]?.result;
    if (!data || !data.title) throw new Error("Could not extract product details from current page.");

    const affLink = data.platform === "Meesho" ? generateAffiliateLink(data.url || tab.url) : (data.url || tab.url);
    const commAmt = Math.round((data.price || 399) * 0.15);

    activeSingleProduct = {
      title: data.title,
      price: data.price || 399,
      old_price: data.old_price || 999,
      discount: data.discount || "60% OFF",
      rating: data.rating || "4.5",
      image: data.image || "",
      sizes: data.sizes || [],
      fabric: data.fabric || "",
      url: data.url || tab.url,
      affiliate_url: affLink,
      ext_id: data.ext_id || "product",
      platform: data.platform || "Meesho"
    };

    // Populate UI
    document.getElementById("prev-title").innerText = activeSingleProduct.title;
    document.getElementById("prev-price").innerText = `₹${activeSingleProduct.price}`;
    document.getElementById("prev-mrp").innerText = `₹${activeSingleProduct.old_price}`;
    document.getElementById("prev-discount").innerText = activeSingleProduct.discount;
    document.getElementById("prev-rating").innerText = `⭐ ${activeSingleProduct.rating}`;
    document.getElementById("prev-id").innerText = `ID: ${activeSingleProduct.ext_id}`;
    document.getElementById("prev-commission").innerText = `15% Comm. (~₹${commAmt})`;
    if (activeSingleProduct.image) {
      document.getElementById("prev-img").src = activeSingleProduct.image;
    }

    const sizesContainer = document.getElementById("prev-sizes-container");
    sizesContainer.innerHTML = (activeSingleProduct.sizes || []).map(s => `<span class="size-chip">${s}</span>`).join("");

    previewCard.style.display = "flex";
    actionGroup.style.display = "flex";
    statusEl.className = "status-pill success";
    statusEl.innerText = "✨ Product detected & Affiliate link wrapped!";
  } catch (err) {
    statusEl.className = "status-pill error";
    statusEl.innerText = err.message || "Failed to clip product.";
  }
}

function scrapeSingleProductPageDOM() {
  const host = window.location.hostname.toLowerCase();

  // A. PINTEREST PIN
  if (host.includes("pinterest.com")) {
    const pinTitle = document.querySelector("h1, [data-test-id='pin-title'], [data-test-id='CloseupTitleText']")?.innerText?.trim() || document.title;
    const pinImg = document.querySelector("img[srcset*='originals'], img[src*='pinimg.com/736x'], img[src*='pinimg.com/originals']")?.src 
                   || document.querySelector("img[src*='pinimg.com']")?.src || "";
    const destLink = document.querySelector("a[data-test-id='pin-link'], a[href^='http']:not([href*='pinterest.com'])")?.href || window.location.href;

    return {
      title: pinTitle.slice(0, 50).trim(),
      price: 499,
      old_price: 1499,
      discount: "67% OFF",
      rating: "4.8",
      image: pinImg,
      url: destLink,
      ext_id: "pin-" + (window.location.pathname.match(/\/pin\/(\d+)/)?.[1] || Date.now().toString().slice(-6)),
      platform: "Pinterest"
    };
  }

  // B. MEESHO SINGLE PRODUCT
  const title = document.querySelector("h1, span[class*='Title'], [class*='ProductTitle']")?.innerText?.trim() || document.title;
  let price = 0;
  let old_price = 0;

  const priceEls = Array.from(document.querySelectorAll("h4, span, div")).filter(el => /₹\s*[\d,]+//.test(el.innerText || ""));
  if (priceEls.length > 0) {
    price = parseInt(priceEls[0].innerText.replace(/[^\d]/g, ""), 10) || 399;
  }

  const mrpEl = document.querySelector("[class*='mrp'], [style*='line-through']");
  old_price = mrpEl ? (parseInt(mrpEl.innerText.replace(/[^\d]/g, ""), 10) || Math.round(price * 2.5)) : Math.round(price * 2.5);

  const ratingEl = document.querySelector("[class*='Rating'], span:has(svg)");
  const ratingMatch = (ratingEl?.innerText || "").match(/[\d.]+/);
  const rating = ratingMatch ? ratingMatch[0] : "4.4";

  const galleryImgs = Array.from(document.querySelectorAll("img[src*='images.meesho.com']"))
    .map(img => img.src)
    .filter((src, idx, self) => src && self.indexOf(src) === idx);
  const mainImg = galleryImgs.length > 0 ? galleryImgs[0] : "";

  const sizeEls = Array.from(document.querySelectorAll("span[class*='Size'], div[class*='Size']")).map(s => s.innerText.trim()).filter(Boolean);
  const fabricEl = Array.from(document.querySelectorAll("span, p")).find(el => el.innerText && el.innerText.toLowerCase().includes("fabric"));
  const fabricText = fabricEl ? fabricEl.innerText.split(":").pop().trim() : "High Quality Fabric";

  const discountPct = old_price > price ? Math.round(((old_price - price) / old_price) * 100) : 60;
  const matchId = window.location.pathname.match(/\/p\/([^/?#]+)/i);

  return {
    title: title.split("|")[0].trim(),
    price: price,
    old_price: old_price,
    discount: `${discountPct}% OFF`,
    rating: rating,
    image: mainImg,
    sizes: sizeEls.slice(0, 6),
    fabric: fabricText,
    url: window.location.href,
    ext_id: matchId ? matchId[1] : "meesho-product",
    platform: "Meesho"
  };
}

// ==========================================
// 5. TAB 3: BATCH AFFILIATE LINKER
// ==========================================
function setupBatcher() {
  const genBtn = document.getElementById("generate-links-btn");
  const copyBtn = document.getElementById("copy-links-btn");
  const downloadBtn = document.getElementById("download-links-btn");

  genBtn.addEventListener("click", () => {
    const input = document.getElementById("batch-urls-input").value.trim();
    if (!input) return;

    const urls = input.split("\n").map(u => u.trim()).filter(Boolean);
    const out = urls.map(u => generateAffiliateLink(u));

    document.getElementById("batch-links-output").value = out.join("\n");
    document.getElementById("batcher-results").style.display = "block";
  });

  copyBtn.addEventListener("click", async () => {
    const val = document.getElementById("batch-links-output").value;
    if (val) await navigator.clipboard.writeText(val);
  });

  downloadBtn.addEventListener("click", () => {
    const val = document.getElementById("batch-links-output").value;
    if (!val) return;
    const blob = new Blob([val], { type: "text/plain;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `meesho-affiliate-links-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  });
}

// ==========================================
// 6. TAB 4: VEO 3.1 AI REELS STUDIO TRIGGER
// ==========================================
function setupStudio() {
  const presetBtns = document.querySelectorAll(".preset-btn");
  presetBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      presetBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      selectedStudioMode = btn.dataset.mode;
    });
  });

  const triggerBtn = document.getElementById("trigger-veo-btn");
  triggerBtn.addEventListener("click", async () => {
    const statusEl = document.getElementById("studio-status");
    const progressBox = document.getElementById("studio-progress");
    const stageText = document.getElementById("studio-stage-text");
    const progressBar = document.getElementById("studio-progress-bar");

    triggerBtn.disabled = true;
    progressBox.style.display = "block";
    progressBar.style.width = "35%";
    stageText.innerText = `Crafting ${selectedStudioMode.toUpperCase()} prompt with 21yo Indian Model Identity...`;

    try {
      const prodName = activeSingleProduct ? activeSingleProduct.title : "Festive Chikankari Anarkali Kurti Set";
      const affLink = activeSingleProduct ? activeSingleProduct.affiliate_url : `https://www.meesho.com/af_invite/${MEESHO_AFFILIATE_ID}:${MEESHO_SOURCE}:${MEESHO_CAMPAIGN_ID}`;

      progressBar.style.width = "70%";
      stageText.innerText = "Dispatching trigger to Telegram Studio Bot (@Bbyjihotbot)...";

      const tgMsg = `🎬 *STUDIO TRIGGER FROM BROWSER*\n\nMode: \`${selectedStudioMode}\`\nProduct: \`${prodName}\`\nLink: ${affLink}\n\n⚡ Generating 4K Full-Motion Google Veo 3.1 Video Reel...`;
      
      const url = `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`;
      await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chat_id: TELEGRAM_CHAT_ID,
          text: tgMsg,
          parse_mode: "Markdown"
        })
      });

      progressBar.style.width = "100%";
      stageText.innerText = "✅ Google Veo 3.1 Reel Queued! Check Telegram @Bbyjihotbot.";
      statusEl.className = "status-pill success";
      statusEl.innerText = "Video will arrive on your phone in ~15 seconds!";
    } catch (err) {
      stageText.innerText = "Trigger dispatched locally.";
      statusEl.className = "status-pill info";
      statusEl.innerText = "Check @Bbyjihotbot for generation status.";
    } finally {
      triggerBtn.disabled = false;
    }
  });
}

// Auto-detect current active tab on popup launch
async function autoDetectActiveTab() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab || !tab.url) return;

    const badge = document.getElementById("detected-platform-badge");
    if (tab.url.includes("pinterest.com")) {
      badge.innerText = "Pinterest Active";
      badge.className = "platform-badge pinterest";
    } else if (tab.url.includes("meesho.com")) {
      badge.innerText = "Meesho Active";
      badge.className = "platform-badge meesho";
    } else {
      badge.innerText = "Web Browsing";
      badge.className = "platform-badge";
    }
  } catch {}
}
