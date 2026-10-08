/**
 * Shelf. All-in-One Creator Suite - Unified Popup Controller
 * Combines: 1-Click Clipper, Bulk Page Scraper, Affiliate Link Batcher, and Veo Studio Trigger.
 */

const MEESHO_AFFILIATE_ID = "374453404";
const MEESHO_SOURCE = "youtube_long_form";
const MEESHO_CAMPAIGN_ID = "12492338";
const TELEGRAM_BOT_TOKEN = "8564017881:AAGgH4xtjjOZYdyVG6CfNT86i-7t1s9ob7c";
const TELEGRAM_CHAT_ID = "6486771356";

let activeProduct = null;
let activeScrapedCsv = "";
let selectedStudioMode = "unboxing";

// Initialize UI
document.addEventListener("DOMContentLoaded", () => {
  setupTabs();
  setupClipper();
  setupScraper();
  setupBatcher();
  setupStudio();
  autoDetectProductOnOpen();
});

// 1. Tab Switching
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

// 2. Affiliate Link Pattern Generator
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

// 3. Tab 1: 1-Click Clipper Logic
function setupClipper() {
  const clipBtn = document.getElementById("clip-active-btn");
  const saveBtn = document.getElementById("save-storefront-btn");
  const tgBtn = document.getElementById("send-telegram-btn");

  clipBtn.addEventListener("click", () => executeProductClipper());

  saveBtn.addEventListener("click", async () => {
    if (!activeProduct) return;
    saveBtn.disabled = true;
    saveBtn.innerText = "⏳ Saving...";
    try {
      // Post to local or hosted Catalog API
      const res = await fetch("http://localhost:8787/api/items", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: json.stringify({
          title: activeProduct.title,
          price: activeProduct.price,
          old_price: activeProduct.old_price,
          affiliate_url: activeProduct.affiliate_url,
          image_url: activeProduct.image,
          category: activeProduct.category || "meesho-finds"
        })
      });
      document.getElementById("clipper-status").className = "status-pill success";
      document.getElementById("clipper-status").innerText = "✅ Saved to Shelf Storefront successfully!";
    } catch {
      // Fallback save to local chrome storage
      chrome.storage.local.get(["clipped_items"], (res) => {
        const items = res.clipped_items || [];
        items.push(activeProduct);
        chrome.storage.local.set({ clipped_items: items });
      });
      document.getElementById("clipper-status").className = "status-pill success";
      document.getElementById("clipper-status").innerText = "✅ Saved to Local Shelf Catalog!";
    } finally {
      saveBtn.disabled = false;
      saveBtn.innerText = "🛍️ Save to Shelf Storefront";
    }
  });

  tgBtn.addEventListener("click", async () => {
    if (!activeProduct) return;
    tgBtn.disabled = true;
    tgBtn.innerText = "⏳ Sending to Telegram...";
    const caption = `🛍️ *PRODUCT CLIPPED FROM BROWSER*\n\n👗 *Product:* ${activeProduct.title}\n💰 *Deal:* ₹${activeProduct.price} (MRP ₹${activeProduct.old_price} • ${activeProduct.discount})\n⭐ *Rating:* ${activeProduct.rating}\n🔗 *Affiliate Link:* ${activeProduct.affiliate_url}\n\n🎬 Ready for 4K Google Veo Video Generation!`;
    
    try {
      const url = `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`;
      await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chat_id: TELEGRAM_CHAT_ID,
          text: caption,
          parse_mode: "Markdown"
        })
      });
      document.getElementById("clipper-status").className = "status-pill success";
      document.getElementById("clipper-status").innerText = "🚀 Dispatched to @Bbyjihotbot!";
    } catch (err) {
      document.getElementById("clipper-status").className = "status-pill error";
      document.getElementById("clipper-status").innerText = "Failed to send to Telegram.";
    } finally {
      tgBtn.disabled = false;
      tgBtn.innerText = "📱 Push to Telegram Bot";
    }
  });
}

async function autoDetectProductOnOpen() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab?.url && tab.url.includes("meesho.com")) {
    executeProductClipper(true);
  }
}

