import React, { useState, useMemo, useRef } from 'react';
import Icon from './Icon.jsx';
import { detectStore } from '../data.js';

const CATEGORY_GROUPS = [
  'All Categories',
  '📌 Pinterest Viral Drops',
  'Tops & Tunics',
  'Kurtis',
  'Dresses',
  'Bottomwear',
  'Layers & Outerwear',
  'Accessories',
  'Innerwear',
  'Ethnic Wear',
  'Beauty',
  'Home',
  'Winter'
];

const MARKETPLACES = ['All Stores', 'Amazon', 'Flipkart', 'Myntra', 'Meesho', 'Pinterest'];

function money(value) {
  return `₹${Number(value || 0).toLocaleString('en-IN')}`;
}

export default function AdminCatalogView({
  products = [],
  onApproveProduct,
  onDeleteProduct,
  onUpdateProduct,
  onOpenAddProduct,
  onOpenEditProduct,
  onBulkDeleteProducts,
  onBulkUpdateProducts
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All Categories');
  const [selectedStore, setSelectedStore] = useState('All Stores');
  const [statusFilter, setStatusFilter] = useState('all'); // 'all', 'published', 'draft', 'archived', 'missing_link', 'missing_image', 'ai_flagged'
  const [minRatingFilter, setMinRatingFilter] = useState(0);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [pageSize, setPageSize] = useState(15);
  const [page, setPage] = useState(1);
  const [copiedId, setCopiedId] = useState('');
  const [bulkCategoryTarget, setBulkCategoryTarget] = useState('Tops & Tunics');
  const [confirmModal, setConfirmModal] = useState(null); // { title, message, count, onConfirm }
  const [manageImagesProduct, setManageImagesProduct] = useState(null);
  const [imageIndexMap, setImageIndexMap] = useState({});
  const [importNotice, setImportNotice] = useState('');
  const fileInputRef = useRef(null);

  // Real Dynamic Counts
  const activeCount = useMemo(() => products.filter(p => p.status !== 'draft' && p.status !== 'pending_review' && p.status !== 'archived').length, [products]);
  const draftCount = useMemo(() => products.filter(p => p.status === 'draft' || p.status === 'pending_review').length, [products]);
  const archivedCount = useMemo(() => products.filter(p => p.status === 'archived').length, [products]);
  const missingLinkCount = useMemo(() => products.filter(p => !p.affiliateUrl).length, [products]);
  const aiFlaggedCount = useMemo(() => products.filter(p => p.aiFlagged).length, [products]);

  // Filtered dataset
  const filteredProducts = useMemo(() => {
    return products.filter((p) => {
      // 1. Search query
      const q = searchQuery.toLowerCase().trim();
      if (q) {
        const title = (p.title || '').toLowerCase();
        const cat = (p.category || '').toLowerCase();
        const id = (p.id || '').toLowerCase();
        const ext = (p.ext_id || '').toLowerCase();
        if (!title.includes(q) && !cat.includes(q) && !id.includes(q) && !ext.includes(q)) {
          return false;
        }
      }

      // 2. Category
      if (selectedCategory === '📌 Pinterest Viral Drops') {
        const isPin = Boolean(
          p.isPinterestCombo || p.isTrending || (p.collectionId || '').includes('pinterest') ||
          (p.title || '').toLowerCase().includes('jersey') || (p.title || '').toLowerCase().includes('spider') ||
          (p.title || '').toLowerCase().includes('y2k') || (p.category || '').toLowerCase().includes('accessories') ||
          (p.category || '').toLowerCase().includes('baby tees')
        );
        if (!isPin) return false;
      } else if (selectedCategory !== 'All Categories') {
        const cat = (p.category || '').toLowerCase();
        const target = selectedCategory.toLowerCase();
        if (!cat.includes(target) && (target === 'dresses' ? !cat.includes('women dresses') : true)) {
          return false;
        }
      }

      // 3. Store
      if (selectedStore !== 'All Stores') {
        const itemStore = p.store || detectStore(p.productUrl || p.affiliateUrl) || 'Meesho';
        if (selectedStore === 'Pinterest') {
          const isPin = itemStore === 'Pinterest' || Boolean(p.isPinterestCombo || (p.collectionId || '').includes('pinterest') || (p.productUrl || '').includes('pinterest'));
          if (!isPin) return false;
        } else if (itemStore.toLowerCase() !== selectedStore.toLowerCase()) {
          return false;
        }
      }

      // 4. Status Filter
      if (statusFilter === 'published') {
        if (p.status === 'draft' || p.status === 'pending_review' || p.status === 'archived') return false;
      } else if (statusFilter === 'draft') {
        if (p.status !== 'draft' && p.status !== 'pending_review') return false;
      } else if (statusFilter === 'archived') {
        if (p.status !== 'archived') return false;
      } else if (statusFilter === 'missing_link') {
        if (p.affiliateUrl) return false;
      } else if (statusFilter === 'missing_image') {
        if (p.image && !p.image.includes('placeholder')) return false;
      } else if (statusFilter === 'ai_flagged') {
        if (!p.aiFlagged) return false;
      }

      // 5. Min Rating
      if (minRatingFilter > 0) {
        const r = Number(p.rating || 4.2);
        if (r < minRatingFilter) return false;
      }

      return true;
    });
  }, [products, searchQuery, selectedCategory, selectedStore, statusFilter, minRatingFilter]);

  const totalPages = Math.max(1, Math.ceil(filteredProducts.length / pageSize));
  const paginatedProducts = useMemo(() => {
    const start = (page - 1) * pageSize;
    return filteredProducts.slice(start, start + pageSize);
  }, [filteredProducts, page, pageSize]);

  const toggleSelect = (id) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleSelectPage = () => {
    const pageIds = paginatedProducts.map(p => p.id);
    const allPageSelected = pageIds.length > 0 && pageIds.every(id => selectedIds.has(id));
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (allPageSelected) {
        pageIds.forEach(id => next.delete(id));
      } else {
        pageIds.forEach(id => next.add(id));
      }
      return next;
    });
  };

  const toggleSelectAllFiltered = () => {
    if (selectedIds.size === filteredProducts.length && filteredProducts.length > 0) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredProducts.map(p => p.id)));
    }
  };

  // Bulk Archive / Move to Trash
  const handleBulkArchive = () => {
    if (selectedIds.size === 0) return;
    setConfirmModal({
      title: 'Move to Archive / Trash',
      message: `Are you sure you want to move ${selectedIds.size} selected product(s) to Archive? They will be hidden from the public store but can be restored anytime.`,
      count: selectedIds.size,
      confirmLabel: 'Move to Archive',
      confirmColor: 'var(--ink)',
      onConfirm: async () => {
        for (const id of selectedIds) {
          await onUpdateProduct?.(id, { status: 'archived' });
        }
        setSelectedIds(new Set());
        setConfirmModal(null);
      }
    });
  };

  // Bulk Restore from Archive
  const handleBulkRestore = () => {
    if (selectedIds.size === 0) return;
    setConfirmModal({
      title: 'Restore to Live Store',
      message: `Restore ${selectedIds.size} product(s) back to Live Storefront?`,
      count: selectedIds.size,
      confirmLabel: 'Restore to Live',
      confirmColor: 'var(--green-deep)',
      onConfirm: async () => {
        for (const id of selectedIds) {
          await onUpdateProduct?.(id, { status: 'published' });
        }
        setSelectedIds(new Set());
        setConfirmModal(null);
      }
    });
  };

  // Bulk Permanent Delete
  const handleBulkPermanentDelete = () => {
    if (selectedIds.size === 0) return;
    setConfirmModal({
      title: '⚠️ Permanent Delete Confirmation',
      message: `Are you sure you want to permanently delete ${selectedIds.size} product(s)? This will delete them from the SQLite database and JSON catalog permanently.`,
      count: selectedIds.size,
      confirmLabel: 'Delete Permanently',
      confirmColor: '#dc2626',
      onConfirm: async () => {
        const idList = Array.from(selectedIds);
        if (onBulkDeleteProducts) {
          await onBulkDeleteProducts(idList);
        } else {
          for (const id of idList) {
            await onDeleteProduct?.(id);
          }
        }
        setSelectedIds(new Set());
        setConfirmModal(null);
      }
    });
  };

  const handleBulkChangeCategory = async () => {
    if (selectedIds.size === 0) return;
    const idList = Array.from(selectedIds);
    if (onBulkUpdateProducts) {
      const updates = idList.map(id => ({ id, patch: { category: bulkCategoryTarget } }));
      await onBulkUpdateProducts(updates);
    } else {
      for (const id of idList) {
        await onUpdateProduct?.(id, { category: bulkCategoryTarget });
      }
    }
    setSelectedIds(new Set());
  };

  const copyAffiliate = (id, url) => {
    if (!url) return;
    navigator.clipboard.writeText(url);
    setCopiedId(id);
    setTimeout(() => setCopiedId(''), 2000);
  };

  // Extension CSV Batch Import Handler (Exact ext_id matching)
  const handleCSVUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (event) => {
      try {
        const text = event.target?.result;
        if (typeof text !== 'string') return;
        const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
        if (lines.length < 2) {
          setImportNotice('CSV is empty or invalid format.');
          return;
        }

        const headers = lines[0].split(',').map(h => h.replace(/^["']|["']$/g, '').trim().toLowerCase());
        let updatedCount = 0;

        for (let i = 1; i < lines.length; i++) {
          const cols = lines[i].split(',').map(c => c.replace(/^["']|["']$/g, '').trim());
          const row = {};
          headers.forEach((h, idx) => { row[h] = cols[idx] || ''; });

          // Check if it's from Creator Link Batcher (contains affiliate_url and ext_id / product_id)
          const extId = row.ext_id || row.product_id || row.p_id || '';
          const affUrl = row.affiliate_url || row.link || '';

          if (extId && affUrl) {
            const matched = products.find(p => (p.ext_id && String(p.ext_id).toLowerCase() === extId.toLowerCase()) || (p.id && String(p.id).toLowerCase().includes(extId.toLowerCase())));
            if (matched) {
              await onUpdateProduct?.(matched.id, { affiliateUrl: affUrl });
              updatedCount++;
            }
          }
        }

        setImportNotice(`✨ Successfully matched and updated ${updatedCount} products by exact Meesho Product ID!`);
        setTimeout(() => setImportNotice(''), 6000);
      } catch (err) {
        setImportNotice('Error parsing CSV file: ' + err.message);
      }
    };
    reader.readAsText(file);
  };

  const exportCSV = () => {
    const items = filteredProducts.length ? filteredProducts : products;
    if (!items.length) return;

    const rows = [
      ["ID", "Ext ID", "Title", "Category", "Store", "Price", "Rating", "Image URL", "Product URL", "Affiliate URL", "Status"]
    ];

    items.forEach((p) => {
      rows.push([
        `"${p.id || ''}"`,
        `"${p.ext_id || ''}"`,
        `"${(p.title || '').replace(/"/g, '""')}"`,
        `"${p.category || 'Tops & Tunics'}"`,
        `"${p.store || 'Meesho'}"`,
        `"₹${p.price || 0}"`,
        `"${p.rating || 4.3}"`,
        `"${p.image || ''}"`,
        `"${p.productUrl || ''}"`,
        `"${p.affiliateUrl || ''}"`,
        `"${p.status || 'published'}"`
      ]);
    });

    const csvContent = "data:text/csv;charset=utf-8," + rows.map(e => e.join(",")).join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `catalog_export_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="admin-catalog-view" style={{ maxWidth: '1440px', margin: '0 auto', padding: '24px 20px' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: '800', color: 'var(--ink)', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span>📦 Master Catalog Control</span>
            <span style={{ fontSize: '12px', background: 'var(--green-pale)', color: 'var(--green-deep)', border: '1px solid var(--line)', padding: '3px 10px', borderRadius: '999px', fontWeight: '700' }}>
              {products.length} Real Database Products
            </span>
          </h1>
          <p style={{ fontSize: '13px', color: 'var(--muted)', marginTop: '4px' }}>
            Live SQLite Database &amp; Catalog Management · Filter, categorize, bulk archive, delete, and match Creator affiliate links.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleCSVUpload} 
            accept=".csv" 
            style={{ display: 'none' }} 
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="button button-light"
            style={{ fontSize: '12.5px', padding: '9px 14px' }}
            title="Import Meesho extension CSV or affiliate link batch"
          >
            <Icon name="download" size={15} /> Batch Import CSV
          </button>
          <button
            type="button"
            onClick={onOpenAddProduct}
            className="button button-dark"
            style={{ fontSize: '12.5px', padding: '9px 16px' }}
          >
            <Icon name="plus" size={15} /> Add Product
          </button>
          <button
            type="button"
            onClick={exportCSV}
            className="button button-light"
            style={{ fontSize: '12.5px', padding: '9px 14px' }}
          >
            Export CSV
          </button>
        </div>
      </div>

      {/* Import Notice Alert */}
      {importNotice && (
        <div style={{ background: 'var(--green-pale)', border: '1px solid var(--green)', color: 'var(--green-deep)', padding: '10px 16px', borderRadius: '10px', marginBottom: '16px', fontSize: '13px', fontWeight: '600' }}>
          {importNotice}
        </div>
      )}

      {/* Real Summary Status Pills */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', flexWrap: 'wrap' }}>
        <button 
          type="button" 
          onClick={() => { setStatusFilter('all'); setPage(1); }}
          className={`filter-chip${statusFilter === 'all' ? ' is-active' : ''}`}
        >
          All ({products.length})
        </button>
        <button 
          type="button" 
          onClick={() => { setStatusFilter('published'); setPage(1); }}
          className={`filter-chip${statusFilter === 'published' ? ' is-active' : ''}`}
        >
          ● Live Storefront ({activeCount})
        </button>
        <button 
          type="button" 
          onClick={() => { setStatusFilter('draft'); setPage(1); }}
          className={`filter-chip${statusFilter === 'draft' ? ' is-active' : ''}`}
        >
          ⏳ Drafts / Review ({draftCount})
        </button>
        <button 
          type="button" 
          onClick={() => { setStatusFilter('archived'); setPage(1); }}
          className={`filter-chip${statusFilter === 'archived' ? ' is-active' : ''}`}
        >
          📁 Archive / Trash ({archivedCount})
        </button>
        <button 
          type="button" 
          onClick={() => { setStatusFilter('missing_link'); setPage(1); }}
          className={`filter-chip${statusFilter === 'missing_link' ? ' is-active' : ''}`}
        >
          ⚠️ Missing Affiliate Link ({missingLinkCount})
        </button>
        <button 
          type="button" 
          onClick={() => { setStatusFilter('ai_flagged'); setPage(1); }}
          className={`filter-chip${statusFilter === 'ai_flagged' ? ' is-active' : ''}`}
          style={aiFlaggedCount > 0 ? {
            borderColor: '#ef4444',
            color: statusFilter === 'ai_flagged' ? '#fff' : '#dc2626',
            background: statusFilter === 'ai_flagged' ? '#dc2626' : 'rgba(239, 68, 68, 0.08)',
            fontWeight: '700'
          } : {}}
        >
          🚨 AI Flagged ({aiFlaggedCount})
        </button>
      </div>

      {/* Filter Control Bar */}
      <div style={{ background: 'var(--paper)', border: '1px solid var(--line)', borderRadius: '16px', padding: '16px', marginBottom: '20px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1.2fr 1fr 1fr', gap: '10px', alignItems: 'center' }}>
          {/* Search */}
          <div>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => { setSearchQuery(e.target.value); setPage(1); }}
              placeholder="Search by title, category, ext_id, product ID..."
              style={{ width: '100%', borderRadius: '10px', padding: '9px 14px', background: 'var(--canvas)', border: '1px solid var(--line)', color: 'var(--ink)', fontSize: '13px' }}
            />
          </div>

          {/* Category Dropdown */}
          <select
            value={selectedCategory}
            onChange={(e) => { setSelectedCategory(e.target.value); setPage(1); }}
            style={{ borderRadius: '10px', padding: '9px', background: 'var(--canvas)', border: '1px solid var(--line)', color: 'var(--ink)', fontSize: '12px' }}
          >
            {CATEGORY_GROUPS.map((cat) => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>

          {/* Store Dropdown */}
          <select
            value={selectedStore}
            onChange={(e) => { setSelectedStore(e.target.value); setPage(1); }}
            style={{ borderRadius: '10px', padding: '9px', background: 'var(--canvas)', border: '1px solid var(--line)', color: 'var(--ink)', fontSize: '12px' }}
          >
            {MARKETPLACES.map((st) => (
              <option key={st} value={st}>{st}</option>
            ))}
          </select>

          {/* Min Rating */}
          <select
            value={minRatingFilter}
            onChange={(e) => { setMinRatingFilter(Number(e.target.value)); setPage(1); }}
            style={{ borderRadius: '10px', padding: '9px', background: 'var(--canvas)', border: '1px solid var(--line)', color: 'var(--ink)', fontSize: '12px' }}
          >
            <option value="0">All Ratings</option>
            <option value="3.8">⭐ 3.8+ Quality</option>
            <option value="4.0">⭐ 4.0+ High Quality</option>
            <option value="4.3">⭐ 4.3+ Top Rated</option>
          </select>
        </div>
      </div>

      {/* Bulk Action Toolbar */}
      {selectedIds.size > 0 && (
        <div style={{ background: 'var(--paper-raised, var(--paper))', border: '1px solid var(--green)', borderRadius: '12px', padding: '12px 18px', marginBottom: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '13px', fontWeight: '750', color: 'var(--green-deep)' }}>
              ✓ {selectedIds.size} Selected
            </span>
            <button
              type="button"
              onClick={toggleSelectAllFiltered}
              style={{ fontSize: '11.5px', background: 'none', border: 'none', color: 'var(--ink)', textDecoration: 'underline', cursor: 'pointer' }}
            >
              {selectedIds.size === filteredProducts.length ? 'Deselect all' : `Select all ${filteredProducts.length} filtered`}
            </button>
          </div>

          <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
            {/* Category target */}
            <select
              value={bulkCategoryTarget}
              onChange={(e) => setBulkCategoryTarget(e.target.value)}
              style={{ borderRadius: '8px', padding: '6px 10px', background: 'var(--canvas)', border: '1px solid var(--line)', color: 'var(--ink)', fontSize: '11.5px' }}
            >
              {CATEGORY_GROUPS.filter(c => c !== 'All Categories' && !c.includes('📌')).map(c => (
                <option key={c} value={c}>Move to: {c}</option>
              ))}
            </select>
            <button
              type="button"
              onClick={handleBulkChangeCategory}
              className="button button-light"
              style={{ fontSize: '11.5px', padding: '6px 10px' }}
            >
              Apply Category
            </button>

            {statusFilter === 'archived' ? (
              <button
                type="button"
                onClick={handleBulkRestore}
                className="button button-dark"
                style={{ fontSize: '11.5px', padding: '6px 12px' }}
              >
                Restore to Live
              </button>
            ) : (
              <button
                type="button"
                onClick={handleBulkArchive}
                className="button button-light"
                style={{ fontSize: '11.5px', padding: '6px 12px' }}
              >
                📁 Move to Archive
              </button>
            )}

            <button
              type="button"
              onClick={handleBulkPermanentDelete}
              style={{ background: 'rgba(220, 38, 38, 0.1)', color: '#dc2626', border: '1px solid rgba(220, 38, 38, 0.3)', borderRadius: '8px', padding: '6px 12px', fontSize: '11.5px', fontWeight: '700', cursor: 'pointer' }}
            >
              🗑️ Delete Permanently
            </button>
          </div>
        </div>
      )}

      {/* Main Table */}
      <div style={{ background: 'var(--paper)', border: '1px solid var(--line)', borderRadius: '16px', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '12.5px' }}>
          <thead>
            <tr style={{ background: 'var(--canvas)', borderBottom: '1px solid var(--line)', color: 'var(--muted)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              <th style={{ padding: '12px 16px', width: '40px' }}>
                <input
                  type="checkbox"
                  checked={paginatedProducts.length > 0 && paginatedProducts.every(p => selectedIds.has(p.id))}
                  onChange={toggleSelectPage}
                  aria-label="Select page"
                />
              </th>
              <th style={{ padding: '12px 10px', width: '88px' }}>Photos</th>
              <th style={{ padding: '12px 14px' }}>Product Title &amp; Details</th>
              <th style={{ padding: '12px 14px', width: '140px' }}>Category</th>
              <th style={{ padding: '12px 14px', width: '90px' }}>Price</th>
              <th style={{ padding: '12px 14px', width: '120px' }}>Affiliate Link</th>
              <th style={{ padding: '12px 14px', width: '100px' }}>Status</th>
              <th style={{ padding: '12px 14px', width: '90px', textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {paginatedProducts.length === 0 ? (
              <tr>
                <td colSpan={8} style={{ padding: '40px 20px', textAlign: 'center', color: 'var(--muted)' }}>
                  No matching products found. Try clearing filters or search query.
                </td>
              </tr>
            ) : (
              paginatedProducts.map((p) => {
                const isSelected = selectedIds.has(p.id);
                const hasAffiliate = Boolean(p.affiliateUrl);
                const productImages = (Array.isArray(p.images) && p.images.length > 0)
                  ? p.images
                  : (Array.isArray(p.galleryImages) && p.galleryImages.length > 0)
                    ? p.galleryImages
                    : [p.image || '/images/meesho-dress-ae6lv9.webp'];
                const activeImgIdx = (imageIndexMap[p.id] !== undefined)
                  ? Math.min(imageIndexMap[p.id], productImages.length - 1)
                  : 0;
                const currentImg = productImages[activeImgIdx] || productImages[0];

                return (
                  <tr
                    key={p.id}
                    style={{
                      borderBottom: '1px solid var(--line)',
                      background: isSelected ? 'var(--green-pale)' : p.aiFlagged ? 'rgba(239, 68, 68, 0.03)' : 'transparent',
                      transition: 'background 0.15s ease'
                    }}
                  >
                    <td style={{ padding: '12px 16px' }}>
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleSelect(p.id)}
                        aria-label={`Select ${p.title}`}
                      />
                    </td>
                    <td style={{ padding: '10px' }}>
                      <div style={{ position: 'relative', width: '56px', height: '70px', borderRadius: '8px', overflow: 'hidden', background: 'var(--canvas)', border: p.aiFlagged ? '2px solid #ef4444' : '1px solid var(--line)', boxShadow: '0 2px 6px rgba(0,0,0,0.06)' }}>
                        <img
                          src={currentImg}
                          alt={p.title}
                          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                          loading="lazy"
                        />
                        {p.aiFlagged && (
                          <span
                            style={{
                              position: 'absolute',
                              top: '2px',
                              left: '2px',
                              background: '#ef4444',
                              color: '#fff',
                              fontSize: '8px',
                              fontWeight: '800',
                              padding: '1px 3px',
                              borderRadius: '3px',
                              letterSpacing: '0.02em',
                              lineHeight: '1.2'
                            }}
                            title={p.aiFlagReason || 'AI Image Flagged'}
                          >
                            AI
                          </span>
                        )}
                        {productImages.length > 1 && (
                          <div style={{ position: 'absolute', bottom: '0', left: '0', right: '0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1px 2px', background: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(3px)', color: '#fff', fontSize: '9px', fontWeight: '700' }}>
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                setImageIndexMap(prev => ({
                                  ...prev,
                                  [p.id]: (activeImgIdx - 1 + productImages.length) % productImages.length
                                }));
                              }}
                              style={{ background: 'transparent', border: 'none', color: '#fff', cursor: 'pointer', padding: '0 2px', fontSize: '11px', lineHeight: '1' }}
                              title="Previous Photo Variation"
                            >
                              ‹
                            </button>
                            <span style={{ fontSize: '8px' }}>{activeImgIdx + 1}/{productImages.length}</span>
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                setImageIndexMap(prev => ({
                                  ...prev,
                                  [p.id]: (activeImgIdx + 1) % productImages.length
                                }));
                              }}
                              style={{ background: 'transparent', border: 'none', color: '#fff', cursor: 'pointer', padding: '0 2px', fontSize: '11px', lineHeight: '1' }}
                              title="Next Photo Variation"
                            >
                              ›
                            </button>
                          </div>
                        )}
                      </div>
                      <button
                        type="button"
                        onClick={() => setManageImagesProduct(p)}
                        style={{
                          marginTop: '4px',
                          fontSize: '9.5px',
                          padding: '2px 5px',
                          background: 'var(--canvas)',
                          border: '1px solid var(--line)',
                          borderRadius: '5px',
                          cursor: 'pointer',
                          color: 'var(--ink)',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '2px',
                          fontWeight: '600',
                          whiteSpace: 'nowrap'
                        }}
                        title="Add or manage images / color variations"
                      >
                        <span>➕ {productImages.length > 1 ? `${productImages.length} Imgs` : 'Add'}</span>
                      </button>
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <strong style={{ display: 'block', color: 'var(--ink)', fontSize: '13px', lineHeight: '1.4' }}>
                        {p.title}
                      </strong>
                      <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginTop: '4px', fontSize: '11px', color: 'var(--muted)', flexWrap: 'wrap' }}>
                        <span>Store: {p.store || 'Meesho'}</span>
                        <span>·</span>
                        <span>ID: {p.ext_id || p.id}</span>
                        {p.rating && <span>· ⭐ {p.rating}</span>}
                        {productImages.length > 1 && (
                          <span style={{ color: 'var(--green-deep)', fontWeight: '600' }}>
                            · 📸 {productImages.length} Variations
                          </span>
                        )}
                      </div>
                      {p.aiFlagged && (
                        <div style={{
                          marginTop: '6px',
                          padding: '4px 8px',
                          borderRadius: '6px',
                          background: 'rgba(239, 68, 68, 0.08)',
                          border: '1px solid rgba(239, 68, 68, 0.3)',
                          color: '#dc2626',
                          fontSize: '11px',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          flexWrap: 'wrap'
                        }}>
                          <span style={{ fontWeight: '700' }}>🚨 AI / Low-Res Image Detected:</span>
                          <span style={{ opacity: 0.9, fontSize: '10.5px' }}>{p.aiFlagReason || 'Synthetic AI Watermark'}</span>

                          <button
                            type="button"
                            onClick={() => setManageImagesProduct(p)}
                            style={{
                              marginLeft: 'auto',
                              background: '#dc2626',
                              color: '#fff',
                              border: 'none',
                              borderRadius: '4px',
                              padding: '2px 8px',
                              fontSize: '10px',
                              fontWeight: '700',
                              cursor: 'pointer'
                            }}
                          >
                            Replace Photo
                          </button>
                        </div>
                      )}
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <span style={{ display: 'inline-block', padding: '3px 8px', borderRadius: '6px', background: 'var(--canvas)', border: '1px solid var(--line)', color: 'var(--ink)', fontSize: '11px', fontWeight: '600' }}>
                        {p.category || 'Fashion'}
                      </span>
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <strong style={{ color: 'var(--ink)', fontSize: '13px' }}>
                        {money(p.price)}
                      </strong>
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      {hasAffiliate ? (
                        <button
                          type="button"
                          onClick={() => copyAffiliate(p.id, p.affiliateUrl)}
                          style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', background: 'var(--green-pale)', color: 'var(--green-deep)', border: '1px solid var(--green)', borderRadius: '6px', padding: '4px 8px', fontSize: '11px', fontWeight: '700', cursor: 'pointer' }}
                          title="Click to copy affiliate link"
                        >
                          {copiedId === p.id ? '✓ Copied' : '🔗 Link Ready'}
                        </button>
                      ) : (
                        <span style={{ color: '#d97706', fontSize: '11px', fontWeight: '600' }}>
                          ⚠️ Missing Link
                        </span>
                      )}
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <span style={{
                        display: 'inline-block',
                        padding: '3px 8px',
                        borderRadius: '6px',
                        fontSize: '11px',
                        fontWeight: '700',
                        background: p.status === 'archived' ? 'rgba(100,116,139,0.15)' : (p.status === 'draft' || p.status === 'pending_review') ? 'rgba(234,179,8,0.15)' : 'rgba(34,197,94,0.15)',
                        color: p.status === 'archived' ? 'var(--muted)' : (p.status === 'draft' || p.status === 'pending_review') ? '#b45309' : '#15803d'
                      }}>
                        {p.status === 'archived' ? 'Archived' : (p.status === 'draft' || p.status === 'pending_review') ? 'Draft' : 'Live'}
                      </span>
                    </td>
                    <td style={{ padding: '12px 14px', textAlign: 'right' }}>
                      <div style={{ display: 'flex', gap: '6px', justifyContent: 'flex-end' }}>
                        <button
                          type="button"
                          onClick={() => onOpenEditProduct?.(p)}
                          style={{ background: 'var(--canvas)', border: '1px solid var(--line)', borderRadius: '6px', width: '28px', height: '28px', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', color: 'var(--ink)' }}
                          title="Edit Product"
                        >
                          ✏️
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            setConfirmModal({
                              title: 'Delete Product',
                              message: `Are you sure you want to delete "${p.title}"?`,
                              count: 1,
                              confirmLabel: 'Delete',
                              confirmColor: '#dc2626',
                              onConfirm: async () => {
                                await onDeleteProduct?.(p.id);
                                setConfirmModal(null);
                              }
                            });
                          }}
                          style={{ background: 'rgba(220, 38, 38, 0.08)', border: '1px solid rgba(220, 38, 38, 0.2)', borderRadius: '6px', width: '28px', height: '28px', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', color: '#dc2626' }}
                          title="Delete Product"
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

        {/* Pagination Bar */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 18px', borderTop: '1px solid var(--line)', background: 'var(--canvas)', flexWrap: 'wrap', gap: '10px' }}>
          <span style={{ fontSize: '12px', color: 'var(--muted)' }}>
            Showing {filteredProducts.length > 0 ? (page - 1) * pageSize + 1 : 0} - {Math.min(page * pageSize, filteredProducts.length)} of {filteredProducts.length} filtered items
          </span>

          <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => setPage(p => Math.max(1, p - 1))}
              className="button button-light"
              style={{ fontSize: '12px', padding: '5px 10px', opacity: page <= 1 ? 0.4 : 1 }}
            >
              Previous
            </button>
            <span style={{ fontSize: '12px', color: 'var(--ink)', padding: '0 8px' }}>
              Page {page} of {totalPages}
            </span>
            <button
              type="button"
              disabled={page >= totalPages}
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              className="button button-light"
              style={{ fontSize: '12px', padding: '5px 10px', opacity: page >= totalPages ? 0.4 : 1 }}
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Confirmation Modal */}
      {confirmModal && (
        <div className="modal-backdrop" style={{ zIndex: 10002 }} onClick={() => setConfirmModal(null)}>
          <div className="modal-card" style={{ maxWidth: '440px', padding: '24px' }} onClick={e => e.stopPropagation()}>
            <h3 style={{ fontSize: '18px', margin: '0 0 10px', color: 'var(--ink)' }}>{confirmModal.title}</h3>
            <p style={{ fontSize: '13px', color: 'var(--muted)', lineHeight: '1.5', margin: '0 0 20px' }}>{confirmModal.message}</p>
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                type="button"
                className="button button-light"
                onClick={() => setConfirmModal(null)}
              >
                Cancel
              </button>
              <button
                type="button"
                style={{ background: confirmModal.confirmColor || 'var(--ink)', color: '#fff', border: 'none', borderRadius: '10px', padding: '8px 16px', fontSize: '13px', fontWeight: '700', cursor: 'pointer' }}
                onClick={confirmModal.onConfirm}
              >
                {confirmModal.confirmLabel || 'Confirm'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Multi-Image Variation Management Modal */}
      {manageImagesProduct && (
        <ManageImagesModal
          product={manageImagesProduct}
          onClose={() => setManageImagesProduct(null)}
          onSave={async (updatedProduct) => {
            await onUpdateProduct?.(updatedProduct.id, updatedProduct);
            setManageImagesProduct(null);
          }}
        />
      )}
    </div>
  );
}

function ManageImagesModal({ product, onClose, onSave }) {
  const [urlsInput, setUrlsInput] = useState('');
  const initialImages = (Array.isArray(product.images) && product.images.length > 0)
    ? [...product.images]
    : (Array.isArray(product.galleryImages) && product.galleryImages.length > 0)
      ? [...product.galleryImages]
      : [product.image || '/images/meesho-dress-ae6lv9.webp'];
  const [imageList, setImageList] = useState(initialImages);
  const [saving, setSaving] = useState(false);

  const handleAddUrls = (e) => {
    e.preventDefault();
    const newItems = urlsInput
      .split(/[\n,]+/)
      .map(u => u.trim())
      .filter(u => u.length > 5);
    if (newItems.length > 0) {
      setImageList(prev => [...prev, ...newItems]);
      setUrlsInput('');
    }
  };

  const handleRemoveImage = (index) => {
    if (imageList.length <= 1) {
      alert('A product must retain at least 1 image.');
      return;
    }
    setImageList(prev => prev.filter((_, i) => i !== index));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave({
        ...product,
        images: imageList,
        image: imageList[0],
        aiFlagged: false,
        aiFlagReason: ''
      });
      onClose();
    } catch (err) {
      alert(`Could not save images: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-backdrop" style={{ zIndex: 10003 }} onClick={onClose}>
      <div className="modal-card" style={{ maxWidth: '640px', padding: '24px', maxHeight: '90vh', overflowY: 'auto' }} onClick={e => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h3 style={{ fontSize: '18px', fontWeight: '800', margin: 0, color: 'var(--ink)' }}>
              📸 Manage Product Images &amp; Variations
            </h3>
            <p style={{ fontSize: '12px', color: 'var(--muted)', margin: '4px 0 0' }}>
              {product.title}
            </p>
          </div>
          <button type="button" onClick={onClose} style={{ background: 'none', border: 'none', fontSize: '20px', cursor: 'pointer', color: 'var(--muted)' }}>✕</button>
        </div>

        {/* Existing Images Grid */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', color: 'var(--ink)', marginBottom: '8px' }}>
            Current Photos ({imageList.length}) · Leftmost is Primary
          </label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(90px, 1fr))', gap: '10px' }}>
            {imageList.map((imgUrl, idx) => (
              <div key={idx} style={{ position: 'relative', width: '100%', height: '115px', borderRadius: '8px', overflow: 'hidden', border: idx === 0 ? '2px solid var(--green)' : '1px solid var(--line)', background: 'var(--canvas)' }}>
                <img src={imgUrl} alt={`Photo ${idx + 1}`} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                {idx === 0 && (
                  <span style={{ position: 'absolute', bottom: '3px', left: '3px', right: '3px', textAlign: 'center', background: 'var(--green-deep)', color: '#fff', fontSize: '8.5px', fontWeight: '800', borderRadius: '3px', padding: '1px 0' }}>
                    COVER
                  </span>
                )}
                <button
                  type="button"
                  onClick={() => handleRemoveImage(idx)}
                  title="Remove this photo"
                  style={{ position: 'absolute', top: '3px', right: '3px', background: 'rgba(220, 38, 38, 0.85)', color: '#fff', border: 'none', borderRadius: '50%', width: '20px', height: '20px', display: 'grid', placeItems: 'center', fontSize: '11px', cursor: 'pointer' }}
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Add New URLs Form */}
        <div style={{ background: 'var(--canvas)', border: '1px solid var(--line)', borderRadius: '12px', padding: '14px', marginBottom: '20px' }}>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', color: 'var(--ink)', marginBottom: '6px' }}>
            ➕ Add More Image URLs (Meesho / Myntra / Amazon variation links)
          </label>
          <textarea
            rows={3}
            value={urlsInput}
            onChange={e => setUrlsInput(e.target.value)}
            placeholder="Paste image URLs here (one per line or comma-separated)&#10;e.g. https://images.meesho.com/images/products/..."
            style={{ width: '100%', padding: '8px 10px', fontSize: '12px', borderRadius: '8px', border: '1px solid var(--line)', background: 'var(--paper)', color: 'var(--ink)', boxSizing: 'border-box', fontFamily: 'inherit' }}
          />
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '8px' }}>
            <button
              type="button"
              onClick={handleAddUrls}
              className="button button-light"
              style={{ fontSize: '12px', padding: '6px 12px' }}
            >
              Add to Photos
            </button>
          </div>
        </div>

        {/* Modal Actions */}
        <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
          <button type="button" className="button button-light" onClick={onClose} disabled={saving}>
            Cancel
          </button>
          <button
            type="button"
            className="button button-dark"
            onClick={handleSave}
            disabled={saving}
            style={{ padding: '8px 18px', fontSize: '13px' }}
          >
            {saving ? 'Saving...' : '💾 Save Photos & Clear AI Flag'}
          </button>
        </div>
      </div>
    </div>
  );
}
