const $ = (id) => document.getElementById(id);
let inputFileName = '';
let sourceRows = [];
let sourceHeaders = [];
let urlHeader = '';
let scanned = null;
let activeTabId = null;
let results = [];

const URL_ALIASES = ['product_url', 'item_page_link', 'product_link', 'producturl', 'itemurl', 'url', 'link'];
const EXT_ALIASES = ['ext_id', 'product_id', 'slug', 'item_id'];
const TITLE_ALIASES = ['title', 'product_title', 'name', 'product_name'];

function parseCSV(text) {
  const rows = [];
  let row = [], field = '', quoted = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"' && text[i + 1] === '"') { field += '"'; i++; }
      else if (c === '"') quoted = false;
      else field += c;
    } else if (c === '"') quoted = true;
    else if (c === ',') { row.push(field); field = ''; }
    else if (c === '\n') { row.push(field); rows.push(row); row = []; field = ''; }
    else if (c !== '\r') field += c;
  }
  if (field.length || row.length) { row.push(field); rows.push(row); }
  while (rows.length && rows[rows.length - 1].every(x => !String(x).trim())) rows.pop();
  if (!rows.length) return {headers: [], records: []};
  const headers = rows.shift().map((h, i) => (i === 0 ? h.replace(/^\uFEFF/, '') : h).trim());
  const records = rows.filter(r => r.some(v => String(v).trim())).map(cells => {
    const obj = {};
    headers.forEach((h, i) => obj[h] = (cells[i] ?? '').trim());
    return obj;
  });
  return {headers, records};
}