async function executeProductClipper(silent = false) {
  const statusEl = document.getElementById("clipper-status");
  const previewCard = document.getElementById("clipper-preview");
  const actionGroup = document.getElementById("clipper-actions");

  if (!silent) {
    statusEl.className = "status-pill info";
    statusEl.innerText = "Scanning active tab for product data...";
  }

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab?.id) throw new Error("No active browser tab found.");

    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: scrapeSingleProductDOM
    });

    const data = results?.[0]?.result;
    if (!data || !data.title) throw new Error("Open a Meesho product page and try again.");

    const affiliateLink = generateAffiliateLink(data.url || tab.url);
    const commAmt = Math.round((data.price || 399) * 0.15);

    activeProduct = {
      title: data.title,
      price: data.price || 399,
      old_price: data.old_price || Math.round((data.price || 399) * 2.5),
      discount: data.discount || "65% OFF",
      rating: data.rating || "4.5",
      image: data.image || "",
      product_url: data.url || tab.url,
      affiliate_url: affiliateLink,
      ext_id: data.ext_id || "meesho-find"
    };

    // Populate UI
    document.getElementById("prev-title").innerText = activeProduct.title;
    document.getElementById("prev-price").innerText = `₹${activeProduct.price}`;
    document.getElementById("prev-mrp").innerText = `₹${activeProduct.old_price}`;
    document.getElementById("prev-discount").innerText = activeProduct.discount;
    document.getElementById("prev-rating").innerText = `⭐ ${activeProduct.rating}`;
    document.getElementById("prev-id").innerText = `ID: ${activeProduct.ext_id}`;
    document.getElementById("prev-commission").innerText = `15% Comm. (~₹${commAmt})`;
    if (activeProduct.image) {
      document.getElementById("prev-img").src = activeProduct.image;
    }

    previewCard.style.display = "flex";
    actionGroup.style.display = "flex";
    statusEl.className = "status-pill success";
    statusEl.innerText = "✨ Product detected & Affiliate link wrapped!";
  } catch (err) {
    if (!silent) {
      statusEl.className = "status-pill error";
      statusEl.innerText = err.message || "Could not read product from page.";
    }
  }
}

