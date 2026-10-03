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
  const [showCrawler, setShowCrawler] = useState(true);
  const [pasteText, setPasteText] = useState('');
  const [crawling, setCrawling] = useState(false);
  const [crawlNotice, setCrawlNotice] = useState('');
  const [viewMode, setViewMode] = useState('table'); // 'table' or 'grid'
  const [selectedIds, setSelectedIds] = useState(new Set());

  const pendingItems = products.filter(
    (p) => p.status === 'pending_review' || p.status === 'draft'
  );

  const handleSmartCrawl = async () => {
    if (!pasteText.trim()) return;
    setCrawling(true);
    setCrawlNotice('🚀 Crawling live product, images & affiliate route...');
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
        setCrawlNotice(`✨ Successfully synced "${data.product.title.slice(0, 30)}..." with real CDN images & affiliate link!`);
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

  const exportCSV = () => {
    const items = pendingItems.length > 0 ? pendingItems : products;
    if (!items.length) return;

    const rows = [
      ["ID", "Title", "Wholesale Cost", "Retail Price", "Sizes", "Fabric", "Product Image", "Live URL", "Creator Affiliate URL", "Category", "Status"]
    ];

    items.forEach((p) => {
      const title = getVal(p.id, 'title', p.title || '');
      const price = getVal(p.id, 'price', p.price || 399);
      const retail = Math.round(Number(price) * 1.6);
      const sizes = (p.sizes || ["S", "M", "L", "XL"]).join(', ');
      const img = getVal(p.id, 'image', p.image || '');
      const url = p.productUrl || '';
      const aff = p.affiliateUrl || '';
      const cat = getVal(p.id, 'category', p.category || 'Gen Z Aesthetic & Streetwear');

      rows.push([
        `"${p.id}"`,
        `"${title.replace(/"/g, '""')}"`,
        `"₹${price}"`,
        `"₹${retail}"`,
        `"${sizes}"`,
        `"${p.fabric || 'Cotton'}"`,
        `"${img}"`,
        `"${url}"`,
        `"${aff}"`,
        `"${cat}"`,
        `"${p.status}"`
      ]);
    });

    const csvContent = "data:text/csv;charset=utf-8," + rows.map(e => e.join(",")).join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `affiliate_catalog_setup_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const toggleSelect = (id) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (selectedIds.size === pendingItems.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(pendingItems.map((p) => p.id)));
    }
  };

  return (
    <div className="inbox-page" style={{ maxWidth: '1400px', margin: '0 auto', padding: '24px 20px' }}>
      {/* Header */}
      <div className="inbox-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
        <div>
          <div className="inbox-title-row" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <h1 className="inbox-title" style={{ fontSize: '24px', fontWeight: '800', color: '#fff' }}>📊 Live Data Setup & Trend Ingest</h1>
            <span className="inbox-count-badge" style={{ background: 'rgba(236, 72, 153, 0.2)', color: '#f472b6', border: '1px solid rgba(236, 72, 153, 0.4)', padding: '4px 12px', borderRadius: '999px', fontSize: '12px', fontWeight: '700' }}>
              {pendingItems.length} Records Ready for Curation
            </span>
          </div>
          <p className="inbox-subtitle" style={{ color: 'rgba(255,255,255,0.65)', fontSize: '13px', marginTop: '6px' }}>
            Multi-modal data setup table: Auto-attaches your Creator Affiliate ID, syncs live wholesale prices, calculates retail margins, and publishes with 1-click.
          </p>
        </div>

        {/* View Mode & Action Buttons */}
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <div style={{ background: 'rgba(255,255,255,0.08)', borderRadius: '8px', padding: '3px', display: 'flex', gap: '2px', marginRight: '8px' }}>
            <button
              type="button"
              onClick={() => setViewMode('table')}
              style={{ background: viewMode === 'table' ? '#ec4899' : 'transparent', color: '#fff', border: 'none', borderRadius: '6px', padding: '6px 12px', fontSize: '12px', fontWeight: '600', cursor: 'pointer' }}
            >
              📊 Data Setup Table
            </button>
            <button
              type="button"
              onClick={() => setViewMode('grid')}
              style={{ background: viewMode === 'grid' ? '#ec4899' : 'transparent', color: '#fff', border: 'none', borderRadius: '6px', padding: '6px 12px', fontSize: '12px', fontWeight: '600', cursor: 'pointer' }}
            >
              🖼️ Visual Cards
            </button>
          </div>

          <button
            type="button"
            className="button button-sm button-light"
            onClick={() => setShowCrawler((prev) => !prev)}
            style={{ background: 'rgba(255,255,255,0.1)', color: '#fff', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '8px', padding: '8px 14px', fontSize: '12px', cursor: 'pointer' }}
          >
            <Icon name="sparkles" size={14} /> {showCrawler ? 'Hide Setup Box' : '⚡ Smart Paste & Scraper'}
          </button>
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
                  <span style={{ fontSize: '11px', background: '#22c55e20', color: '#4ade80', border: '1px solid #22c55e40', padding: '2px 8px', borderRadius: '999px' }}>Auto-Affiliate (374453404) Attached</span>
                </strong>
                <p style={{ fontSize: '13px', color: 'rgba(255, 255, 255, 0.65)', margin: '4px 0 0 0' }}>
                  Paste any Meesho URL, Instagram Reel link, Pinterest Pin, or raw text (Ctrl+A &rarr; Ctrl+C). Python extracts real CDN images, sizes, pricing, and injects your official affiliate route.
                </p>
              </div>
            </div>
          </div>

          <textarea
            className="crawler-input-textarea"
            rows={3}
            value={pasteText}
            onChange={(e) => setPasteText(e.target.value)}
            placeholder="Paste Meesho Product URL (e.g. https://www.meesho.com/myali-brasil-rio-graphic-slim-fit-for-women/p/gy4v8f) or copied page text here..."
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
                <Icon name="sparkles" size={16} /> {crawling ? '🚀 Crawling & Syncing CDN Media...' : '⚡ Extract Variations & Add to Setup Table'}
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

      {/* DATA SETUP MASTER TABLE VIEW (Matching User's Screenshot) */}
      {viewMode === 'table' ? (
        <div style={{ background: 'rgba(255, 255, 255, 0.04)', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: '16px', padding: '20px', backdropFilter: 'blur(16px)' }}>
          {/* Table Header & Download Bar */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '14px', fontWeight: '700', color: '#fff' }}>Showing {pendingItems.length} records</span>
              <button
                type="button"
                onClick={toggleSelectAll}
                style={{ background: 'none', border: 'none', color: '#ec4899', fontSize: '12px', fontWeight: '600', cursor: 'pointer', textDecoration: 'underline' }}
              >
                {selectedIds.size === pendingItems.length ? 'Deselect All' : 'Select All'}
              </button>
            </div>

            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <button
                type="button"
                onClick={exportCSV}
                style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', padding: '6px 14px', borderRadius: '8px', fontSize: '12px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}
              >
                📥 .CSV
              </button>
              <button
                type="button"
                onClick={exportCSV}
                style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', padding: '6px 14px', borderRadius: '8px', fontSize: '12px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}
              >
                📊 .XLSX
              </button>
              <button
                type="button"
                onClick={() => window.location.reload()}
                style={{ background: 'transparent', border: '1px solid #38bdf8', color: '#38bdf8', padding: '6px 14px', borderRadius: '20px', fontSize: '12px', fontWeight: '700', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
              >
                Re-generate 🔄
              </button>
              <button
                type="button"
                onClick={onApproveAll}
                style={{ background: '#0d9488', border: 'none', color: '#fff', padding: '8px 20px', borderRadius: '20px', fontSize: '12px', fontWeight: '700', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
              >
                Continue / Publish All 🚀
              </button>
            </div>
          </div>

          {/* Table */}
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.15)', color: '#38bdf8', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  <th style={{ padding: '12px 8px', width: '40px' }}>✓</th>
                  <th style={{ padding: '12px 8px', width: '70px' }}>Photo</th>
                  <th style={{ padding: '12px 12px' }}>Product Title</th>
                  <th style={{ padding: '12px 10px', width: '100px' }}>Wholesale</th>
                  <th style={{ padding: '12px 10px', width: '110px' }}>Retail Est.</th>
                  <th style={{ padding: '12px 10px', width: '110px' }}>Net Profit</th>
                  <th style={{ padding: '12px 12px', width: '140px' }}>Sizes Available</th>
                  <th style={{ padding: '12px 12px' }}>Creator Affiliate Link</th>
                  <th style={{ padding: '12px 12px', width: '130px', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {pendingItems.length === 0 ? (
                  <tr>
                    <td colSpan={9} style={{ textAlign: 'center', padding: '40px', color: 'rgba(255,255,255,0.5)' }}>
                      ✨ No pending items. Use Smart Paste or CSV Upload above to add trending products!
                    </td>
                  </tr>
                ) : (
                  pendingItems.map((item) => {
                    const currentTitle = getVal(item.id, 'title', item.title || '');
                    const currentPrice = getVal(item.id, 'price', item.price || 245);
                    const costPrice = item.costPrice || Math.max(149, Number(currentPrice) - 100);
                    const retailEst = Math.round(Number(currentPrice) * 1.6);
                    const netMargin = retailEst - currentPrice;
                    const isSelected = selectedIds.has(item.id);

                    return (
                      <tr key={item.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.06)', background: isSelected ? 'rgba(236, 72, 153, 0.08)' : 'transparent' }}>
                        <td style={{ padding: '10px 8px' }}>
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => toggleSelect(item.id)}
                            style={{ cursor: 'pointer', accentColor: '#ec4899' }}
                          />
                        </td>
                        <td style={{ padding: '8px' }}>
                          <img
                            src={getVal(item.id, 'image', item.image)}
                            alt="preview"
                            style={{ width: '48px', height: '48px', objectFit: 'cover', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)' }}
                          />
                        </td>
                        <td style={{ padding: '10px 12px', fontWeight: '600', color: '#fff' }}>
                          <div>{currentTitle}</div>
                          <span style={{ fontSize: '11px', color: '#9ca3af' }}>{item.category || 'Gen Z Streetwear'}</span>
                        </td>
                        <td style={{ padding: '10px 10px', color: '#4ade80', fontWeight: '700' }}>
                          ₹{currentPrice}
                        </td>
                        <td style={{ padding: '10px 10px', color: '#38bdf8', fontWeight: '700' }}>
                          ₹{retailEst}
                        </td>
                        <td style={{ padding: '10px 10px', color: '#facc15', fontWeight: '700' }}>
                          +₹{netMargin}
                        </td>
                        <td style={{ padding: '10px 12px' }}>
                          <span style={{ background: 'rgba(56, 189, 248, 0.12)', color: '#38bdf8', padding: '3px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: '600' }}>
                            {(item.sizes || ["S", "M", "L", "XL"]).join(', ')}
                          </span>
                        </td>
                        <td style={{ padding: '10px 12px' }}>
                          <a
                            href={item.affiliateUrl || item.productUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{ color: '#ec4899', fontSize: '11px', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px', maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                            title={item.affiliateUrl}
                          >
                            🔗 {item.affiliateUrl ? 'Verified Creator Link' : 'Source Link'}
                          </a>
                        </td>
                        <td style={{ padding: '10px 12px', textAlign: 'right' }}>
                          <div style={{ display: 'flex', gap: '6px', justifyContent: 'flex-end' }}>
                            <button
                              type="button"
                              onClick={() => handleApprove(item)}
                              style={{ background: '#22c55e', border: 'none', color: '#fff', padding: '6px 12px', borderRadius: '6px', fontSize: '11px', fontWeight: '700', cursor: 'pointer' }}
                            >
                              ✓ Publish
                            </button>
                            <button
                              type="button"
                              onClick={() => handleDelete(item.id)}
                              style={{ background: 'rgba(239, 68, 68, 0.2)', border: '1px solid rgba(239, 68, 68, 0.4)', color: '#f87171', padding: '6px 10px', borderRadius: '6px', fontSize: '11px', cursor: 'pointer' }}
                            >
                              🗑️
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        /* Visual Cards Grid View */
        <div className="inbox-grid">
          {pendingItems.map((item) => {
            const currentTitle = getVal(item.id, 'title', item.title || '');
            const currentCat = getVal(item.id, 'category', item.category || 'Gen Z Aesthetic & Streetwear');
            const currentPrice = getVal(item.id, 'price', item.price || 245);
            const costPrice = item.costPrice || Math.max(149, Number(currentPrice) - 100);
            const estProfit = Math.max(0, Number(currentPrice) - costPrice);

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
                </div>

                <div className="inbox-card-content">
                  <div className="inbox-field-group">
                    <label className="inbox-label">Product Title</label>
                    <input
                      type="text"
                      className="inbox-input inbox-title-input"
                      value={currentTitle}
                      onChange={(e) => setVal(item.id, 'title', e.target.value)}
                    />
                  </div>

                  <div className="inbox-field-row">
                    <div className="inbox-field-group">
                      <label className="inbox-label">Price (₹)</label>
                      <input
                        type="number"
                        className="inbox-input"
                        value={currentPrice}
                        onChange={(e) => setVal(item.id, 'price', e.target.value)}
                      />
                    </div>
                    <div className="inbox-field-group">
                      <label className="inbox-label">Collection</label>
                      <select
                        className="inbox-select"
                        value={currentCat}
                        onChange={(e) => setVal(item.id, 'category', e.target.value)}
                      >
                        {CATEGORY_CHOICES.map((c) => (
                          <option key={c} value={c}>{c}</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div className="inbox-card-actions" style={{ marginTop: '12px', display: 'flex', gap: '8px' }}>
                    <button
                      type="button"
                      className="button button-sm button-dark"
                      onClick={() => handleApprove(item)}
                      style={{ flex: 1, background: '#22c55e', border: 'none', color: '#fff', padding: '8px', borderRadius: '8px', fontWeight: '700', cursor: 'pointer' }}
                    >
                      ✓ Publish to Storefront
                    </button>
                    <button
                      type="button"
                      className="button button-sm button-light button-danger-soft"
                      onClick={() => handleDelete(item.id)}
                      style={{ background: 'rgba(239, 68, 68, 0.2)', border: 'none', color: '#f87171', padding: '8px 12px', borderRadius: '8px', cursor: 'pointer' }}
                    >
                      🗑️
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
