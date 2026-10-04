import React, { useMemo, useState } from 'react';
import Icon from './Icon.jsx';

function lines(value) {
  return value.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
}

function statusLabel(status = '') {
  if (status === 'ready_update_existing') return 'Ready · update existing';
  if (status === 'ready_add_new') return 'Ready · new product';
  if (status.startsWith('published_update_existing')) return 'Published · updated';
  if (status.startsWith('published_new')) return 'Published · new product';
  if (status.startsWith('needs_')) return status.replaceAll('_', ' ');
  if (status.startsWith('not_published')) return status.replaceAll('_', ' ');
  return status.replaceAll('_', ' ') || 'Review needed';
}

function isReady(record) {
  return record.status === 'ready_update_existing' || record.status === 'ready_add_new';
}

export default function ImporterPanel({ onProductsPublished }) {
  const [text, setText] = useState('');
  const [linksText, setLinksText] = useState('');
  const [imagesText, setImagesText] = useState('');
  const [records, setRecords] = useState([]);
  const [busy, setBusy] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const readyCount = useMemo(() => records.filter(isReady).length, [records]);

  const preview = async (event) => {
    event.preventDefault();
    setError('');
    setNotice('');
    setRecords([]);
    setBusy(true);
    try {
      const response = await fetch('/api/import/preview', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, links: lines(linksText), images: lines(imagesText) }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Could not analyse this paste');
      setRecords(data.records || []);
      setNotice(data.count ? `Found ${data.count} listing${data.count === 1 ? '' : 's'} · ${data.readyCount || 0} ready to publish` : 'No product cards found in that paste.');
    } catch (exception) {
      setError(exception.message || 'The Python import service is not responding.');
    } finally {
      setBusy(false);
    }
  };

  const publish = async () => {
    if (!readyCount) return;
    setError('');
    setNotice('');
    setPublishing(true);
    try {
      const response = await fetch('/api/import/publish', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ records: records.filter(isReady) }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Could not publish the ready listings');
      const stillNeedsReview = records.filter((record) => !isReady(record));
      setRecords([...(data.records || []), ...stillNeedsReview]);
      setNotice(`Published ${data.published || 0} · ${data.skipped || 0} need review`);
      onProductsPublished?.(data.products || []);
    } catch (exception) {
      setError(exception.message || 'The Python import service is not responding.');
    } finally {
      setPublishing(false);
    }
  };

  return (
    <div className="standard-view importer-view">
      <div className="page-intro">
        <div>
          <p className="eyebrow">PYTHON-POWERED · CREATOR ONLY</p>
          <h1>Import a little edit</h1>
          <p className="page-subtitle">Paste a batch or approved product export. Python sorts it, checks IDs and prepares the affiliate routes.</p>
        </div>
        <span className="importer-safety-chip"><span /> No title-only matching</span>
      </div>

      <div className="importer-layout">
        <form className="importer-form-card" onSubmit={preview}>
          <div className="importer-card-heading"><span className="importer-card-icon"><Icon name="sparkles" size={18} /></span><div><strong>Drop in your listing text</strong><small>One batch is enough—no need to add each card to the site by hand.</small></div></div>
          <label className="field-label" htmlFor="paste-listings">Copied Meesho listing text or approved export</label>
          <textarea id="paste-listings" className="importer-listing-input" value={text} onChange={(event) => setText(event.target.value)} placeholder={'Paste the full copied listing batch here…\n\nInclude product links and image URLs in the copied content when available.'} required />
          <details className="importer-optional-inputs">
            <summary>Optional: separate product and image URLs</summary>
            <p>If your copy omits these, paste URL lists in the same order as the cards. For the 3-second product-photo slider, an approved CSV/feed can include a <code>gallery_image_urls</code> column with extra Meesho image URLs separated by <code>|</code> (up to 8 per listing; keep the main photo in <code>image_url</code>).</p>
            <label className="field-label" htmlFor="paste-product-links">Product links · one per line</label>
            <textarea id="paste-product-links" value={linksText} onChange={(event) => setLinksText(event.target.value)} placeholder="https://www.meesho.com/s/p/…" rows={3} />
            <label className="field-label" htmlFor="paste-image-links">Product image URLs · one per line</label>
            <textarea id="paste-image-links" value={imagesText} onChange={(event) => setImagesText(event.target.value)} placeholder="https://images.meesho.com/images/products/…" rows={3} />
          </details>
          <div className="importer-note"><Icon name="shield" size={15} /><span>Copied detail-page text like title, price, rating, color, fabric, fit, length and sizes is welcome—it will appear as a review draft. To publish a new product, add its exact Meesho product URL or ID and a real product image URL. This tool never scrapes protected pages or guesses IDs.</span></div>
          {error && <p className="importer-message importer-message-error" role="alert">{error}</p>}
          {notice && <p className="importer-message" role="status">{notice}</p>}
          <div className="importer-actions"><button className="button button-dark" type="submit" disabled={busy || !text.trim()}><Icon name="sparkles" size={16} /> {busy ? 'Analysing…' : 'Analyse with Python'}</button>{records.length > 0 && <button className="button button-primary" type="button" onClick={publish} disabled={publishing || readyCount === 0}><Icon name="check" size={15} /> {publishing ? 'Publishing…' : `Publish ${readyCount} ready`}</button>}</div>
        </form>

        <aside className="importer-process-card">
          <p className="eyebrow">THE AUTO-FLOW</p>
          <h2>One batch in.<br /><em>Neat product cards out.</em></h2>
          <ol className="importer-steps">
            <li><span>01</span><div><strong>Read the listing</strong><small>Title, current price, old price, visible review score and product URLs.</small></div></li>
            <li><span>02</span><div><strong>Sort the edit</strong><small>Women’s categories and subcategory tags are assigned automatically.</small></div></li>
            <li><span>03</span><div><strong>Check IDs & duplicates</strong><small>One Meesho product ID becomes one card. Different IDs stay separate.</small></div></li>
            <li><span>04</span><div><strong>Route, then publish</strong><small>Ready listings get your Meesho route. Missing source data stays for review.</small></div></li>
          </ol>
          <div className="importer-trend-note"><span>✦</span><p><strong>Trend-led, not Pinterest photos.</strong> Use trend themes to guide the edit; product images and shopping links must come from the real marketplace listing or an approved feed.</p></div>
        </aside>
      </div>

      {records.length > 0 && (
        <section className="importer-results-card">
          <div className="section-heading-row importer-results-heading"><div><p className="eyebrow">CHECK BEFORE IT GOES LIVE</p><h2>Import review <span className="section-count">{records.length}</span></h2></div><span className="importer-ready-count">{readyCount} ready</span></div>
          <div className="importer-results-list">
            {records.map((record, index) => (
              <article className="importer-result-row" key={`${record.ext_id || record.title}-${index}`}>
                <div className="importer-result-thumb">{record.image_url ? <img src={record.image_url} alt="" loading="lazy" /> : <Icon name="image" size={17} />}</div>
                <div className="importer-result-main"><strong>{record.title || 'Title needs review'}</strong><span>{record.category}{record.subcategories ? ` · ${record.subcategories}` : ''}</span><small>{record.ext_id ? `ID ${record.ext_id}` : 'Product ID missing'}{Array.isArray(record.gallery_image_urls) && record.gallery_image_urls.length ? ` · ${record.gallery_image_urls.length} extra photos` : typeof record.gallery_image_urls === 'string' && record.gallery_image_urls ? ` · ${record.gallery_image_urls.split(/[|;]+/).filter(Boolean).length} extra photos` : ''}</small>{(record.color || record.fabric || record.fit_shape || record.length || record.sizes) && <small>{[record.color, record.fabric, record.fit_shape, record.length].filter(Boolean).join(' · ')}{record.sizes ? `${[record.color, record.fabric, record.fit_shape, record.length].some(Boolean) ? ' · ' : ''}Sizes ${Array.isArray(record.sizes) ? record.sizes.join(', ') : record.sizes.replace(/[|;]/g, ', ')}` : ''}</small>}{record.rating && <small>★ {record.rating}{record.rating_count ? ` · ${Number(record.rating_count).toLocaleString('en-IN')} ratings` : ''}{record.review_count ? ` · ${Number(record.review_count).toLocaleString('en-IN')} reviews` : ''}{record.seller_name ? ` · ${record.seller_name}` : ''}</small>}</div>
                <div className="importer-result-price">₹{Number(record.price || 0).toLocaleString('en-IN')}<small>{record.old_price ? `was ₹${Number(record.old_price).toLocaleString('en-IN')}` : 'current price'}</small></div>
                <span className={`importer-status${isReady(record) ? ' is-ready' : record.status.startsWith('published_') ? ' is-published' : ' needs-review'}`}>{statusLabel(record.status)}</span>
              </article>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