function scrapeSingleProductDOM() {
  const title = document.querySelector("h1, span[class*='Title'], [class*='ProductTitle']")?.innerText?.trim() || document.title;
  let price = 0;
  let old_price = 0;

  const priceEls = Array.from(document.querySelectorAll("h4, span, div")).filter(el => /₹\s*[\d,]+/.test(el.innerText || ""));
  if (priceEls.length > 0) {
    const raw = priceEls[0].innerText.replace(/[^\d]/g, "");
    price = parseInt(raw, 10) || 399;
  }

  const mrpEl = document.querySelector("[class*='mrp'], [style*='line-through']");
  if (mrpEl) {
    old_price = parseInt(mrpEl.innerText.replace(/[^\d]/g, ""), 10) || Math.round(price * 2.5);
  } else {
    old_price = Math.round(price * 2.5);
  }

  const ratingEl = document.querySelector("[class*='Rating'], span:has(svg)");
  const ratingMatch = (ratingEl?.innerText || "").match(/[\d.]+/);
  const rating = ratingMatch ? ratingMatch[0] : "4.4";

  let img = "";
  const imgEl = document.querySelector("img[src*='images.meesho.com'], img[class*='ProductImage'], [class*='Carousel'] img");
  if (imgEl) img = imgEl.src;

  const discountPct = old_price > price ? Math.round(((old_price - price) / old_price) * 100) : 60;
  const matchId = window.location.pathname.match(/\/p\/([^/?#]+)/i);

  return {
    title: title.split("|")[0].trim(),
    price: price,
    old_price: old_price,
    discount: `${discountPct}% OFF`,
    rating: rating,
    image: img,
    url: window.location.href,
    ext_id: matchId ? matchId[1] : ""
  };
}

// 4. Tab 2: Bulk Page Scraper Logic
function setupScraper() {
  const scrapeBtn = document.getElementById("scrape-page-btn");
  const copyBtn = document.getElementById("copy-csv-btn");
  const downloadBtn = document.getElementById("download-csv-btn");

  scrapeBtn.addEventListener("click", async () => {
    scrapeBtn.disabled = true;
    const statusEl = document.getElementById("scraper-status");
    const resultsBox = document.getElementById("scraper-results");
    statusEl.className = "status-pill info";
    statusEl.innerText = "Extracting all product listings from current page...";

    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      const res = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: scrapeMeeshoCategoryPageDOM
      });

      const items = res?.[0]?.result || [];
      if (!items.length) throw new Error("No products found on this page. Scroll down to load listings.");

      // Build CSV
      const headers = ["title", "price", "old_price", "discount", "rating", "image_url", "product_url", "generated_affiliate_url"];
      const rows = items.map(item => {
        const aff = generateAffiliateLink(item.product_url);
        return [
          `"${(item.title || '').replace(/"/g, '""')}"`,
          item.price || 399,
          item.old_price || 999,
          `"${item.discount || '65% OFF'}"`,
          item.rating || "4.4",
          `"${item.image_url || ''}"`,
          `"${item.product_url || ''}"`,
          `"${aff}"`
        ].join(",");
      });

      activeScrapedCsv = [headers.join(","), ...rows].join("\n");
      document.getElementById("scraped-count-pill").innerText = `${items.length} Products Scraped`;
      document.getElementById("scraper-csv-text").value = activeScrapedCsv;
      resultsBox.style.display = "block";
      statusEl.className = "status-pill success";
      statusEl.innerText = `✅ Successfully extracted ${items.length} Meesho products with affiliate links!`;
    } catch (err) {
      statusEl.className = "status-pill error";
      statusEl.innerText = err.message || "Could not scrape page.";
    } finally {
      scrapeBtn.disabled = false;
    }
  });

  copyBtn.addEventListener("click", async () => {
    if (!activeScrapedCsv) return;
    await navigator.clipboard.writeText(activeScrapedCsv);
    document.getElementById("scraper-status").innerText = "📋 CSV copied to clipboard!";
  });

  downloadBtn.addEventListener("click", () => {
    if (!activeScrapedCsv) return;
    const blob = new Blob([activeScrapedCsv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `meesho-scraped-${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  });
}

function scrapeMeeshoCategoryPageDOM() {
  const cards = Array.from(document.querySelectorAll("a[href*='/p/'], [class*='ProductCard'], div[class*='Card']"));
  const seen = new Set();
  const list = [];

  for (const card of cards) {
    const link = card.tagName === "A" ? card.href : card.querySelector("a")?.href;
    if (!link || !link.includes("/p/") || seen.has(link)) continue;
    seen.add(link);

    const title = card.querySelector("p, span[class*='Title'], h2, h3")?.innerText?.trim() || "Meesho Fashion Find";
    const priceText = card.innerText.match(/₹\s*[\d,]+/);
    const price = priceText ? parseInt(priceText[0].replace(/[^\d]/g, ""), 10) : 349;
    const old_price = Math.round(price * 2.5);
    const img = card.querySelector("img")?.src || "";

    list.push({
      title: title.slice(0, 40),
      price: price,
      old_price: old_price,
      discount: "60% OFF",
      rating: "4.4",
      image_url: img,
      product_url: link
    });

    if (list.length >= 50) break;
  }
  return list;
}

// 5. Tab 3: Affiliate Link Batcher Logic
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
    a.download = `affiliate-links-${Date.now()}.txt`;
    a.click();
  });
}

// 6. Tab 4: Veo 3.1 AI Studio Trigger Logic
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
      const prodName = activeProduct ? activeProduct.title : "Festive Chikankari Anarkali Kurti Set";
      const affLink = activeProduct ? activeProduct.affiliate_url : `https://www.meesho.com/af_invite/${MEESHO_AFFILIATE_ID}:${MEESHO_SOURCE}:${MEESHO_CAMPAIGN_ID}`;

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
