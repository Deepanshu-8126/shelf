const scanButton = document.getElementById('scan');
const statusNode = document.getElementById('status');
const resultNode = document.getElementById('result');
const summaryNode = document.getElementById('summary');
const csvNode = document.getElementById('csvText');
const copyButton = document.getElementById('copy');
const downloadButton = document.getElementById('download');
let currentCsv = '';
let currentFilename = 'meesho-listing.csv';

scanButton.addEventListener('click', async () => {
  scanButton.disabled = true;
  resultNode.hidden = true;
  statusNode.classList.remove('error');
  statusNode.textContent = 'Reading the current page…';
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab?.id || !tab.url) throw new Error('Could not find the active browser tab.');
    const host = new URL(tab.url).hostname.toLowerCase();
    if (host !== 'meesho.com' && !host.endsWith('.meesho.com')) {
      throw new Error('Open a Meesho product page first, then click Extract this page.');
    }
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: extractCurrentListing,
    });
    const listing = results?.[0]?.result;
    if (!listing?.title && !listing?.product_url) throw new Error('Could not identify a product listing on this page.');
    currentCsv = toCsv(listing);
    const safeId = listing.ext_id || new Date().toISOString().slice(0, 10);
    currentFilename = `meesho-${safeId}.csv`;
    csvNode.value = currentCsv;
    summaryNode.textContent = `${listing.title || 'Untitled listing'} · ₹${listing.price || 'price not found'} · ${listing.image_count} product image link${listing.image_count === 1 ? '' : 's'}${listing.ext_id ? ` · ID ${listing.ext_id}` : ' · ID not found'}`;
    resultNode.hidden = false;
    statusNode.textContent = listing.warning || 'CSV ready. Review the image URLs before importing.';
  } catch (error) {
    statusNode.classList.add('error');
    statusNode.textContent = error?.message || 'Could not read this page.';
  } finally {
    scanButton.disabled = false;
  }
});

copyButton.addEventListener('click', async () => {
  if (!currentCsv) return;
  try {
    await navigator.clipboard.writeText(currentCsv);
    statusNode.classList.remove('error');
    statusNode.textContent = 'CSV copied. Paste it into Import listings.';
  } catch {
    csvNode.focus();
    csvNode.select();
    const copied = document.execCommand('copy');
    statusNode.classList.toggle('error', !copied);
    statusNode.textContent = copied ? 'CSV copied. Paste it into Import listings.' : 'Select the CSV text above and copy it.';
  }
});

downloadButton.addEventListener('click', () => {
  if (!currentCsv) return;
  const blob = new Blob(['\uFEFF', currentCsv], { type: 'text/csv;charset=utf-8' });
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = objectUrl;
  anchor.download = currentFilename;
  anchor.click();
  URL.revokeObjectURL(objectUrl);
  statusNode.classList.remove('error');
  statusNode.textContent = `Downloaded ${currentFilename}.`;
});

function toCsv(listing) {
  const columns = [
    'title', 'price', 'old_price', 'discount', 'rating', 'rating_count', 'review_count',
    'category', 'subcategories', 'color', 'fabric', 'fit_shape', 'length', 'sizes', 'seller_name',
    'product_url', 'ext_id', 'image_url', 'gallery_image_urls', 'affiliate_url',
  ];
  const escape = (value) => `"${String(value ?? '').replaceAll('"', '""')}"`;
  return [columns.map(escape).join(','), columns.map((key) => escape(listing[key] ?? '')).join(',')].join('\r\n');
}

