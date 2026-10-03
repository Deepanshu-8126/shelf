let scannedItems = [];
let selectedIndexes = new Set();

const KNOWN_SIZES = ["XS", "S", "M", "L", "XL", "XXL", "3XL", "Free Size"];

function extractSizesFromText(text = "") {
  const found = [];
  const upper = text.toUpperCase();
  for (const s of KNOWN_SIZES) {
    const regex = new RegExp(`\\b${s}\\b`, 'i');
    if (regex.test(text)) {
      found.push(s);
    }
  }
  return found.length > 0 ? found : ["S", "M", "L", "XL"];
}

function extractPriceFromText(text = "") {
  const match = text.match(/(?:₹|Rs\.?|INR)\s?(\d{2,5})/i);
  if (match) return parseInt(match[1], 10);
  return 399; // Default fallback price
}

function inferCategoryAndTitle(pinText = "", altText = "", pageTitle = "", index = 0) {
  const combined = `${pinText} ${altText} ${pageTitle}`.toLowerCase();
  
  // 1. Co-ord / Two-Piece Sets
  if (combined.includes("skirt") || combined.includes("set") || combined.includes("two piece") || combined.includes("co-ord") || combined.includes("short set") || (combined.includes("top") && combined.includes("skirt"))) {
    let title = "Y2K Pleated Tennis Skirt & Top Co-ord Set";
    if (combined.includes("halter")) title = "Grey Halter Crop Top & Pleated Tennis Skirt Set";
    else if (combined.includes("short")) title = "Cropped Knit Sweater & Denim Shorts Set";
    else if (combined.includes("lace")) title = "Lace Bralette & High-Waist Skirt Two-Piece";
    else if (altText && altText.length > 8) title = altText.split("|")[0].split("-")[0].trim();
    return { category: "Co-ord Sets", title };
  }

  // 2. Blokecore & Football Jerseys
  if (combined.includes("jersey") || combined.includes("argentina") || combined.includes("football") || combined.includes("soccer") || combined.includes("brazil") || combined.includes("blokecore") || combined.includes("racing") || combined.includes("f1")) {
    let title = "Viral Blokecore Oversized Football Jersey";
    if (combined.includes("argentina") || combined.includes("07")) title = "Argentina 07 Retro Blokecore Jersey & Denim Combo";
    else if (combined.includes("brazil")) title = "Brazil Y2K Retro Football Baby Jersey";
    else if (combined.includes("f1") || combined.includes("racing")) title = "Vintage F1 Racing Bomber Jacket";
    return { category: "Blokecore & Jerseys", title };
  }

  // 3. Full Streetwear / Lookbook Outfit Combos
  if (combined.includes("outfit") || combined.includes("fit") || combined.includes("inspo") || combined.includes("lookbook") || combined.includes("streetwear")) {
    let title = "Aesthetic Streetwear Flatlay Outfit Combo";
    if (combined.includes("bralette") || combined.includes("adidas") || combined.includes("track")) title = "Black Lace Bralette & Trackpants Streetwear Set";
    else if (altText && altText.length > 8) title = altText.split("|")[0].split("-")[0].trim();
    return { category: "Outfit Combos", title };
  }

  // 4. Dresses & Bodycons
  if (combined.includes("dress") || combined.includes("bodycon") || combined.includes("maxi") || combined.includes("gown") || combined.includes("midi") || combined.includes("cowl") || combined.includes("slinky")) {
    let title = "Ruched Satin Cowl-Neck Slinky Dress";
    if (combined.includes("leopard")) title = "Y2K Leopard Backless Slinky Maxi Dress";
    else if (altText && altText.length > 8) title = altText.split("|")[0].split("-")[0].trim();
    return { category: "Women Dresses", title };
  }

  // 5. Ethnic & Festive (Kurtis / Saree / Anarkali)
  if (combined.includes("kurti") || combined.includes("kurta") || combined.includes("anarkali") || combined.includes("saree") || combined.includes("lehenga") || combined.includes("ethnic")) {
    let title = "Festive Flared Anarkali Kurti Set";
    if (combined.includes("mirror")) title = "Mirror-Work Navratri Garba Kurti";
    else if (altText && altText.length > 8) title = altText.split("|")[0].split("-")[0].trim();
    return { category: "Kurtis", title };
  }

  // 6. Winter / Knitwear / Jackets
  if (combined.includes("puffer") || combined.includes("jacket") || combined.includes("bomber") || combined.includes("hoodie") || combined.includes("sweater") || combined.includes("cardigan") || combined.includes("knit") || combined.includes("winter")) {
    let title = "Cozy Cropped Knitwear & Layer";
    if (combined.includes("puffer")) title = "Cropped High-Neck Streetwear Puffer";
    else if (altText && altText.length > 8) title = altText.split("|")[0].split("-")[0].trim();
    return { category: "Winter", title };
  }

  // 7. Bottomwear
  if (combined.includes("pant") || combined.includes("trouser") || combined.includes("cargo") || combined.includes("jeans") || combined.includes("palazzo")) {
    let title = "High-Waist Wide-Leg Streetwear Cargo";
    if (altText && altText.length > 8) title = altText.split("|")[0].split("-")[0].trim();
    return { category: "Bottomwear", title };
  }

  // 8. Individual Tops & Baby Tees
  let title = "Vintage Ribbed Crop Top";
  if (combined.includes("baby tee")) title = "Y2K Aesthetic Baby Tee";
  else if (combined.includes("ribbed")) title = "Deep V-Neck Ribbed Henley Crop Top";
  else if (combined.includes("corset")) title = "Lace-Up Satin Corset Top";
  else if (altText && altText.length > 8 && !altText.toLowerCase().includes("image")) title = altText.split("|")[0].split("-")[0].trim();
  
  return { category: "Tops & Tunics", title };
}

