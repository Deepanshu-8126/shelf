import React, { useState, useMemo } from 'react';
import Icon from './Icon';

const CATEGORY_GROUPS = [
  'All Categories',
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

const MARKETPLACES = ['All Stores', 'Meesho', 'Amazon', 'Zara', 'Savana', 'H&M'];

export default function AdminCatalogView({
  products = [],
  onApproveProduct,
  onDeleteProduct,
  onUpdateProduct,
  onOpenAddProduct,
  onOpenEditProduct
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All Categories');
  const [selectedStore, setSelectedStore] = useState('All Stores');
  const [statusFilter, setStatusFilter] = useState('all'); // 'all', 'published', 'draft', 'missing_link', 'missing_image'
  const [minRatingFilter, setMinRatingFilter] = useState(0);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [pageSize, setPageSize] = useState(15);
  const [page, setPage] = useState(1);
  const [copiedId, setCopiedId] = useState('');
  const [bulkCategoryTarget, setBulkCategoryTarget] = useState('Tops & Tunics');

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
      if (selectedCategory !== 'All Categories') {
        const cat = (p.category || '').toLowerCase();
        const target = selectedCategory.toLowerCase();
        if (!cat.includes(target) && (target === 'dresses' ? !cat.includes('women dresses') : true)) {
          return false;
        }
      }

      // 3. Store
      if (selectedStore !== 'All Stores') {
        if ((p.store || 'Meesho').toLowerCase() !== selectedStore.toLowerCase()) {
          return false;
        }
      }

      // 4. Status Filter
      if (statusFilter === 'published') {
        if (p.status !== 'published') return false;
      } else if (statusFilter === 'draft') {
        if (p.status === 'published') return false;
      } else if (statusFilter === 'missing_link') {
        if (p.affiliateUrl) return false;
      } else if (statusFilter === 'missing_image') {
        if (p.image && !p.image.includes('placeholder')) return false;
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
    const allPageSelected = pageIds.every(id => selectedIds.has(id));
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
    if (selectedIds.size === filteredProducts.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredProducts.map(p => p.id)));
    }
  };

  const handleBulkDelete = async () => {
    if (selectedIds.size === 0) return;
    if (!window.confirm(`⚠️ Are you sure you want to permanently delete ${selectedIds.size} selected products? They will be removed from your live store and database.`)) return;
    for (const id of selectedIds) {
      await onDeleteProduct?.(id);
    }
    setSelectedIds(new Set());
  };

  const handleBulkPublish = async () => {
    if (selectedIds.size === 0) return;
    for (const id of selectedIds) {
      const prod = products.find(p => p.id === id);
      if (prod) await onApproveProduct?.({ ...prod, status: 'published' });
    }
    setSelectedIds(new Set());
  };

  const handleBulkMoveToDraft = async () => {
    if (selectedIds.size === 0) return;
    for (const id of selectedIds) {
      const prod = products.find(p => p.id === id);
      if (prod) await onApproveProduct?.({ ...prod, status: 'draft' });
    }
    setSelectedIds(new Set());
  };

  const handleBulkChangeCategory = async () => {
    if (selectedIds.size === 0) return;
    for (const id of selectedIds) {
      const prod = products.find(p => p.id === id);
      if (prod) await onApproveProduct?.({ ...prod, category: bulkCategoryTarget });
    }
    setSelectedIds(new Set());
  };

  const copyAffiliate = (id, url) => {
    if (!url) return;
    navigator.clipboard.writeText(url);
    setCopiedId(id);
    setTimeout(() => setCopiedId(''), 2000);
  };

  const exportCSV = () => {
    const items = filteredProducts.length ? filteredProducts : products;
    if (!items.length) return;

    const rows = [
      ["ID", "Title", "Category", "Store", "Wholesale Cost", "Retail Price", "Est Profit", "Rating", "Sizes", "Image URL", "Product URL", "Affiliate URL", "Status"]
    ];

    items.forEach((p) => {
      const wholesale = p.costPrice || Math.max(149, Number(p.price || 245) - 100);
      const retail = p.price || 399;
      const profit = Math.max(0, retail - wholesale);
      const sizes = (p.sizes || ["S", "M", "L", "XL"]).join(', ');

      rows.push([
        `"${p.id}"`,
        `"${(p.title || '').replace(/"/g, '""')}"`,
        `"${p.category || 'Tops & Tunics'}"`,
        `"${p.store || 'Meesho'}"`,
        `"₹${wholesale}"`,
        `"₹${retail}"`,
        `"₹${profit}"`,
        `"${p.rating || 4.3}"`,
        `"${sizes}"`,
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
          <h1 style={{ fontSize: '24px', fontWeight: '800', color: '#fff', display: 'flex', alignItems: 'center', gap: '10px' }}>
            📦 Products &amp; Master Catalog
            <span style={{ fontSize: '12px', background: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8', border: '1px solid rgba(56, 189, 248, 0.3)', padding: '3px 10px', borderRadius: '999px', fontWeight: '700' }}>
              {products.length} Items Total
            </span>
          </h1>
          <p style={{ fontSize: '13px', color: 'rgba(255, 255, 255, 0.65)', marginTop: '4px' }}>
            Manage live public inventory, edit pricing &amp; profit margins, filter by quality rating, and perform bulk operations.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
          <button
            type="button"
            onClick={onOpenAddProduct}
            style={{ background: 'linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%)', color: '#fff', border: 'none', borderRadius: '10px', padding: '10px 18px', fontSize: '13px', fontWeight: '700', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <Icon name="plus" size={16} /> Add Manual Pick
          </button>
          <button
            type="button"
            onClick={exportCSV}
            style={{ background: 'rgba(255, 255, 255, 0.08)', color: '#fff', border: '1px solid rgba(255, 255, 255, 0.15)', borderRadius: '10px', padding: '10px 16px', fontSize: '13px', fontWeight: '600', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            📥 Export CSV
          </button>
        </div>
      </div>

      {/* Filter Control Bar */}
      <div style={{ background: 'rgba(255, 255, 255, 0.04)', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: '16px', padding: '16px', marginBottom: '20px', backdropFilter: 'blur(16px)' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1.2fr 1fr 1fr 1fr', gap: '10px', alignItems: 'center' }}>
          {/* Search */}
          <div style={{ position: 'relative' }}>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => { setSearchQuery(e.target.value); setPage(1); }}
              placeholder="Search by title, category, ID, fabric..."
              style={{ width: '100%', borderRadius: '10px', padding: '10px 14px', background: 'rgba(0,0,0,0.4)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', fontSize: '13px' }}
            />
          </div>

          {/* Category Dropdown */}
          <select
            value={selectedCategory}
            onChange={(e) => { setSelectedCategory(e.target.value); setPage(1); }}
            style={{ borderRadius: '10px', padding: '10px', background: 'rgba(20,24,35,0.95)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', fontSize: '12px' }}
          >
            {CATEGORY_GROUPS.map((cat) => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>

          {/* Store Dropdown */}
          <select
            value={selectedStore}
            onChange={(e) => { setSelectedStore(e.target.value); setPage(1); }}
            style={{ borderRadius: '10px', padding: '10px', background: 'rgba(20,24,35,0.95)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', fontSize: '12px' }}
          >
            {MARKETPLACES.map((st) => (
              <option key={st} value={st}>{st}</option>
            ))}
          </select>

          {/* Status Dropdown */}
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            style={{ borderRadius: '10px', padding: '10px', background: 'rgba(20,24,35,0.95)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', fontSize: '12px' }}
          >
            <option value="all">Status: All Items</option>
            <option value="published">● Live Storefront</option>
            <option value="draft">⏳ Drafts / Review</option>
            <option value="missing_link">⚠️ Missing Affiliate Link</option>
            <option value="missing_image">⚠️ Missing Photo</option>
          </select>

          {/* Quality Rating Filter */}
          <select
            value={minRatingFilter}
            onChange={(e) => { setMinRatingFilter(Number(e.target.value)); setPage(1); }}
            style={{ borderRadius: '10px', padding: '10px', background: 'rgba(20,24,35,0.95)', border: '1px solid rgba(255,255,255,0.15)', color: '#facc15', fontSize: '12px', fontWeight: '600' }}
          >
            <option value={0}>⭐ All Ratings</option>
            <option value={3.8}>⭐ 3.8+ Stars</option>
            <option value={4.0}>⭐ 4.0+ Stars</option>
            <option value={4.3}>⭐ 4.3+ Stars (Viral)</option>
          </select>
        </div>

        {/* Bulk Action Bar when items are selected */}
        {selectedIds.size > 0 && (
          <div style={{ marginTop: '14px', paddingTop: '14px', borderTop: '1px solid rgba(255,255,255,0.1)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '13px', fontWeight: '700', color: '#ec4899' }}>
                ✓ {selectedIds.size} Products Selected
              </span>
              <button
                type="button"
                onClick={toggleSelectAllFiltered}
                style={{ background: 'none', border: 'none', color: '#38bdf8', fontSize: '12px', cursor: 'pointer', textDecoration: 'underline' }}
              >
                {selectedIds.size === filteredProducts.length ? 'Deselect All' : `Select All ${filteredProducts.length} Filtered`}
              </button>
            </div>

            <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
              <button
                type="button"
                onClick={handleBulkPublish}
                style={{ background: '#22c55e', color: '#fff', border: 'none', padding: '6px 14px', borderRadius: '8px', fontSize: '12px', fontWeight: '700', cursor: 'pointer' }}
              >
                ✓ Publish to Live Store
              </button>
              <button
                type="button"
                onClick={handleBulkMoveToDraft}
                style={{ background: 'rgba(234, 179, 8, 0.2)', border: '1px solid rgba(234, 179, 8, 0.4)', color: '#fde047', padding: '6px 14px', borderRadius: '8px', fontSize: '12px', fontWeight: '600', cursor: 'pointer' }}
              >
                👁️ Move to Drafts
              </button>
              
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <select
                  value={bulkCategoryTarget}
                  onChange={(e) => setBulkCategoryTarget(e.target.value)}
                  style={{ background: 'rgba(20,24,35,0.95)', border: '1px solid rgba(255,255,255,0.2)', color: '#fff', padding: '5px 8px', borderRadius: '6px', fontSize: '11px' }}
                >
                  {CATEGORY_GROUPS.filter(c => c !== 'All Categories').map(c => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={handleBulkChangeCategory}
                  style={{ background: 'rgba(255,255,255,0.1)', color: '#fff', border: '1px solid rgba(255,255,255,0.2)', padding: '6px 10px', borderRadius: '6px', fontSize: '11px', fontWeight: '600', cursor: 'pointer' }}
                >
                  Apply Category
                </button>
              </div>

              <button
                type="button"
                onClick={handleBulkDelete}
                style={{ background: 'rgba(239, 68, 68, 0.25)', border: '1px solid rgba(239, 68, 68, 0.5)', color: '#f87171', padding: '6px 14px', borderRadius: '8px', fontSize: '12px', fontWeight: '700', cursor: 'pointer' }}
              >
                🗑️ Delete Selected
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Catalog Table */}
      <div style={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: '16px', overflow: 'hidden', backdropFilter: 'blur(16px)' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.12)', background: 'rgba(255,255,255,0.02)', color: '#38bdf8', fontSize: '11.5px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                <th style={{ padding: '12px 10px', width: '35px' }}>
                  <input
                    type="checkbox"
                    checked={paginatedProducts.length > 0 && paginatedProducts.every(p => selectedIds.has(p.id))}
                    onChange={toggleSelectPage}
                    style={{ cursor: 'pointer', accentColor: '#ec4899' }}
                    title="Select Page"
                  />
                </th>
                <th style={{ padding: '12px 8px', width: '90px' }}>Thumbnail</th>
                <th style={{ padding: '12px 12px' }}>Product Title &amp; Marketplace</th>
                <th style={{ padding: '12px 10px', width: '120px' }}>Category &amp; Tags</th>
                <th style={{ padding: '12px 10px', width: '90px' }}>Price</th>
                <th style={{ padding: '12px 10px', width: '90px' }}>Net Profit</th>
                <th style={{ padding: '12px 10px', width: '100px' }}>Sizes</th>
                <th style={{ padding: '12px 10px', width: '140px' }}>Affiliate Route</th>
                <th style={{ padding: '12px 10px', width: '90px' }}>Status</th>
                <th style={{ padding: '12px 12px', width: '110px', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {paginatedProducts.length === 0 ? (
                <tr>
                  <td colSpan={10} style={{ textAlign: 'center', padding: '60px 20px', color: 'rgba(255,255,255,0.5)' }}>
                    ✨ No products found matching this filter criteria.
                  </td>
                </tr>
              ) : (
                paginatedProducts.map((p) => {
                  const isSelected = selectedIds.has(p.id);
                  const gallery = p.galleryImages || (p.gallery && p.gallery.length ? p.gallery : [p.image]);
                  const wholesale = p.costPrice || Math.max(149, Number(p.price || 245) - 100);
                  const retail = Number(p.price || 245);
                  const profit = Math.max(0, retail - wholesale);
                  const isLive = p.status === 'published';

                  return (
                    <tr 
                      key={p.id}
                      style={{ borderBottom: '1px solid rgba(255,255,255,0.06)', background: isSelected ? 'rgba(236, 72, 153, 0.08)' : 'transparent', transition: 'background 0.15s' }}
                    >
                      <td style={{ padding: '10px 10px', verticalAlign: 'middle' }}>
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleSelect(p.id)}
                          style={{ cursor: 'pointer', accentColor: '#ec4899' }}
                        />
                      </td>
                      <td style={{ padding: '8px', verticalAlign: 'middle' }}>
                        <div style={{ position: 'relative', width: '52px', height: '62px' }}>
                          <img
                            src={p.image || '/images/meesho-dress-ae6lv9.webp'}
                            alt=""
                            style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.15)' }}
                          />
                          {gallery.length > 1 && (
                            <span style={{ position: 'absolute', bottom: '2px', right: '2px', background: 'rgba(0,0,0,0.85)', color: '#fff', fontSize: '8.5px', padding: '1px 3px', borderRadius: '3px', fontWeight: '700' }}>
                              +{gallery.length - 1}
                            </span>
                          )}
                        </div>
                      </td>
                      <td style={{ padding: '10px 12px', verticalAlign: 'middle' }}>
                        <div style={{ fontWeight: '600', color: '#fff', fontSize: '13px', lineHeight: '1.3' }}>
                          {p.title}
                        </div>
                        <div style={{ display: 'flex', gap: '6px', alignItems: 'center', marginTop: '4px' }}>
                          <span style={{ fontSize: '10px', color: '#38bdf8', background: 'rgba(56,189,248,0.12)', padding: '1px 6px', borderRadius: '4px', fontWeight: '600' }}>
                            {p.store || 'Meesho'}
                          </span>
                          {p.ext_id && (
                            <span style={{ fontSize: '10px', color: 'rgba(255,255,255,0.5)', fontFamily: 'monospace' }}>
                              ID: {p.ext_id}
                            </span>
                          )}
                          {p.rating && (
                            <span style={{ fontSize: '10px', color: '#facc15' }}>
                              ★ {p.rating}
                            </span>
                          )}
                        </div>
                      </td>
                      <td style={{ padding: '10px', verticalAlign: 'middle' }}>
                        <span style={{ background: 'rgba(236, 72, 153, 0.15)', color: '#f472b6', padding: '3px 8px', borderRadius: '6px', fontSize: '11px', fontWeight: '600', display: 'inline-block' }}>
                          {p.category || 'Tops & Tunics'}
                        </span>
                      </td>
                      <td style={{ padding: '10px', verticalAlign: 'middle', fontWeight: '700', color: '#fff' }}>
                        ₹{retail}
                      </td>
                      <td style={{ padding: '10px', verticalAlign: 'middle', fontWeight: '700', color: '#4ade80' }}>
                        +₹{profit}
                      </td>
                      <td style={{ padding: '10px', verticalAlign: 'middle' }}>
                        <span style={{ fontSize: '11px', color: '#9ca3af' }}>
                          {(p.sizes || ["S", "M", "L", "XL"]).slice(0, 3).join(', ')}
                        </span>
                      </td>
                      <td style={{ padding: '10px', verticalAlign: 'middle' }}>
                        {p.affiliateUrl ? (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <button
                              type="button"
                              onClick={() => copyAffiliate(p.id, p.affiliateUrl)}
                              style={{ background: copiedId === p.id ? '#22c55e' : 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', padding: '3px 8px', borderRadius: '4px', fontSize: '10px', cursor: 'pointer' }}
                            >
                              {copiedId === p.id ? '✓ Copied' : '📋 Copy Link'}
                            </button>
                          </div>
                        ) : (
                          <span style={{ fontSize: '10.5px', color: '#f87171' }}>⚠️ Missing Link</span>
                        )}
                      </td>
                      <td style={{ padding: '10px', verticalAlign: 'middle' }}>
                        <span style={{ fontSize: '10.5px', fontWeight: '700', padding: '3px 8px', borderRadius: '999px', background: isLive ? 'rgba(34, 197, 94, 0.15)' : 'rgba(234, 179, 8, 0.15)', color: isLive ? '#4ade80' : '#fde047', border: isLive ? '1px solid rgba(34, 197, 94, 0.3)' : '1px solid rgba(234, 179, 8, 0.3)' }}>
                          {isLive ? '● Live' : '⏳ Draft'}
                        </span>
                      </td>
                      <td style={{ padding: '10px 12px', textAlign: 'right', verticalAlign: 'middle' }}>
                        <div style={{ display: 'flex', gap: '4px', justifyContent: 'flex-end' }}>
                          <button
                            type="button"
                            onClick={() => onOpenEditProduct?.(p)}
                            title="Edit Pick"
                            style={{ background: 'rgba(56, 189, 248, 0.15)', border: '1px solid rgba(56, 189, 248, 0.3)', color: '#38bdf8', padding: '5px 7px', borderRadius: '6px', fontSize: '11px', cursor: 'pointer' }}
                          >
                            ✏️
                          </button>
                          <button
                            type="button"
                            onClick={() => onApproveProduct?.({ ...p, status: isLive ? 'draft' : 'published' })}
                            title={isLive ? 'Hide (Move to Drafts)' : 'Publish to Live Store'}
                            style={{ background: isLive ? 'rgba(234, 179, 8, 0.15)' : 'rgba(34, 197, 94, 0.15)', border: '1px solid rgba(255,255,255,0.2)', color: isLive ? '#fde047' : '#4ade80', padding: '5px 7px', borderRadius: '6px', fontSize: '11px', cursor: 'pointer' }}
                          >
                            {isLive ? '👁️' : '✓'}
                          </button>
                          <button
                            type="button"
                            onClick={() => {
                              if (window.confirm(`Delete "${p.title.slice(0, 30)}..." permanently?`)) {
                                onDeleteProduct?.(p.id);
                              }
                            }}
                            title="Delete Permanently"
                            style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#f87171', padding: '5px 7px', borderRadius: '6px', fontSize: '11px', cursor: 'pointer' }}
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

        {/* Pagination Bar */}
        {filteredProducts.length > pageSize && (
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 20px', borderTop: '1px solid rgba(255,255,255,0.08)', background: 'rgba(255,255,255,0.02)' }}>
            <span style={{ fontSize: '12px', color: '#9ca3af' }}>
              Showing {((page - 1) * pageSize) + 1} to {Math.min(filteredProducts.length, page * pageSize)} of {filteredProducts.length} items
            </span>
            <div style={{ display: 'flex', gap: '6px' }}>
              <button
                type="button"
                disabled={page === 1}
                onClick={() => setPage(p => Math.max(1, p - 1))}
                style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', padding: '5px 12px', borderRadius: '6px', fontSize: '12px', cursor: page === 1 ? 'not-allowed' : 'pointer', opacity: page === 1 ? 0.5 : 1 }}
              >
                Previous
              </button>
              <span style={{ padding: '5px 10px', fontSize: '12px', color: '#fff', fontWeight: '700' }}>
                Page {page} of {totalPages}
              </span>
              <button
                type="button"
                disabled={page === totalPages}
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', padding: '5px 12px', borderRadius: '6px', fontSize: '12px', cursor: page === totalPages ? 'not-allowed' : 'pointer', opacity: page === totalPages ? 0.5 : 1 }}
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