function extractCurrentListing() {
  const clean = (value) => String(value || '').replace(/\u00a0/g, ' ').replace(/\s+/g, ' ').trim();
  const normalise = (value) => clean(value).toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
  const visibleText = document.body?.innerText || '';
  const lowerText = visibleText.toLowerCase();
  const contentStops = ['real images and videos from customers', 'people also viewed'];
  const stopPositions = contentStops.map((marker) => lowerText.indexOf(marker)).filter((index) => index >= 0);
  const stopIndex = stopPositions.length ? Math.min(...stopPositions) : -1;
  const mainText = stopIndex >= 0 ? visibleText.slice(0, stopIndex) : visibleText;
  const lines = mainText.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);

  const visible = (element) => {
    if (!element) return false;
    const style = window.getComputedStyle(element);
    const rect = element.getBoundingClientRect();
    return style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0 && rect.height > 0;
  };
  const heading = Array.from(document.querySelectorAll('h1'))
    .find(visible);
  let title = clean(heading?.innerText || document.title.split(/[|–—]/)[0]);
  const priceMatch = /₹\s*([\d,]+)/.exec(mainText);
  if (!title && priceMatch) title = clean(mainText.slice(0, priceMatch.index));
  if (title) {
    const titleParts = title.split(/\s+/);
    if (titleParts.length % 2 === 0) {
      const half = titleParts.length / 2;
      if (titleParts.slice(0, half).join(' ').toLowerCase() === titleParts.slice(half).join(' ').toLowerCase()) title = titleParts.slice(0, half).join(' ');
    }
  }

  const productUrl = location.href;
  let extId = '';
  try {
    const url = new URL(productUrl);
    extId = url.searchParams.get('ext_id') || '';
    if (!extId) extId = url.pathname.match(/(?:^|\/)p\/([^/?#]+)/i)?.[1] || '';
    extId = extId.toLowerCase();
  } catch { /* keep the product ID blank when URL parsing fails */ }

  const labelAliases = {
    color: ['color', 'colour'],
    fabric: ['fabric', 'material'],
    fit_shape: ['fit shape', 'fit', 'shape'],
    length: ['length', 'dress length'],
  };
  const labelSet = new Set(['color', 'colour', 'fabric', 'material', 'fit shape', 'fit', 'shape', 'length', 'dress length', 'additional details', 'sold by', 'select size', 'product highlights', 'product ratings reviews', 'check delivery date']);
  const field = (aliases) => {
    for (let i = 0; i < lines.length; i += 1) {
      if (!aliases.includes(normalise(lines[i]))) continue;
      for (let j = i + 1; j < lines.length; j += 1) {
        const candidate = clean(lines[j]);
        if (!candidate) continue;
        if (labelSet.has(normalise(candidate))) break;
        return candidate;
      }
    }
    return '';
  };
  const color = field(labelAliases.color);
  const fabric = field(labelAliases.fabric);
  const fitShape = field(labelAliases.fit_shape);
  const length = field(labelAliases.length);

  let sizes = '';
  const sizeIndex = lines.findIndex((line) => normalise(line) === 'select size');
  const highlightsIndex = lines.findIndex((line, index) => index > sizeIndex && normalise(line) === 'product highlights');
  if (sizeIndex >= 0) {
    const sizeLines = lines.slice(sizeIndex + 1, highlightsIndex >= 0 ? highlightsIndex : sizeIndex + 12).join(' ');
    const matches = sizeLines.match(/\b(XXXL|XXL|XXS|XL|XS|S|M|L|ONE\s+SIZE|FREE\s+SIZE)\b/gi) || [];
    sizes = [...new Set(matches.map((size) => clean(size).toUpperCase()))].join(' | ');
  }

  let sellerName = '';
  const soldByIndex = lines.findIndex((line) => normalise(line) === 'sold by');
  if (soldByIndex >= 0) {
    for (const candidate of lines.slice(soldByIndex + 1, soldByIndex + 10)) {
      const value = clean(candidate);
      const normalized = normalise(value);
      if (!value || ['shop profile icon', 'view shop', 'products', 'ratings'].includes(normalized)) continue;
      if (/^[\d,.]+(?:\s+ratings?)?$/i.test(value) || /^[0-5](?:\.\d)?$/.test(value) || /^\d+\s+products?$/i.test(value)) continue;
      sellerName = value;
      break;
    }
  }

  let price = '';
  let oldPrice = '';
  let discount = '';
  if (priceMatch) {
    price = priceMatch[1].replaceAll(',', '');
    const afterPrice = mainText.slice(priceMatch.index + priceMatch[0].length);
    const oldMatch = /^\s*₹\s*([\d,]+)/.exec(afterPrice);
    if (oldMatch) {
      oldPrice = oldMatch[1].replaceAll(',', '');
      const discountMatch = /^\s*₹\s*[\d,]+\s*(\d+(?:\.\d+)?\s*%\s*off)/i.exec(afterPrice);
      if (discountMatch) discount = discountMatch[1].replace(/\s+/g, '');
    }
  }

  let rating = '';
  let ratingCount = '';
  let reviewCount = '';
  if (priceMatch) {
    const afterPrice = mainText.slice(priceMatch.index + priceMatch[0].length);
    const ratingMatch = /(?:^|\n)\s*([0-5](?:\.\d)?)\s+([\d,]+)\s+Ratings?\b/i.exec(afterPrice);
    if (ratingMatch) {
      rating = ratingMatch[1];
      ratingCount = ratingMatch[2].replaceAll(',', '');
      const afterRating = afterPrice.slice(ratingMatch.index + ratingMatch[0].length);
      const reviewMatch = /^\s*,?\s*([\d,]+)\s+Reviews?\b/i.exec(afterRating);
      if (reviewMatch) reviewCount = reviewMatch[1].replaceAll(',', '');
    } else {
      const simpleRating = /(?:^|\n)\s*([0-5](?:\.\d)?)\s*\n/i.exec(afterPrice);
      if (simpleRating) rating = simpleRating[1];
    }
  }

  const combined = `${title} ${fitShape} ${mainText}`.toLowerCase();
  let category = 'Fashion';
  if (/\b(bra|pant(?:y|ies)|lingerie|innerwear)\b/.test(combined)) category = 'Innerwear';
  else if (/\b(skirt|palazzo|plazo|trouser|pants|leggings|jeggings|shorts)\b/.test(combined)) category = 'Bottomwear';
  else if (/\b(kurti|kurta|anarkali)\b/.test(combined)) category = 'Kurtis';
  else if (/\b(saree|lehenga|salwar|ethnic|suit set)\b/.test(combined)) category = 'Ethnic Wear';
  else if (/\b(dress|bodycon|gown|one-piece|one piece|maxi|midi)\b/.test(combined)) category = 'Women Dresses';
  else if (/\b(top|tunic|shirt|blouse)\b/.test(combined)) category = 'Tops & Tunics';
  else if (/\b(sweater|sweatshirt|jacket|puffer|cardigan|shawl)\b/.test(combined)) category = 'Winter';
  const subcategories = [];
  if (/bodycon/i.test(`${title} ${fitShape}`)) subcategories.push('Bodycon');
  if (/full\s*sleeves?|long\s*sleeves?/i.test(combined)) subcategories.push('Full sleeves');
  if (/sleeveless/i.test(combined)) subcategories.push('Sleeveless');
  if (/party\s*wear/i.test(combined)) subcategories.push('Partywear');
  if (/floral/i.test(combined)) subcategories.push('Floral');

  const findBoundaryY = () => {
    const markers = ['real images and videos from customers', 'people also viewed'];
    const candidates = Array.from(document.querySelectorAll('h2,h3,h4,[role="heading"],p,div,section'));
    const found = [];
    for (const marker of markers) {
      for (const element of candidates) {
        const text = normalise(element.innerText || '');
        if (text.startsWith(marker) && text.length < 140) {
          const rect = element.getBoundingClientRect();
          if (rect.width || rect.height) found.push(rect.top + window.scrollY);
        }
      }
    }
    return found.length ? Math.min(...found) : null;
  };
  const boundaryY = findBoundaryY();
  const imageUrls = [];
  const seenImageKeys = new Set();
  const addImage = (raw) => {
    if (!raw || /^data:/i.test(raw)) return;
    try {
      const url = new URL(raw, location.href);
      if (url.hostname.toLowerCase() !== 'images.meesho.com') return;
      if (!url.pathname.toLowerCase().includes('/images/products/')) return;
      const key = `${url.origin}${url.pathname}`;
      if (seenImageKeys.has(key)) return;
      seenImageKeys.add(key);
      imageUrls.push(url.href);
    } catch { /* ignore malformed or non-image sources */ }
  };
  for (const image of Array.from(document.images)) {
    const rect = image.getBoundingClientRect();
    const imageY = rect.top + window.scrollY;
    if (boundaryY !== null && imageY >= boundaryY) continue;
    addImage(image.currentSrc);
    addImage(image.getAttribute('src'));
    addImage(image.getAttribute('data-src'));
    addImage(image.getAttribute('data-original'));
    addImage(image.getAttribute('data-lazy-src'));
    const srcset = image.getAttribute('srcset') || '';
    for (const candidate of srcset.split(',')) addImage(candidate.trim().split(/\s+/)[0]);
  }
  if (!imageUrls.length) {
    addImage(document.querySelector('meta[property="og:image"]')?.content || '');
  }

  let warning = '';
  if (!imageUrls.length) warning = 'No loaded product-image URLs found. Open/scroll the product gallery and try again; this tool will not fetch hidden images.';
  else if (boundaryY === null) warning = 'CSV ready. The page section boundary was not found, so check that image links belong to the main product—not recommendations.';
  else warning = 'CSV ready. It used product-image URLs already loaded above the customer-photo/recommendations section.';

  return {
    title,
    price,
    old_price: oldPrice,
    discount,
    rating,
    rating_count: ratingCount,
    review_count: reviewCount,
    category,
    subcategories: [...new Set(subcategories)].join(' | '),
    color,
    fabric,
    fit_shape: fitShape,
    length,
    sizes,
    seller_name: sellerName,
    product_url: productUrl,
    ext_id: extId,
    image_url: imageUrls[0] || '',
    gallery_image_urls: imageUrls.slice(1, 9).join('|'),
    affiliate_url: '',
    image_count: imageUrls.length,
    warning,
  };
}