function normalized(s) { return String(s || '').toLowerCase().replace(/[^a-z0-9]/g, ''); }
function findHeader(headers, aliases) {
  const map = new Map(headers.map(h => [normalized(h), h]));
  for (const a of aliases) if (map.has(normalized(a))) return map.get(normalized(a));
  return '';
}
function inferExtId(row, headers) {
  const key = findHeader(headers, EXT_ALIASES);
  if (key && row[key]) return String(row[key]).trim();
  const urlKey = findHeader(headers, URL_ALIASES);
  const url = urlKey ? row[urlKey] : '';
  const m = String(url || '').match(/\/p\/([^/?#]+)/i);
  return m ? m[1] : '';
}
function inferTitle(row, headers) {
  const key = findHeader(headers, TITLE_ALIASES);
  return (key && row[key]) || inferExtId(row, headers) || 'Product';
}
function csvEscape(v) { const s = String(v ?? ''); return /[",\r\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; }
function toCSV(headers, rows) { return [headers, ...rows.map(r => headers.map(h => r[h] ?? ''))].map(r => r.map(csvEscape).join(',')).join('\r\n'); }

function getProductRows() {
  return sourceRows.map(row => {
    const id = inferExtId(row, sourceHeaders);
    const url = row[urlHeader] || '';
    const title = inferTitle(row, sourceHeaders);
    return { ...row, __title: title, __ext_id: id, __url: url };
  });
}
function renderPreview() {
  const box = $('preview');
  if (!sourceRows.length) { box.classList.add('hidden'); return; }
  const rows = getProductRows();
  box.classList.remove('hidden');
  box.textContent = `${rows.length} product rows · URL column: ${urlHeader || 'not found'} · ${rows.filter(r => r.__ext_id).length} with ext_id`;
}
function setRunMessage(message, type = '') {
  const el = $('runStatus');
  el.textContent = message;
  el.className = 'run-status' + (type ? ' ' + type : '');
}

$('csvFile').addEventListener('change', async (event) => {
  const file = event.target.files?.[0];
  if (!file) return;
  inputFileName = file.name;
  const text = await file.text();
  const parsed = parseCSV(text);
  sourceHeaders = parsed.headers;
  sourceRows = parsed.records;
  urlHeader = findHeader(sourceHeaders, URL_ALIASES);
  $('csvStatus').textContent = `${inputFileName}: ${sourceRows.length} rows`;
  renderPreview();
  updateStartState();
});

async function currentTab() {
  const tabs = await chrome.tabs.query({active: true, currentWindow: true});
  return tabs[0] || null;
}

function optionLabel(c) {
  const main = [c.label, c.type && c.type !== 'text' ? c.type : '', c.tag].filter(Boolean).join(' · ');
  const s = c.selector.length > 48 ? c.selector.slice(0, 45) + '…' : c.selector;
  return `${main || c.selector}  [${s}]`;
}
function fillSelect(select, items, emptyLabel) {
  select.innerHTML = '';
  const first = document.createElement('option');
  first.value = ''; first.textContent = emptyLabel;
  select.appendChild(first);
  items.forEach((item, i) => {
    const o = document.createElement('option');
    o.value = String(i); o.textContent = optionLabel(item); select.appendChild(o);
  });
}
function updateStartState() {
  $('startBtn').disabled = !(sourceRows.length && urlHeader && scanned && $('urlField').value && $('generateButton').value);
}

$('scanBtn').addEventListener('click', async () => {
  try {
    const tab = await currentTab();
    if (!tab?.id) throw new Error('No active tab. Open the Meesho Creator link generator first.');
    activeTabId = tab.id;
    const response = await chrome.scripting.executeScript({target: {tabId: tab.id}, func: discoverControls});
    scanned = response?.[0]?.result;
    if (!scanned) throw new Error('Could not inspect this page. Open the visible Creator generator tab and try again.');
    if (scanned.error) throw new Error(scanned.error);
    fillSelect($('urlField'), scanned.fields, 'Choose URL / bulk field');
    fillSelect($('generateButton'), scanned.buttons, 'Choose Generate / submit button');
    const preferField = scanned.fields.findIndex(f => /url|product|link/i.test(`${f.label} ${f.name} ${f.placeholder}`) && f.type !== 'file')
      ?? -1;
    const preferButton = scanned.buttons.findIndex(b => /generate|create|convert|affiliate|submit/i.test(b.label));
    if (preferField >= 0) $('urlField').value = String(preferField);
    else if (scanned.fields.length === 1) $('urlField').value = '0';
    if (preferButton >= 0) $('generateButton').value = String(preferButton);
    else if (scanned.buttons.length === 1) $('generateButton').value = '0';
    $('controls').classList.toggle('hidden', !scanned.fields.length || !scanned.buttons.length);
    $('pageStatus').textContent = `${scanned.fields.length} visible input(s), ${scanned.buttons.length} button(s) found on ${tab.url || 'current tab'}`;
    if (!scanned.fields.length || !scanned.buttons.length) {
      $('pageStatus').textContent += '. If the page uses a different control, share a screenshot so the adapter can be tuned.';
    }
    updateStartState();
  } catch (err) {
    $('pageStatus').textContent = err.message || String(err);
    $('controls').classList.add('hidden');
    scanned = null;
    updateStartState();
  }
});

$('urlField').addEventListener('change', updateStartState);
$('generateButton').addEventListener('change', updateStartState);
$('mode').addEventListener('change', () => {
  if ($('mode').value === 'file' && $('urlField').value && scanned) {
    const c = scanned.fields[Number($('urlField').value)];
    if (c && c.type !== 'file') setRunMessage('CSV upload mode needs a visible file input selected above.', 'warn');
  }
});

$('startBtn').addEventListener('click', async () => {
  if (!sourceRows.length || !urlHeader || !scanned) return;
  $('startBtn').disabled = true;
  $('downloadBtn').disabled = true;
  $('results').innerHTML = '';
  setRunMessage(`Starting ${sourceRows.length} rows on the current Creator tab…`);
  try {
    const tab = await currentTab();
    if (!tab?.id || tab.id !== activeTabId) throw new Error('The active tab changed after scanning. Return to the scanned Creator tab and scan again.');
    const field = scanned.fields[Number($('urlField').value)];
    const button = scanned.buttons[Number($('generateButton').value)];
    const mode = $('mode').value;
    if (mode === 'file' && field.type !== 'file') throw new Error('For CSV upload mode, select the visible file input as the first field.');
    if (mode !== 'file' && field.type === 'file') throw new Error('A file input was selected. Choose CSV upload mode or select a URL/text field.');
    const payloadRows = getProductRows().map(r => ({...r, __url: String(r.__url || '').trim(), __ext_id: String(r.__ext_id || '').trim(), __title: String(r.__title || '').trim()}));
    const response = await chrome.scripting.executeScript({
      target: {tabId: tab.id},
      func: runPageBatch,
      args: [payloadRows, field.selector, button.selector, mode, 35000]
    });
    results = response?.[0]?.result?.rows || [];
    if (!results.length) throw new Error(response?.[0]?.result?.error || 'No results returned. Keep the official generator tab open and try again.');
    renderResults();
    const ok = results.filter(r => r.affiliate_status === 'ok').length;
    const missing = results.length - ok;
    $('downloadBtn').disabled = false;
    setRunMessage(`Finished: ${ok}/${results.length} official links validated${missing ? ` · ${missing} need review` : ''}.`, missing ? 'warn' : '');
  } catch (err) {
    setRunMessage(err.message || String(err), 'error');
  } finally {
    $('startBtn').disabled = !(sourceRows.length && urlHeader && scanned && $('urlField').value && $('generateButton').value);
  }
});

function renderResults() {
  const box = $('results');
  box.innerHTML = '';
  results.forEach(r => {
    const item = document.createElement('div'); item.className = 'result-item';
    const dot = document.createElement('span'); dot.className = 'dot ' + (r.affiliate_status === 'ok' ? 'ok' : 'err');
    const text = document.createElement('div'); text.className = 'result-text';
    const title = document.createElement('div'); title.className = 'result-title'; title.textContent = `${r.__title || r.__ext_id || 'Product'} · ${r.affiliate_status}`;
    text.appendChild(title);
    const url = document.createElement('span'); url.className = 'result-url'; url.textContent = r.affiliate_url || r.affiliate_error || '';
    text.appendChild(url); item.append(dot, text); box.appendChild(item);
  });
}

$('downloadBtn').addEventListener('click', () => {
  if (!results.length) return;
  const outputHeaders = [...sourceHeaders];
  for (const h of ['affiliate_url', 'affiliate_p_id', 'affiliate_status', 'affiliate_error']) if (!outputHeaders.includes(h)) outputHeaders.push(h);
  const byKey = new Map(results.map(r => [r.__ext_id, r]));
  const outRows = sourceRows.map(row => {
    const idKey = findHeader(sourceHeaders, EXT_ALIASES);
    const id = (idKey && row[idKey]) || inferExtId(row, sourceHeaders);
    const result = byKey.get(id) || {};
    return {...row, affiliate_url: result.affiliate_url || '', affiliate_p_id: result.affiliate_p_id || '', affiliate_status: result.affiliate_status || 'not_processed', affiliate_error: result.affiliate_error || ''};
  });
  const csv = '\uFEFF' + toCSV(outputHeaders, outRows);
  const blob = new Blob([csv], {type:'text/csv;charset=utf-8'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href = url; a.download = `meesho-creator-links-${new Date().toISOString().slice(0,10)}.csv`;
  document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
});

function discoverControls() {
  const isVisible = (el) => {
    const s = window.getComputedStyle(el); const r = el.getBoundingClientRect();
    return s.display !== 'none' && s.visibility !== 'hidden' && Number(s.opacity || 1) > 0 && r.width > 0 && r.height > 0;
  };
  const esc = (s) => window.CSS && CSS.escape ? CSS.escape(String(s)) : String(s).replace(/[^a-zA-Z0-9_-]/g, '\\$&');
  const selectorFor = (el) => {
    if (el.id) {
      const s = `#${esc(el.id)}`; if (document.querySelectorAll(s).length === 1) return s;
    }
    for (const attr of ['data-testid', 'name', 'aria-label', 'placeholder']) {
      const value = el.getAttribute(attr);
      if (value) {
        const s = `${el.tagName.toLowerCase()}[${attr}="${String(value).replace(/\\/g,'\\\\').replace(/"/g,'\\"')}"]`;
        try { if (document.querySelectorAll(s).length === 1) return s; } catch {}
      }
    }
    const parts = []; let node = el;
    while (node && node.nodeType === 1 && node !== document.documentElement) {
      let part = node.tagName.toLowerCase();
      if (node.id) { part += `#${esc(node.id)}`; parts.unshift(part); break; }
      const parent = node.parentElement;
      if (parent) {
        const same = [...parent.children].filter(x => x.tagName === node.tagName);
        if (same.length > 1) part += `:nth-of-type(${same.indexOf(node) + 1})`;
      }
      parts.unshift(part); node = parent;
    }
    return parts.join(' > ');
  };
  const textFor = (el) => {
    const labels = [];
    if (el.labels) [...el.labels].forEach(l => labels.push(l.innerText || l.textContent || ''));
    const labelledBy = el.getAttribute('aria-labelledby');
    if (labelledBy) labelledBy.split(/\s+/).forEach(id => { const n = document.getElementById(id); if (n) labels.push(n.innerText || n.textContent || ''); });
    return [...labels, el.getAttribute('aria-label'), el.getAttribute('placeholder'), el.getAttribute('name'), el.getAttribute('title'), el.value].filter(Boolean).join(' ').replace(/\s+/g, ' ').trim().slice(0, 90);
  };
  const fields = [...document.querySelectorAll('input:not([type="hidden"]), textarea')].filter(isVisible).map(el => ({
    selector: selectorFor(el), tag: el.tagName.toLowerCase(), type: String(el.type || (el.tagName.toLowerCase() === 'textarea' ? 'textarea' : 'text')).toLowerCase(),
    name: el.getAttribute('name') || '', placeholder: el.getAttribute('placeholder') || '', label: textFor(el), disabled: !!el.disabled
  }));
  const buttons = [...document.querySelectorAll('button, [role="button"], input[type="submit"], input[type="button"]')].filter(isVisible).map(el => ({
    selector: selectorFor(el), tag: el.tagName.toLowerCase(), type: String(el.type || '').toLowerCase(),
    label: (el.innerText || el.value || el.getAttribute('aria-label') || el.getAttribute('title') || '').replace(/\s+/g, ' ').trim().slice(0, 90), disabled: !!el.disabled
  }));
  return {url: location.href, fields, buttons};
}

async function runPageBatch(rows, fieldSelector, buttonSelector, mode, timeoutMs) {
  const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
  const getField = () => document.querySelector(fieldSelector);
  const getButton = () => document.querySelector(buttonSelector);
  const urlKey = (raw) => {
    try {
      const u = new URL(String(raw).replace(/&amp;/g, '&'), location.href);
      if (!u.pathname.includes('/af_invite/')) return null;
      return {url:u.href, ext_id:u.searchParams.get('ext_id') || '', p_id:u.searchParams.get('p_id') || ''};
    } catch { return null; }
  };
  const collectLinks = () => {
    const values = [];
    document.querySelectorAll('a[href*="/af_invite/"]').forEach(a => values.push(a.href));
    document.querySelectorAll('input,textarea,[contenteditable="true"],[data-clipboard-text],[data-copy]').forEach(el => {
      const v = el.value || el.innerText || el.textContent || el.getAttribute('data-clipboard-text') || el.getAttribute('data-copy') || '';
      if (v.includes('af_invite')) values.push(v);
    });
    const body = document.body?.innerText || '';
    for (const match of body.match(/https?:\/\/[^\s"'<>]+\/af_invite\/[^\s"'<>]+/g) || []) values.push(match.replace(/[),.;]+$/, ''));
    const found = new Map();
    for (let value of values) {
      value = String(value).replace(/&amp;/g, '&').trim();
      const direct = urlKey(value);
      if (direct) found.set(direct.url, direct);
      const matches = value.match(/https?:\/\/[^\s"'<>]+\/af_invite\/[^\s"'<>]+/g) || [];
      for (const m of matches) { const parsed = urlKey(m.replace(/[),.;]+$/, '')); if (parsed) found.set(parsed.url, parsed); }
    }
    return [...found.values()];
  };
  const setValue = (el, value) => {
    if (!el) throw new Error('Selected field is missing. Rescan the page.');
    if (el.disabled || el.readOnly) throw new Error('Selected field is disabled/read-only.');
    const proto = el.tagName.toLowerCase() === 'textarea' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
    if (setter) setter.call(el, value); else el.value = value;
    el.dispatchEvent(new Event('input', {bubbles:true}));
    el.dispatchEvent(new Event('change', {bubbles:true}));
  };
  const makeStatus = () => {
    let panel = document.getElementById('__creator_link_batch_status__');
    if (!panel) {
      panel = document.createElement('div'); panel.id = '__creator_link_batch_status__';
      panel.style.cssText = 'position:fixed;z-index:2147483647;right:14px;bottom:14px;background:#241a32;color:#fff;padding:10px 14px;border-radius:12px;font:600 13px/1.35 system-ui, sans-serif;box-shadow:0 8px 30px #0004;max-width:360px';
      document.documentElement.appendChild(panel);
    }
    return (text) => { panel.textContent = text; };
  };
  const status = makeStatus();
  const output = [];
  const targetField = getField(); const targetButton = getButton();
  if (!targetField || !targetButton) return {error:'Selected controls were not found. Click Scan page again and choose the controls.'};
  const cleanRows = rows.map(r => ({...r, __ext_id:String(r.__ext_id || '').trim(), __url:String(r.__url || '').trim(), __title:String(r.__title || '').trim()}));
  const captchaSeen = () => /captcha|verify you are human|are you human|security check|robot check/i.test(document.body?.innerText || '');
  const waitFor = async (row, previousUrls, limit) => {
    const end = Date.now() + limit;
    while (Date.now() < end) {
      if (captchaSeen()) return {manual:true};
      const match = collectLinks().find(x => x.ext_id === row.__ext_id && !previousUrls.has(x.url));
      if (match) return {link:match};
      await sleep(450);
    }
    return {};
  };
  const statusFor = (row, link, error='') => {
    const p = (link?.p_id || '').trim();
    const ok = !!(link?.url && link.ext_id === row.__ext_id && /^\d+$/.test(p));
    return {...row, affiliate_url:link?.url || '', affiliate_p_id:p, affiliate_status:ok ? 'ok' : (link?.url ? 'needs_review' : 'failed'), affiliate_error:error || (!link?.url ? 'No official link with matching ext_id appeared in the page.' : (!/^\d+$/.test(p) ? 'Generated URL did not contain a numeric p_id.' : 'Generated ext_id did not match input.'))};
  };

  try {
    if (mode === 'file') {
      if (targetField.type !== 'file') return {error:'CSV upload mode needs a visible file input selected.'};
      const csvRows = [['title','ext_id','product_url'], ...cleanRows.map(r => [r.__title,r.__ext_id,r.__url])];
      const csv = csvRows.map(r => r.map(v => { const s=String(v??''); return /[",\r\n]/.test(s) ? '"'+s.replace(/"/g,'""')+'"' : s; }).join(',')).join('\r\n');
      const file = new File([csv], 'meesho-creator-products.csv', {type:'text/csv'});
      const dt = new DataTransfer(); dt.items.add(file); targetField.files = dt.files;
      targetField.dispatchEvent(new Event('input',{bubbles:true})); targetField.dispatchEvent(new Event('change',{bubbles:true}));
      status('CSV submitted to visible file field. Starting generator…');
      const before = new Set(collectLinks().map(x=>x.url)); targetButton.click();
      const deadline = Date.now() + timeoutMs * 2;
      while (Date.now() < deadline) {
        if (captchaSeen()) break;
        const all = collectLinks();
        if (cleanRows.every(r => all.some(x=>x.ext_id===r.__ext_id && /^\d+$/.test(x.p_id)))) break;
        await sleep(500);
      }
      const all = collectLinks();
      for (const row of cleanRows) {
        const link = all.find(x=>x.ext_id===row.__ext_id && /^\d+$/.test(x.p_id)) || all.find(x=>x.ext_id===row.__ext_id) || null;
        output.push(statusFor(row, link, captchaSeen() ? 'Stopped for a human verification / CAPTCHA on the official page.' : ''));
      }
      return {rows:output, stoppedForManualCheck:captchaSeen()};
    }

    const isBulk = mode === 'bulk' || (mode === 'auto' && targetField.tagName.toLowerCase() === 'textarea');
    if (isBulk) {
      const before = new Set(collectLinks().map(x=>x.url));
      setValue(targetField, cleanRows.map(r=>r.__url).filter(Boolean).join('\n'));
      status(`Submitting ${cleanRows.length} URLs as one batch…`);
      targetButton.click();
      const deadline = Date.now() + timeoutMs * 2;
      while (Date.now() < deadline) {
        if (captchaSeen()) break;
        const all = collectLinks();
        const count = cleanRows.filter(r=>all.some(x=>x.ext_id===r.__ext_id && /^\d+$/.test(x.p_id))).length;
        status(`Waiting for official links… ${count}/${cleanRows.length}`);
        if (count >= cleanRows.length) break;
        await sleep(550);
      }
      const all = collectLinks();
      for (const row of cleanRows) {
        const link = all.find(x=>x.ext_id===row.__ext_id && !before.has(x.url)) || all.find(x=>x.ext_id===row.__ext_id) || null;
        output.push(statusFor(row, link, captchaSeen() ? 'Stopped for a human verification / CAPTCHA on the official page.' : ''));
      }
      return {rows:output, stoppedForManualCheck:captchaSeen()};
    }

    for (let i=0; i<cleanRows.length; i++) {
      const row = cleanRows[i];
      status(`Generating ${i+1}/${cleanRows.length} · ${row.__title || row.__ext_id}`);
      if (!row.__url || !row.__ext_id) {
        output.push(statusFor(row,null,'Missing product URL or ext_id in input CSV.'));
        continue;
      }
      if (captchaSeen()) {
        for (let j=i; j<cleanRows.length; j++) output.push(statusFor(cleanRows[j],null,'Paused: official page requested a human verification.'));
        break;
      }
      const before = new Set(collectLinks().map(x=>x.url));
      setValue(targetField, row.__url);
      await sleep(120);
      targetButton.click();
      const result = await waitFor(row,before,timeoutMs);
      if (result.manual) {
        output.push(statusFor(row,null,'Stopped: complete the human verification on the official page, then run again.'));
        for (let j=i+1; j<cleanRows.length; j++) output.push(statusFor(cleanRows[j],null,'Not run: previous row stopped for human verification.'));
        return {rows:output, stoppedForManualCheck:true};
      }
      output.push(statusFor(row,result.link || null));
      await sleep(850);
    }
    status(`Finished ${output.length}/${cleanRows.length}. Check the extension for results.`);
    return {rows:output};
  } catch (err) {
    status(`Stopped: ${err.message || String(err)}`);
    return {rows:output, error:err.message || String(err)};
  }
}