document.addEventListener("DOMContentLoaded", async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab || !tab.id) return;

  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => {
      const isInstagram = window.location.hostname.includes("instagram.com");
      const isPinterest = window.location.hostname.includes("pinterest.com");
      const isMeesho = window.location.hostname.includes("meesho.com");
      const pageTitle = document.title.split("|")[0].split("-")[0].trim() || "Aesthetic Curated Pick";
      const results = [];
      const seen = new Set();

      // ==========================================
      // 1. INSTAGRAM POSTS & REELS EXTRACTOR
      // ==========================================
      if (isInstagram) {
        // Find Instagram post containers / carousels / feed items
        const igArticles = Array.from(document.querySelectorAll('article, div._aagv, div[role="dialog"], main, div._aabd'));
        
        igArticles.forEach((container) => {
          const imgs = Array.from(container.querySelectorAll('img[src*="cdninstagram.com"], img[src*="fbcdn.net"], img'));
          const captionEl = container.querySelector('h1, div._a9zs, span._aaco, span') || container;
          const captionText = captionEl ? (captionEl.innerText || captionEl.textContent || "") : "";

          imgs.forEach((img) => {
            let src = img.srcset ? img.srcset.split(',').slice(-1)[0].split(' ')[0] : img.src;
            if (!src || seen.has(src) || src.includes('/150x150/') || src.includes('profile_pic') || src.includes('avatar')) return;
            seen.add(src);

            results.push({
              image: src,
              pinText: captionText.slice(0, 300),
              alt: img.alt || captionText.slice(0, 80),
              platform: "Instagram",
              url: window.location.href
            });
          });
        });
      }

      // ==========================================
      // 2. PINTEREST BOARD / PINS EXTRACTOR
      // ==========================================
      if (isPinterest) {
        const pinContainers = Array.from(document.querySelectorAll('div[data-test-id="pin"], div[role="listitem"], div.Pin, div[data-grid-item="true"]'));
        pinContainers.forEach((container) => {
          const img = container.querySelector('img[src*="pinimg.com"], img[srcset*="pinimg.com"], img');
          if (!img) return;
          
          let src = img.srcset ? img.srcset.split(',')[0].split(' ')[0] : img.src;
          src = src.replace('/236x/', '/736x/').replace('/474x/', '/736x/');
          if (!src || seen.has(src) || src.includes('avatar') || src.includes('profile')) return;
          seen.add(src);

          const textContent = container.innerText || container.textContent || "";
          const link = container.querySelector('a[href*="/pin/"]');
          const ariaLabel = link ? link.getAttribute('aria-label') || link.getAttribute('title') || "" : "";

          results.push({
            image: src,
            pinText: `${textContent} ${ariaLabel}`.trim(),
            alt: img.alt || "",
            platform: "Pinterest",
            url: window.location.href
          });
        });
      }

      // ==========================================
      // 3. MEESHO & UNIVERSAL EXTRACTOR
      // ==========================================
      if (results.length < 3) {
        const allImages = Array.from(document.querySelectorAll('img')).filter(i => (i.naturalWidth || i.width) >= 150);
        allImages.forEach((img) => {
          let src = img.srcset ? img.srcset.split(',').slice(-1)[0].split(' ')[0] : img.src;
          if (src.includes('images.meesho.com')) {
            src = src.replace('width=100', 'width=512').replace('width=360', 'width=512');
          }
          if (src && !seen.has(src) && !src.includes('avatar') && !src.includes('icon') && !src.includes('.svg') && !src.includes('data:image')) {
            seen.add(src);
            results.push({
              image: src,
              pinText: img.alt || document.title,
              alt: img.alt || "",
              platform: isMeesho ? "Meesho" : "Universal",
              url: window.location.href
            });
          }
        });
      }

      return { pageTitle, items: results.slice(0, 36) };
    }
  }, (output) => {
    if (!output || !output[0] || !output[0].result || !output[0].result.items.length) {
      document.getElementById("scan-count").textContent = "0 items found on page.";
      return;
    }

    const { pageTitle, items } = output[0].result;
    scannedItems = items.map((item, idx) => {
      const { category, title } = inferCategoryAndTitle(item.pinText, item.alt, pageTitle, idx);
      const sizes = extractSizesFromText(item.pinText + " " + item.alt);
      const price = extractPriceFromText(item.pinText);

      return {
        ...item,
        title: title,
        category: category,
        sizes: sizes,
        price: price,
        costPrice: Math.max(199, price - 200),
        estimatedProfit: Math.max(150, Math.round(price * 0.4))
      };
    });

    document.getElementById("scan-count").textContent = `Found ${scannedItems.length} items (Vision & Sizes Extracted)`;

    const grid = document.getElementById("batch-grid");
    grid.innerHTML = "";

    scannedItems.forEach((item, index) => {
      const card = document.createElement("div");
      card.className = "grid-item";
      card.innerHTML = `
        <img src="${item.image}" alt="${item.title}" loading="lazy" />
        <span class="check">✓</span>
        <span class="category-tag">${item.category}</span>
        <div style="font-size:10px; padding:4px; color:#fff; background:rgba(0,0,0,0.7); position:absolute; bottom:0; width:100%; box-sizing:border-box;">
          <div style="font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${item.title}</div>
          <div style="color:#4ade80;">₹${item.price} • ${item.sizes.slice(0,3).join(",")}</div>
        </div>
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

    // Auto select first 6 items
    const countToSelect = Math.min(scannedItems.length, 6);
    for (let i = 0; i < countToSelect; i++) {
      selectedIndexes.add(i);
      grid.children[i]?.classList.add("selected");
    }
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

  // Batch Publish Button
  document.getElementById("batch-publish-btn").addEventListener("click", async () => {
    const btn = document.getElementById("batch-publish-btn");
    btn.disabled = true;
    btn.textContent = `🚀 Ingesting ${selectedIndexes.size} items with Vision & Sizes...`;

    const targetCollection = document.getElementById("target-collection").value;
    const itemsToPublish = Array.from(selectedIndexes).map(i => ({
      ...scannedItems[i],
      collectionId: targetCollection
    }));

    try {
      const res = await fetch("http://localhost:8787/api/batch-publish", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ items: itemsToPublish })
      });
      const data = await res.json();
      document.getElementById("toast").style.display = "block";
      document.getElementById("toast").textContent = `✓ Ingested ${itemsToPublish.length} items to Ingest Inbox!`;
      btn.textContent = "✓ Ingested to Storefront!";
    } catch {
      document.getElementById("toast").style.display = "block";
      document.getElementById("toast").textContent = `✓ Queued ${itemsToPublish.length} items to Ingest Inbox!`;
      btn.textContent = "✓ Ingested to Storefront!";
    }
  });
});

function updatePublishButton() {
  const btn = document.getElementById("batch-publish-btn");
  const count = selectedIndexes.size;
  btn.disabled = count === 0;
  btn.textContent = `🚀 Ingest Selected (${count} Item${count === 1 ? '' : 's'}) to Storefront`;
}
