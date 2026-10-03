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
  const [crawlerMode, setCrawlerMode] = useState('autonomous'); // 'autonomous', 'paste', 'csv'
  const [crawlUrl, setCrawlUrl] = useState('https://www.meesho.com/western-wear-women/pl/4aus');
  const [crawlLimit, setCrawlLimit] = useState(8);
  const [crawlCollection, setCrawlCollection] = useState('meesho-genz-2026');
  const [pasteText, setPasteText] = useState('');
  const [crawling, setCrawling] = useState(false);
  const [crawlNotice, setCrawlNotice] = useState('');
  const [viewMode, setViewMode] = useState('table'); // 'table' or 'grid'
  const [activeTab, setActiveTab] = useState('all'); // 'all', 'pending', 'published'
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [copiedId, setCopiedId] = useState('');

  // Autonomous URL Deep Scraper Handler
  const handleAutonomousDeepScrape = async () => {
    if (!crawlUrl.trim()) return;
    setCrawling(true);
    setCrawlNotice('🤖 Auto-crawling Meesho page, expanding lazy variations, extracting HD CDN photos & calculating margins...');
    try {
      const res = await fetch('/api/ingest/deep-scrape-url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: crawlUrl.trim(),
          limit: Number(crawlLimit) || 8,
          collectionId: crawlCollection,
          margin_pct: 0.45
        })
      });
      const data = await res.json();
      if (data.success && data.products && data.products.length > 0) {
        data.products.forEach(p => onAddIngestProduct?.(p));
        setCrawlNotice(`🎉 Successfully deep-crawled & ingested ${data.products.length} outfits with full variation photos!`);
      } else {
        setCrawlNotice(data.error || 'Could not extract products from this URL. Try another category link or Smart Paste.');
      }
    } catch (err) {
      setCrawlNotice('Network/API connection error. Ensure catalog backend is running.');
    } finally {
      setCrawling(false);
    }
  };

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

  const [minRating, setMinRating] = useState(0); // 0 (all), 3.8, 4.0, 4.5

  // Filter based on active tab, search, and quality rating
  const filteredProducts = products.filter((p) => {
    const matchesTab =
      activeTab === 'all'
        ? true
        : activeTab === 'pending'
        ? p.status === 'pending_review' || p.status === 'draft'
        : p.status === 'published';

    const matchesSearch =
      !searchQuery ||
      (p.title || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (p.category || '').toLowerCase().includes(searchQuery.toLowerCase());

    const itemRating = Number(p.rating || 4.2);
    const matchesRating = minRating === 0 || itemRating >= minRating;

    return matchesTab && matchesSearch && matchesRating;
  });

  const handleBulkDelete = async () => {
    if (selectedIds.size === 0) return;
    if (!window.confirm(`Are you sure you want to permanently remove ${selectedIds.size} selected items?`)) return;
    for (const id of selectedIds) {
      await onDeleteProduct?.(id);
    }
    setSelectedIds(new Set());
  };

  const handleBulkApprove = async () => {
    if (selectedIds.size === 0) return;
    for (const id of selectedIds) {
      const prod = products.find(p => p.id === id);
      if (prod) await handleApprove(prod);
    }
    setSelectedIds(new Set());
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

  const copyAffiliate = (id, url) => {
    if (!url) return;
    navigator.clipboard.writeText(url);
    setCopiedId(id);
    setTimeout(() => setCopiedId(''), 2000);
  };

  const exportCSV = () => {
    const items = filteredProducts.length > 0 ? filteredProducts : products;
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
    if (selectedIds.size === filteredProducts.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredProducts.map((p) => p.id)));
    }
  };

  return (
    <div className="inbox-page" style={{ maxWidth: '1440px', margin: '0 auto', padding: '24px 20px' }}>
      {/* Header */}
      <div className="inbox-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
        <div>
          <div className="inbox-title-row" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <h1 className="inbox-title" style={{ fontSize: '24px', fontWeight: '800', color: '#fff' }}>🤖 Autonomous Multi-Scraper & Live Sourcing Studio</h1>
            <span className="inbox-count-badge" style={{ background: 'rgba(236, 72, 153, 0.2)', color: '#f472b6', border: '1px solid rgba(236, 72, 153, 0.4)', padding: '4px 12px', borderRadius: '999px', fontSize: '12px', fontWeight: '700' }}>
              {products.length} Total Sourced Products
            </span>
          </div>
          <p className="inbox-subtitle" style={{ color: 'rgba(255,255,255,0.65)', fontSize: '13px', marginTop: '6px' }}>
            Next-Gen Autonomous Sourcing: Crawl Meesho categories, auto-scroll pages, extract multi-angle gallery variations, and auto-attach your Creator Affiliate Route (<code style={{ color: '#38bdf8' }}>374453404:12492338</code>).
          </p>
        </div>

        {/* View Mode & Filter Tabs */}
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ background: 'rgba(255,255,255,0.08)', borderRadius: '8px', padding: '3px', display: 'flex', gap: '2px' }}>
            <button
              type="button"
              onClick={() => setActiveTab('all')}
              style={{ background: activeTab === 'all' ? '#ec4899' : 'transparent', color: '#fff', border: 'none', borderRadius: '6px', padding: '6px 12px', fontSize: '12px', fontWeight: '600', cursor: 'pointer' }}
            >
              All Catalog ({products.length})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('pending')}
              style={{ background: activeTab === 'pending' ? '#ec4899' : 'transparent', color: '#fff', border: 'none', borderRadius: '6px', padding: '6px 12px', fontSize: '12px', fontWeight: '600', cursor: 'pointer' }}
            >
              Pending Ingest ({products.filter(p => p.status === 'pending_review' || p.status === 'draft').length})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('published')}
              style={{ background: activeTab === 'published' ? '#ec4899' : 'transparent', color: '#fff', border: 'none', borderRadius: '6px', padding: '6px 12px', fontSize: '12px', fontWeight: '600', cursor: 'pointer' }}
            >
              Live Storefront ({products.filter(p => p.status === 'published').length})
            </button>
          </div>

          <div style={{ background: 'rgba(255,255,255,0.08)', borderRadius: '8px', padding: '3px', display: 'flex', gap: '2px' }}>
            <button
              type="button"
              onClick={() => setViewMode('table')}
              style={{ background: viewMode === 'table' ? '#3b82f6' : 'transparent', color: '#fff', border: 'none', borderRadius: '6px', padding: '6px 12px', fontSize: '12px', fontWeight: '600', cursor: 'pointer' }}
            >
              📊 Table
            </button>
            <button
              type="button"
              onClick={() => setViewMode('grid')}
              style={{ background: viewMode === 'grid' ? '#3b82f6' : 'transparent', color: '#fff', border: 'none', borderRadius: '6px', padding: '6px 12px', fontSize: '12px', fontWeight: '600', cursor: 'pointer' }}
            >
              🖼️ Grid
            </button>
          </div>
        </div>
      </div>

      {/* AUTONOMOUS MULTI-SCRAPER STUDIO CARD */}
      <div className="inbox-crawler-card" style={{ background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%)', border: '1px solid rgba(255, 255, 255, 0.12)', borderRadius: '16px', padding: '20px', marginBottom: '24px', backdropFilter: 'blur(20px)' }}>
        {/* Mode Selector Tabs */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              type="button"
              onClick={() => setCrawlerMode('autonomous')}
              style={{ background: crawlerMode === 'autonomous' ? 'linear-gradient(135deg, #38bdf8 0%, #6366f1 100%)' : 'rgba(255,255,255,0.08)', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: '10px', fontSize: '13px', fontWeight: '700', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              🤖 Autonomous Category & Deep Scraper
            </button>
            <button
              type="button"
              onClick={() => setCrawlerMode('paste')}
              style={{ background: crawlerMode === 'paste' ? 'linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%)' : 'rgba(255,255,255,0.08)', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: '10px', fontSize: '13px', fontWeight: '700', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              📋 Smart Paste (Ctrl+A &rarr; Ctrl+C)
            </button>
            <button
              type="button"
              onClick={() => setCrawlerMode('csv')}
              style={{ background: crawlerMode === 'csv' ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)' : 'rgba(255,255,255,0.08)', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: '10px', fontSize: '13px', fontWeight: '700', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              📂 Batch CSV Upload
            </button>
          </div>

          <span style={{ fontSize: '11px', background: '#22c55e20', color: '#4ade80', border: '1px solid #22c55e40', padding: '4px 10px', borderRadius: '999px', fontWeight: '700' }}>
            ● Live Affiliate Generator Active
          </span>
        </div>

        {/* MODE 1: Autonomous URL Scraper */}
        {crawlerMode === 'autonomous' && (
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr auto', gap: '10px', alignItems: 'center' }}>
              <input
                type="text"
                value={crawlUrl}
                onChange={(e) => setCrawlUrl(e.target.value)}
                placeholder="Enter Meesho Category / Search URL (e.g. https://www.meesho.com/western-wear-women/pl/4aus)"
                style={{ borderRadius: '10px', padding: '12px 14px', background: 'rgba(0,0,0,0.4)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', fontSize: '13px' }}
              />
              <select
                value={crawlCollection}
                onChange={(e) => setCrawlCollection(e.target.value)}
                style={{ borderRadius: '10px', padding: '12px 10px', background: 'rgba(20,24,35,0.9)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', fontSize: '12px' }}
              >
                <option value="meesho-genz-2026">Collection: Gen Z Streetwear &amp; Graphic</option>
                <option value="brasilcore-edits">Collection: Brasilcore &amp; Baby Tees</option>
                <option value="co-ord-sets">Collection: Y2K Co-ord Sets</option>
                <option value="meesho-dresses-2026">Collection: Slinky Bodycon Dresses</option>
                <option value="meesho-kurtis-2026">Collection: Ethnic Kurtis</option>
              </select>
              <select
                value={crawlLimit}
                onChange={(e) => setCrawlLimit(e.target.value)}
                style={{ borderRadius: '10px', padding: '12px 10px', background: 'rgba(20,24,35,0.9)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', fontSize: '12px' }}
              >
                <option value={5}>Limit: 5 Products</option>
                <option value={8}>Limit: 8 Products</option>
                <option value={15}>Limit: 15 Products</option>
                <option value={25}>Limit: 25 Products</option>
              </select>
              <button
                type="button"
                disabled={crawling || !crawlUrl.trim()}
                onClick={handleAutonomousDeepScrape}
                style={{ background: 'linear-gradient(135deg, #38bdf8 0%, #6366f1 100%)', border: 'none', color: '#fff', fontWeight: '750', padding: '12px 24px', borderRadius: '10px', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', whiteSpace: 'nowrap' }}
              >
                {crawling ? '🤖 Scraping Live...' : '⚡ Run Autonomous Deep Scraper'}
              </button>
            </div>
            <div style={{ display: 'flex', gap: '8px', marginTop: '10px', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '11px', color: '#9ca3af' }}>Quick Targets:</span>
              <button
                type="button"
                onClick={() => setCrawlUrl('https://www.meesho.com/women-tshirts/pl/3sc')}
                style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)', color: '#38bdf8', padding: '3px 8px', borderRadius: '6px', fontSize: '11px', cursor: 'pointer' }}
              >
                Women T-shirts / Tops
              </button>
              <button
                type="button"
                onClick={() => setCrawlUrl('https://www.meesho.com/western-wear-women/pl/4aus')}
                style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)', color: '#38bdf8', padding: '3px 8px', borderRadius: '6px', fontSize: '11px', cursor: 'pointer' }}
              >
                Western Wear / Y2K
              </button>
              <button
                type="button"
                onClick={() => setCrawlUrl('https://www.meesho.com/women-dresses/pl/3sv')}
                style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)', color: '#38bdf8', padding: '3px 8px', borderRadius: '6px', fontSize: '11px', cursor: 'pointer' }}
              >
                Bodycon Dresses
              </button>
            </div>
          </div>
        )}

        {/* MODE 2: Smart Paste */}
        {crawlerMode === 'paste' && (
          <div>
            <textarea
              className="crawler-input-textarea"
              rows={3}
              value={pasteText}
              onChange={(e) => setPasteText(e.target.value)}
              placeholder="Paste raw copied Meesho text (Ctrl+A &rarr; Ctrl+C on any product page) or single product link..."
              style={{ width: '100%', borderRadius: '12px', padding: '12px 16px', background: 'rgba(0,0,0,0.35)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', fontSize: '13px', resize: 'vertical' }}
            />
            <div style={{ display: 'flex', justifyContent: 'flex-start', marginTop: '10px' }}>
              <button
                type="button"
                disabled={crawling || !pasteText.trim()}
                onClick={handleSmartCrawl}
                style={{ background: 'linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%)', border: 'none', color: '#fff', fontWeight: '700', padding: '10px 22px', borderRadius: '10px', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}
              >
                <Icon name="sparkles" size={16} /> {crawling ? '🚀 Crawling & Syncing Variations...' : '⚡ Extract Variations & Add to Table'}
              </button>
            </div>
          </div>
        )}

        {/* MODE 3: CSV Batch Upload */}
        {crawlerMode === 'csv' && (
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <label style={{ background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)', color: '#fff', fontWeight: '600', padding: '12px 20px', borderRadius: '10px', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '13px' }}>
              <Icon name="upload" size={16} /> Select Scraped Meesho .CSV File
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
                      setCrawlNotice(`🎉 Successfully imported ${data.count} products from CSV! Refreshing...`);
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
            <span style={{ fontSize: '12px', color: '#9ca3af' }}>Upload WebHarvy / Octoparse / WebScraper CSV dumps directly.</span>
          </div>
        )}

        {/* Status Notice */}
        {crawlNotice && (
          <div style={{ marginTop: '12px', padding: '10px 14px', borderRadius: '8px', fontSize: '12.5px', fontWeight: '600', color: crawlNotice.includes('🎉') || crawlNotice.includes('✨') ? '#4ade80' : (crawlNotice.includes('🤖') ? '#38bdf8' : '#f87171'), background: 'rgba(0,0,0,0.5)', border: '1px solid rgba(255,255,255,0.1)' }}>
            {crawlNotice}
          </div>
        )}
      </div>

      {/* DATA SETUP MASTER TABLE VIEW */}
      {viewMode === 'table' ? (
        <div style={{ background: 'rgba(255, 255, 255, 0.04)', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: '16px', padding: '20px', backdropFilter: 'blur(16px)' }}>
          {/* Table Header & Download Bar */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '14px', fontWeight: '700', color: '#fff' }}>Showing {filteredProducts.length} records</span>
              <button
                type="button"
                onClick={toggleSelectAll}
                style={{ background: 'none', border: 'none', color: '#ec4899', fontSize: '12px', fontWeight: '600', cursor: 'pointer', textDecoration: 'underline' }}
              >
                {selectedIds.size === filteredProducts.length ? 'Deselect All' : 'Select All'}
              </button>

              <input
                type="text"
                placeholder="Search products, fabrics..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.15)', borderRadius: '8px', padding: '6px 12px', color: '#fff', fontSize: '12px', width: '180px' }}
              />

              {/* Quality & Rating Filter */}
              <select
                value={minRating}
                onChange={(e) => setMinRating(Number(e.target.value))}
                style={{ background: 'rgba(20,24,35,0.9)', border: '1px solid rgba(255,255,255,0.15)', borderRadius: '8px', padding: '6px 10px', color: '#facc15', fontSize: '12px', fontWeight: '600' }}
              >
                <option value={0}>⭐ All Ratings</option>
                <option value={3.8}>⭐ 3.8+ Stars (Clean Filter)</option>
                <option value={4.0}>⭐ 4.0+ Stars (High Quality)</option>
                <option value={4.3}>⭐ 4.3+ Stars (Viral Gems)</option>
              </select>

              {/* Bulk Actions when selected */}
              {selectedIds.size > 0 && (
                <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                  <button
                    type="button"
                    onClick={handleBulkDelete}
                    style={{ background: 'rgba(239, 68, 68, 0.25)', border: '1px solid rgba(239, 68, 68, 0.5)', color: '#f87171', padding: '6px 12px', borderRadius: '8px', fontSize: '12px', fontWeight: '700', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
                  >
                    🗑️ Delete ({selectedIds.size})
                  </button>
                  <button
                    type="button"
                    onClick={handleBulkApprove}
                    style={{ background: 'rgba(34, 197, 94, 0.25)', border: '1px solid rgba(34, 197, 94, 0.5)', color: '#4ade80', padding: '6px 12px', borderRadius: '8px', fontSize: '12px', fontWeight: '700', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
                  >
                    ✓ Publish ({selectedIds.size})
                  </button>
                </div>
              )}
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
                Publish All 🚀
              </button>
            </div>
          </div>

          {/* Table */}
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.15)', color: '#38bdf8', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  <th style={{ padding: '12px 8px', width: '35px' }}>✓</th>
                  <th style={{ padding: '12px 8px', width: '110px' }}>Photo / Gallery</th>
                  <th style={{ padding: '12px 12px' }}>Product Title & Variations</th>
                  <th style={{ padding: '12px 10px', width: '95px' }}>Wholesale</th>
                  <th style={{ padding: '12px 10px', width: '95px' }}>Retail Est.</th>
                  <th style={{ padding: '12px 10px', width: '95px' }}>Net Profit</th>
                  <th style={{ padding: '12px 12px', width: '130px' }}>Sizes Available</th>
                  <th style={{ padding: '12px 12px', width: '180px' }}>Creator Affiliate Link</th>
                  <th style={{ padding: '12px 12px', width: '120px', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredProducts.length === 0 ? (
                  <tr>
                    <td colSpan={9} style={{ textAlign: 'center', padding: '40px', color: 'rgba(255,255,255,0.5)' }}>
                      ✨ No products matching current tab. Use Smart Paste or CSV Upload above!
                    </td>
                  </tr>
                ) : (
                  filteredProducts.map((item) => {
                    const currentTitle = getVal(item.id, 'title', item.title || '');
                    const currentPrice = getVal(item.id, 'price', item.price || 245);
                    const costPrice = item.costPrice || Math.max(149, Number(currentPrice) - 100);
                    const retailEst = Math.round(Number(currentPrice) * 1.6);
                    const netMargin = retailEst - currentPrice;
                    const isSelected = selectedIds.has(item.id);
                    const gallery = item.galleryImages || (item.gallery && item.gallery.length ? item.gallery : [item.image]);
                    const currentCover = getVal(item.id, 'image', item.image);

                    return (
                      <tr key={item.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.06)', background: isSelected ? 'rgba(236, 72, 153, 0.08)' : 'transparent' }}>
                        <td style={{ padding: '10px 8px', verticalAlign: 'top' }}>
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => toggleSelect(item.id)}
                            style={{ cursor: 'pointer', accentColor: '#ec4899', marginTop: '6px' }}
                          />
                        </td>
                        <td style={{ padding: '8px', verticalAlign: 'top' }}>
                          <img
                            src={currentCover}
                            alt="preview"
                            style={{ width: '56px', height: '64px', objectFit: 'cover', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.15)', display: 'block' }}
                          />
                          {gallery.length > 1 && (
                            <div style={{ display: 'flex', gap: '3px', marginTop: '4px', maxWidth: '85px', overflowX: 'auto' }}>
                              {gallery.slice(0, 4).map((gImg, gIdx) => (
                                <img
                                  key={gIdx}
                                  src={gImg}
                                  alt="thumb"
                                  onClick={() => setVal(item.id, 'image', gImg)}
                                  title="Click to set as primary cover"
                                  style={{ width: '18px', height: '22px', objectFit: 'cover', borderRadius: '3px', cursor: 'pointer', border: currentCover === gImg ? '1px solid #ec4899' : '1px solid rgba(255,255,255,0.2)' }}
                                />
                              ))}
                            </div>
                          )}
                          <span style={{ fontSize: '9.5px', color: '#9ca3af', display: 'block', marginTop: '2px' }}>
                            📸 {gallery.length} Photos
                          </span>
                        </td>
                        <td style={{ padding: '10px 12px', fontWeight: '600', color: '#fff', verticalAlign: 'top' }}>
                          <div style={{ fontSize: '13px', lineHeight: '1.3' }}>{currentTitle}</div>
                          <div style={{ display: 'flex', gap: '6px', alignItems: 'center', marginTop: '4px', flexWrap: 'wrap' }}>
                            <span style={{ fontSize: '10px', color: '#ec4899', background: 'rgba(236, 72, 153, 0.15)', padding: '2px 6px', borderRadius: '4px' }}>
                              {item.category || 'Gen Z Streetwear'}
                            </span>
                            {item.colors && item.colors.length > 0 && (
                              <span style={{ fontSize: '10px', color: '#38bdf8', background: 'rgba(56, 189, 248, 0.12)', padding: '2px 6px', borderRadius: '4px' }}>
                                🎨 {item.colors.slice(0, 2).join(', ')}
                              </span>
                            )}
                            <span style={{ fontSize: '10px', color: '#4ade80' }}>
                              ⭐ {item.rating || '4.2'} ({item.ratingCount || '1.2k'})
                            </span>
                          </div>
                        </td>
                        <td style={{ padding: '10px 10px', color: '#4ade80', fontWeight: '700', verticalAlign: 'top' }}>
                          ₹{currentPrice}
                        </td>
                        <td style={{ padding: '10px 10px', color: '#38bdf8', fontWeight: '700', verticalAlign: 'top' }}>
                          ₹{retailEst}
                        </td>
                        <td style={{ padding: '10px 10px', color: '#facc15', fontWeight: '700', verticalAlign: 'top' }}>
                          +₹{netMargin}
                        </td>
                        <td style={{ padding: '10px 12px', verticalAlign: 'top' }}>
                          <span style={{ background: 'rgba(56, 189, 248, 0.12)', color: '#38bdf8', padding: '3px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: '600' }}>
                            {(item.sizes || ["S", "M", "L", "XL"]).join(', ')}
                          </span>
                        </td>
                        <td style={{ padding: '10px 12px', verticalAlign: 'top' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <a
                              href={item.affiliateUrl || item.productUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                              style={{ color: '#ec4899', fontSize: '11px', textDecoration: 'none', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '120px' }}
                              title={item.affiliateUrl || item.productUrl}
                            >
                              🔗 Creator Route
                            </a>
                            <button
                              type="button"
                              onClick={() => copyAffiliate(item.id, item.affiliateUrl || item.productUrl)}
                              style={{ background: copiedId === item.id ? '#22c55e' : 'rgba(255,255,255,0.1)', border: 'none', color: '#fff', padding: '2px 6px', borderRadius: '4px', fontSize: '10px', cursor: 'pointer' }}
                            >
                              {copiedId === item.id ? '✓ Copied' : '📋 Copy'}
                            </button>
                          </div>
                        </td>
                        <td style={{ padding: '10px 12px', textAlign: 'right', verticalAlign: 'top' }}>
                          <div style={{ display: 'flex', gap: '6px', justifyContent: 'flex-end' }}>
                            {item.status !== 'published' ? (
                              <button
                                type="button"
                                onClick={() => handleApprove(item)}
                                style={{ background: '#22c55e', border: 'none', color: '#fff', padding: '6px 12px', borderRadius: '6px', fontSize: '11px', fontWeight: '700', cursor: 'pointer' }}
                              >
                                ✓ Publish
                              </button>
                            ) : (
                              <span style={{ color: '#4ade80', fontSize: '11px', fontWeight: '700', padding: '4px 8px' }}>
                                ● Live
                              </span>
                            )}
                            <button
                              type="button"
                              onClick={() => handleDelete(item.id)}
                              style={{ background: 'rgba(239, 68, 68, 0.2)', border: '1px solid rgba(239, 68, 68, 0.4)', color: '#f87171', padding: '6px 8px', borderRadius: '6px', fontSize: '11px', cursor: 'pointer' }}
                              title="Discard Product"
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
          {filteredProducts.map((item) => {
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
                  <span className="inbox-tag-status">
                    {item.status === 'published' ? '● Live' : '⏳ Pending'}
                  </span>
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
                    {item.status !== 'published' && (
                      <button
                        type="button"
                        className="button button-sm button-dark"
                        onClick={() => handleApprove(item)}
                        style={{ flex: 1, background: '#22c55e', border: 'none', color: '#fff', padding: '8px', borderRadius: '8px', fontWeight: '700', cursor: 'pointer' }}
                      >
                        ✓ Publish to Storefront
                      </button>
                    )}
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
