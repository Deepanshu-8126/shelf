import React, { useState } from 'react';
import Icon from './Icon';

const CATEGORY_CHOICES = [
  'Gen Z Aesthetic & Streetwear',
  'Y2K Trend Drops',
  'Tops & Baby Tees',
  'Co-ord Sets',
  'Women Dresses',
  'Kurtis',
  'Ethnic Wear',
  'Bottomwear & Skirts',
  'Winter Outerwear',
  'Bags & Accessories',
  'Footwear',
  'Fashion'
];

export default function IngestInboxView({
  products = [],
  onApproveProduct,
  onApproveAll,
  onDeleteProduct,
  onDeleteAll,
  onUpdateProduct,
  onAddIngestProduct
}) {
  const [editingValues, setEditingValues] = useState({});
  const [busyIds, setBusyIds] = useState(new Set());
  const [showCrawler, setShowCrawler] = useState(false);
  const [pasteText, setPasteText] = useState('');
  const [crawling, setCrawling] = useState(false);
  const [crawlNotice, setCrawlNotice] = useState('');

  const pendingItems = products.filter(
    (p) => p.status === 'pending_review' || p.status === 'draft'
  );

  const handleSmartCrawl = async () => {
    if (!pasteText.trim()) return;
    setCrawling(true);
    setCrawlNotice('');
    try {
      const res = await fetch('/api/ingest/smart-crawl', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raw_text: pasteText.trim() })
      });
      const data = await res.json();
      if (data.success && data.product) {
        onAddIngestProduct?.(data.product);
        setPasteText('');
        setCrawlNotice(`✨ Successfully crawled "${data.product.title.slice(0, 35)}..." with ${data.product.colors?.length || 1} colors & ${data.product.sizes?.length || 1} sizes!`);
      } else {
        setCrawlNotice(data.error || 'Failed to crawl. Please check the text format.');
      }
    } catch (err) {
      setCrawlNotice('Network or server error connecting to Python crawler.');
    } finally {
      setCrawling(false);
    }
  };

  const getVal = (id, field, fallback) => {
    if (editingValues[id] && editingValues[id][field] !== undefined) {
      return editingValues[id][field];
    }
    return fallback;
  };

  const setVal = (id, field, value) => {
    setEditingValues((prev) => ({
      ...prev,
      [id]: {
        ...(prev[id] || {}),
        [field]: value
      }
    }));
  };

  const handleApprove = async (product) => {
    setBusyIds((prev) => new Set([...prev, product.id]));
    const edits = editingValues[product.id] || {};
    const updated = {
      ...product,
      ...edits,
      price: Number(edits.price ?? product.price),
      oldPrice: Number(edits.oldPrice ?? product.oldPrice),
      status: 'published'
    };
    await onApproveProduct(updated);
    setBusyIds((prev) => {
      const next = new Set(prev);
      next.delete(product.id);
      return next;
    });
  };

  const handleDelete = async (productId) => {
    if (!window.confirm('Are you sure you want to discard this item?')) return;
    setBusyIds((prev) => new Set([...prev, productId]));
    await onDeleteProduct(productId);
    setBusyIds((prev) => {
      const next = new Set(prev);
      next.delete(productId);
      return next;
    });
  };

  return (
    <div className="inbox-page">
      <div className="inbox-header">
        <div>
          <div className="inbox-title-row">
            <h1 className="inbox-title">📥 Trend Ingest Inbox</h1>
            <span className="inbox-count-badge">
              {pendingItems.length} Pending Review
            </span>
          </div>
          <p className="inbox-subtitle">
            Curated drops from Pinterest Extension and Smart Meesho Auto-Crawler. Review titles, auto-detected variations, prices, and publish to your live storefront.
          </p>
        </div>

        <div className="inbox-top-actions">
          <button
            type="button"
            className="button button-sm button-light"
            onClick={() => setShowCrawler((prev) => !prev)}
          >
            <Icon name="sparkles" size={14} /> {showCrawler ? 'Close Smart Paste' : '📋 Smart Paste & Crawl'}
          </button>
          {pendingItems.length > 0 && (
            <>
              <button
                type="button"
                className="button button-sm button-light button-danger-soft"
                onClick={onDeleteAll}
              >
                <Icon name="close" size={14} /> Discard All
              </button>
              <button
                type="button"
                className="button button-sm button-dark button-publish-all"
                onClick={onApproveAll}
              >
                <Icon name="check" size={14} /> 🚀 Publish All ({pendingItems.length}) to Storefront
              </button>
            </>
          )}
        </div>
      </div>

      {/* Smart Paste & Auto-Crawl Bar */}
      {showCrawler && (
        <div className="inbox-crawler-card" style={{ background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%)', border: '1px solid rgba(255, 255, 255, 0.12)', borderRadius: '16px', padding: '20px', marginBottom: '24px', backdropFilter: 'blur(20px)' }}>
          <div className="crawler-card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
            <div className="crawler-title" style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
              <span className="crawler-icon" style={{ fontSize: '24px', background: 'rgba(236, 72, 153, 0.15)', padding: '10px', borderRadius: '12px', color: '#ec4899' }}>⚡</span>
              <div>
                <strong style={{ fontSize: '16px', color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  Smart Fashion Ingest & Multi-Variant Sync Engine
                  <span style={{ fontSize: '11px', background: '#22c55e20', color: '#4ade80', border: '1px solid #22c55e40', padding: '2px 8px', borderRadius: '999px' }}>Live Catalog + Web Scraper Active</span>
                </strong>
                <p style={{ fontSize: '13px', color: 'rgba(255, 255, 255, 0.65)', margin: '4px 0 0 0' }}>
                  Paste any Meesho URL, Instagram Reel/Post link, Pinterest Pin, or full page text (Ctrl+A &rarr; Ctrl+C). Python extracts high-res Cloud CDN images, sizes, pricing, and generates your official Creator Affiliate link instantly.
                </p>
              </div>
            </div>
          </div>

          <textarea
            className="crawler-input-textarea"
            rows={3}
            value={pasteText}
            onChange={(e) => setPasteText(e.target.value)}
            placeholder="Paste Meesho Product URL (e.g. https://www.meesho.com/a-line-baby-pink-dress/p/baj21t) or copied page text here..."
            style={{ width: '100%', borderRadius: '12px', padding: '12px 16px', background: 'rgba(0,0,0,0.35)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', fontSize: '13px', resize: 'vertical' }}
          />

          <div className="crawler-action-bar" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '12px' }}>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                type="button"
                className="button button-dark crawler-submit-btn"
                disabled={crawling || !pasteText.trim()}
                onClick={handleSmartCrawl}
                style={{ background: 'linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%)', border: 'none', color: '#fff', fontWeight: '600', padding: '10px 20px', borderRadius: '10px', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}
              >
                <Icon name="sparkles" size={16} /> {crawling ? '🚀 Crawling & Extracting CDN Media...' : '⚡ Extract Variations & Add to Inbox'}
              </button>

              <label style={{ background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)', color: '#fff', fontWeight: '500', padding: '10px 16px', borderRadius: '10px', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '13px' }}>
                <Icon name="upload" size={15} /> 📂 Batch Import from CSV
                <input
                  type="file"
                  accept=".csv"
                  style={{ display: 'none' }}
                  onChange={async (e) => {
                    const file = e.target.files?.[0];
                    if (!file) return;
                    setCrawling(true);
                    setCrawlNotice(`Reading ${file.name}...`);
                    try {
                      const text = await file.text();
                      const res = await fetch('/api/ingest/csv-upload', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ csv_text: text })
                      });
                      const data = await res.json();
                      if (data.success) {
                        setCrawlNotice(`🎉 Successfully imported ${data.count} products from CSV with live images & affiliate links! Refreshing...`);
                        setTimeout(() => window.location.reload(), 1500);
                      } else {
                        setCrawlNotice(data.error || 'Failed to import CSV');
                      }
                    } catch {
                      setCrawlNotice('Network error uploading CSV');
                    } finally {
                      setCrawling(false);
                    }
                  }}
                />
              </label>
            </div>
            {crawlNotice && (
              <span className="crawler-notice-msg" style={{ fontSize: '12px', color: crawlNotice.includes('Successfully') ? '#4ade80' : '#f87171', background: 'rgba(0,0,0,0.4)', padding: '6px 12px', borderRadius: '8px' }}>
                {crawlNotice}
              </span>
            )}
          </div>
        </div>
      )}

      {pendingItems.length === 0 ? (
        <div className="inbox-empty-card">
          <div className="empty-sparkle-icon">✨</div>
          <h3>Your Ingest Inbox is all caught up!</h3>
          <p>
            No pending items waiting for review. When you clip aesthetic outfits on Pinterest using the <strong>shelf. Chrome Extension</strong>, they will land right here for your curation.
          </p>
          <div className="inbox-empty-tip">
            💡 <strong>Pro-Tip:</strong> Open Pinterest, open the extension, and click <em>"Ingest to Studio Inbox"</em> to import viral drops in 1 click!
          </div>
        </div>
      ) : (
        <div className="inbox-grid">
          {pendingItems.map((item) => {
            const currentTitle = getVal(item.id, 'title', item.title || '');
            const currentCat = getVal(item.id, 'category', item.category || 'Tops & Baby Tees');
            const currentPrice = getVal(item.id, 'price', item.price || 499);
            const costPrice = item.costPrice || Math.round(Number(currentPrice) * 0.45);
            const estProfit = Math.max(0, Number(currentPrice) - costPrice);
            const currentUrl = getVal(item.id, 'productUrl', item.productUrl || '');
            const currentAffiliate = getVal(item.id, 'affiliateUrl', item.affiliateUrl || '');
            const isBusy = busyIds.has(item.id);

            return (
              <div key={item.id} className="inbox-card">
                <div className="inbox-card-media">
                  <img
                    src={getVal(item.id, 'image', item.image)}
                    alt={currentTitle}
                    referrerPolicy="no-referrer"
                    loading="lazy"
                  />
                  <span className="inbox-tag-status">⏳ Pending Review</span>
                  <span className="inbox-tag-store">Meesho</span>
                  {item.gallery && item.gallery.length > 1 && (
                    <div className="inbox-gallery-strip">
                      {item.gallery.slice(0, 4).map((gImg, gIdx) => (
                        <img
                          key={gIdx}
                          src={gImg}
                          alt="thumb"
                          className={`inbox-thumb-mini ${getVal(item.id, 'image', item.image) === gImg ? 'active-thumb' : ''}`}
                          onClick={() => setVal(item.id, 'image', gImg)}
                          title="Click to use as primary cover"
                        />
                      ))}
                    </div>
                  )}
                </div>

                <div className="inbox-card-content">
                  {/* Title Field */}
                  <div className="inbox-field-group">
                    <label className="inbox-label">Product Title</label>
                    <input
                      type="text"
                      className="inbox-input inbox-title-input"
                      value={currentTitle}
                      onChange={(e) => setVal(item.id, 'title', e.target.value)}
                      placeholder="Product title"
                    />
                  </div>

                  {/* Category Field */}
                  <div className="inbox-field-row">
                    <div className="inbox-field-group" style={{ flex: 1 }}>
                      <label className="inbox-label">Category</label>
                      <select
                        className="inbox-input inbox-select"
                        value={currentCat}
                        onChange={(e) => setVal(item.id, 'category', e.target.value)}
                      >
                        {CATEGORY_CHOICES.map((c) => (
                          <option key={c} value={c}>{c}</option>
                        ))}
                      </select>
                    </div>

                    {/* Price & Profit */}
                    <div className="inbox-field-group" style={{ width: '120px' }}>
                      <label className="inbox-label">Selling Price</label>
                      <div className="inbox-price-input-wrap">
                        <span>₹</span>
                        <input
                          type="number"
                          className="inbox-input"
                          value={currentPrice}
                          onChange={(e) => setVal(item.id, 'price', e.target.value)}
                        />
                      </div>
                    </div>

                    <div className="inbox-profit-pill">
                      <span className="profit-title">Est. Margin</span>
                      <span className="profit-amount">+₹{estProfit}</span>
                    </div>
                  </div>

                  {/* Multi-variant Color & Size tags */}
                  {((item.colors && item.colors.length > 0) || (item.sizes && item.sizes.length > 0)) && (
                    <div className="inbox-variations-box">
                      {item.colors && item.colors.length > 0 && (
                        <div className="inbox-var-group">
                          <span className="inbox-var-label">Auto Colors:</span>
                          <div className="inbox-var-list">
                            {item.colors.map((c) => (
                              <span key={c} className="inbox-var-pill color-pill">{c}</span>
                            ))}
                          </div>
                        </div>
                      )}
                      {item.sizes && item.sizes.length > 0 && (
                        <div className="inbox-var-group">
                          <span className="inbox-var-label">Auto Sizes:</span>
                          <div className="inbox-var-list">
                            {item.sizes.map((s) => (
                              <span key={s} className="inbox-var-pill size-chip">{s}</span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Affiliate Link Field */}
                  <div className="inbox-field-group">
                    <div className="inbox-label-row">
                      <label className="inbox-label">Meesho Affiliate / Search Link</label>
                      <a
                        href={currentAffiliate || currentUrl || `https://www.meesho.com/search?q=${encodeURIComponent(currentTitle)}`}
                        target="_blank"
                        rel="noreferrer"
                        className="inbox-search-link"
                      >
                        🔍 Open on Meesho ↗
                      </a>
                    </div>
                    <input
                      type="text"
                      className="inbox-input inbox-link-input"
                      value={currentAffiliate || currentUrl}
                      onChange={(e) => {
                        const val = e.target.value;
                        setVal(item.id, 'affiliateUrl', val);
                        setVal(item.id, 'productUrl', val);
                      }}
                      placeholder="Paste your Meesho affiliate link or leave search link..."
                    />
                  </div>

                  {/* Bottom Actions */}
                  <div className="inbox-card-actions">
                    <button
                      type="button"
                      className="button button-sm button-light button-danger-soft"
                      onClick={() => handleDelete(item.id)}
                      disabled={isBusy}
                    >
                      <Icon name="close" size={14} /> Discard
                    </button>
                    <button
                      type="button"
                      className="button button-sm button-dark button-approve"
                      onClick={() => handleApprove(item)}
                      disabled={isBusy}
                    >
                      <Icon name="check" size={14} /> 🚀 Publish to Live Storefront
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
