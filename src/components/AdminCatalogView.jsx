import React, { useState, useMemo, useRef } from 'react';
import Icon from './Icon.jsx';
import { detectStore } from '../data.js';
import './AdminCatalogView.css';

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

function getStatusBadgeClass(status) {
  switch (status) {
    case 'live':
    case 'published':
      return 'status-badge-live';
    case 'draft':
    case 'pending_review':
      return 'status-badge-draft';
    case 'archived':
      return 'status-badge-archived';
    default:
      return '';
  }
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
    <div className="admin-catalog-view">
       {/* Top Header */}
       <div className="admin-catalog-header">
         <div>
           <h1 className="admin-catalog-title">
             <span>📦 Master Catalog Control</span>
             <span className="admin-catalog-tag">
               {products.length} Real Database Products
             </span>
           </h1>
         </div>

         <div className="admin-filters">
           <input 
             type="file" 
             ref={fileInputRef} 
             onChange={handleCSVUpload} 
             accept=".csv" 
             className="file-input-hidden"
           />
           <button
             type="button"
             onClick={() => fileInputRef.current?.click()}
             className="button button-light filter-select"
             title="Import Meesho extension CSV or affiliate link batch"
           >
             <Icon name="download" size={15} /> Batch Import CSV
           </button>
           <button
             type="button"
             onClick={onOpenAddProduct}
             className="button button-dark filter-select-sm"
           >
             <Icon name="plus" size={15} /> Add Product
           </button>
           <button
             type="button"
             onClick={exportCSV}
             className="button button-light filter-select"
           >
             Export CSV
           </button>
         </div>
      </div>

       {/* Import Notice Alert */}
       {importNotice && (
         <div className="import-notice">
           {importNotice}
         </div>
       )}

      {/* Real Summary Status Pills */}
       {/* Real Summary Status Pills */}
       <div className="filter-chips">
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
           className={`filter-chip${statusFilter === 'ai_flagged' ? ' is-active' : ''} ai-flagged-chip`}
         >
           🚨 AI Flagged ({aiFlaggedCount})
         </button>
       </div>

       {/* Filter Control Bar */}
       <div className="filter-control-bar">
         <div className="filter-grid">
           {/* Search */}
           <div>
             <input
               type="text"
               value={searchQuery}
               onChange={e => setSearchQuery(e.target.value)}
               placeholder="Search products..."
               className="search-input"
             />
           </div>

           {/* Category Dropdown */}
           <select
             value={selectedCategory}
             onChange={(e) => { setSelectedCategory(e.target.value); setPage(1); }}
             className="filter-select"
           >
             {CATEGORY_GROUPS.map((cat) => (
               <option key={cat} value={cat}>{cat}</option>
             ))}
           </select>

           {/* Store Dropdown */}
           <select
             value={selectedStore}
             onChange={(e) => { setSelectedStore(e.target.value); setPage(1); }}
             className="filter-select"
           >
             {MARKETPLACES.map((st) => (
               <option key={st} value={st}>{st}</option>
             ))}
           </select>

           {/* Min Rating */}
           <select
             value={minRatingFilter}
             onChange={(e) => { setMinRatingFilter(Number(e.target.value)); setPage(1); }}
             className="filter-select"
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
         <div className="bulk-action-toolbar">
           <div className="bulk-action-left">
             <span className="bulk-action-count">
               ✓ {selectedIds.size} Selected
             </span>
             <button
               type="button"
               onClick={toggleSelectAllFiltered}
               className="bulk-action-link"
             >
               {selectedIds.size === filteredProducts.length ? 'Deselect all' : `Select all ${filteredProducts.length} filtered`}
             </button>
           </div>

           <div className="bulk-action-right">
             {/* Category target */}
             <select
               value={bulkCategoryTarget}
               onChange={(e) => setBulkCategoryTarget(e.target.value)}
               className="bulk-category-select"
             >
               {CATEGORY_GROUPS.filter(c => c !== 'All Categories' && !c.includes('📌')).map(c => (
                 <option key={c} value={c}>Move to: {c}</option>
               ))}
             </select>
             <button
               type="button"
               onClick={handleBulkChangeCategory}
               className="button button-light bulk-action-button"
             >
               Apply Category
             </button>

             {statusFilter === 'archived' ? (
               <button
                 type="button"
                 onClick={handleBulkRestore}
                 className="button button-dark bulk-action-button"
               >
                 Restore to Live
               </button>
             ) : (
               <button
                 type="button"
                 onClick={handleBulkArchive}
                 className="button button-light bulk-action-button"
               >
                 📁 Move to Archive
               </button>
             )}

             <button
               type="button"
               onClick={handleBulkPermanentDelete}
               className="action-button"
             >
               🗑️ Delete Permanently
             </button>
           </div>
         </div>
       )}

       {/* Main Table */}
       <div className="main-table-container">
         <table className="product-table">
           <thead>
             <tr className="product-table-header">
               <th className="table-th">
                 <input
                   type="checkbox"
                   checked={paginatedProducts.length > 0 && paginatedProducts.every(p => selectedIds.has(p.id))}
                   onChange={toggleSelectPage}
                   aria-label="Select page"
                 />
               </th>
               <th className="table-th table-th-photos">Photos</th>
               <th className="table-th table-th-title">Product Title &amp; Details</th>
               <th className="table-th table-th-category" width="140px">Category</th>
               <th className="table-th table-th-price" width="90px">Price</th>
               <th className="table-th table-th-affiliate" width="120px">Affiliate Link</th>
               <th className="table-th table-th-status" width="100px">Status</th>
               <th className="table-th table-th-actions" width="90px" textAlign="right">Actions</th>
             </tr>
           </thead>
           <tbody>
             {paginatedProducts.length === 0 ? (
               <tr>
                 <td colSpan={8} className="empty-state">
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
                     className={`${isSelected ? 'selected-row' : ''} ${p.aiFlagged ? 'ai-flagged-row' : ''}`}
                   >
                     <td className="table-td">
                       <input
                         type="checkbox"
                         checked={isSelected}
                         onChange={() => toggleSelect(p.id)}
                         aria-label={`Select ${p.title}`}
                       />
                     </td>
                     <td className="table-td table-td-photos">
                       <div className="product-images-container${p.aiFlagged ? ' flagged' : ''}">
                         <img
                           src={currentImg}
                           alt={p.title}
                           className="product-image"
                           loading="lazy"
                         />
                         {p.aiFlagged && (
                           <span className="ai-flag-badge"
                                 title={p.aiFlagReason || 'AI Image Flagged'}
                           >
                             AI
                           </span>
                         )}
                         {productImages.length > 1 && (
                           <div className="image-overlay">
                             <button
                               type="button"
                               onClick={(e) => {
                                 e.stopPropagation();
                                 setImageIndexMap(prev => ({
                                   ...prev,
                                   [p.id]: (activeImgIdx - 1 + productImages.length) % productImages.length
                                 }));
                               }}
                               className="image-nav-button"
                               title="Previous Photo Variation"
                             >
                               ‹
                             </button>
                             <span className="image-counter">{activeImgIdx + 1}/{productImages.length}</span>
                             <button
                               type="button"
                               onClick={(e) => {
                                 e.stopPropagation();
                                 setImageIndexMap(prev => ({
                                   ...prev,
                                   [p.id]: (activeImgIdx + 1) % productImages.length
                                 }));
                               }}
                               className="image-nav-button"
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
                         className="manage-images-button"
                         title="Add or manage images / color variations"
                       >
                         <span>➕ {productImages.length > 1 ? `${productImages.length} Imgs` : 'Add'}</span>
                       </button>
                     </td>
                     <td className="table-td table-td-title">
                       <strong className="product-title">
                         {p.title}
                       </strong>
                       <div className="product-details">
                         <span>Store: {p.store || 'Meesho'}</span>
                         <span>·</span>
                         <span>ID: {p.ext_id || p.id}</span>
                         {p.rating && <span>· ⭐ {p.rating}</span>}
                         {productImages.length > 1 && (
                           <span className="product-variations">
                             · 📸 {productImages.length} Variations
                           </span>
                         )}
                       </div>
                       {p.aiFlagged && (
                         <div className="ai-flag-warning">
                           <span className="ai-flag-icon">🚨</span>
                           <span className="ai-flag-text">AI / Low-Res Image Detected:</span>
                           <span className="ai-flag-reason">{p.aiFlagReason || 'Synthetic AI Watermark'}</span>
                           <button
                             type="button"
                             onClick={() => setManageImagesProduct(p)}
                             className="ai-flag-button"
                           >
                             Manage Images
                           </button>
                         </div>
                       )}
                     </td>
                     <td className="table-td table-td-category">
                       <span className="category-tag">
                         {p.category || 'Fashion'}
                       </span>
                     </td>
                     <td className="table-td table-td-price">
                       <strong className="price-value">
                         {money(p.price)}
                       </strong>
                     </td>
                     <td className="table-td table-td-affiliate">
                       {hasAffiliate ? (
                         <button
                           type="button"
                           onClick={() => copyAffiliate(p.id, p.affiliateUrl)}
                           className="affiliate-button"
                           title="Click to copy affiliate link"
                         >
                           {copiedId === p.id ? '✓ Copied' : '🔗 Link Ready'}
                         </button>
                       ) : (
                         <span className="missing-link-badge">
                           ⚠️ Missing Link
                         </span>
                       )}
                     </td>
                     <td className="table-td table-td-status">
                       <span className={`status-badge ${getStatusBadgeClass(p.status)}`}>
                         {p.status === 'archived' ? 'Archived' : (p.status === 'draft' || p.status === 'pending_review') ? 'Draft' : 'Live'}
                       </span>
                     </td>
                     <td className="table-td table-td-actions" textAlign="right">
                       <div className="action-buttons">
                         <button
                           type="button"
                           onClick={() => onOpenEditProduct?.(p)}
                           className="action-button-view"
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
                           className="action-button-delete"
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
         <div className="table-pagination">
           <span className="pagination-info">
             Showing {filteredProducts.length > 0 ? (page - 1) * pageSize + 1 : 0} - {Math.min(page * pageSize, filteredProducts.length)} of {filteredProducts.length} filtered items
           </span>

           <div className="pagination-controls">
             <button
               type="button"
               disabled={page <= 1}
               onClick={() => setPage(p => Math.max(1, p - 1))}
               className="button button-light pagination-button"
             >
               Previous
             </button>
             <span className="pagination-page">
               Page {page} of {totalPages}
             </span>
             <button
               type="button"
               disabled={page >= totalPages}
               onClick={() => setPage(p => Math.min(totalPages, p + 1))}
               className="button button-light pagination-button"
             >
               Next
             </button>
           </div>
         </div>
      </div>

       {/* Confirmation Modal */}
       {confirmModal && (
         <div className="modal-backdrop" onClick={() => setConfirmModal(null)}>
           <div className="modal-card" onClick={e => e.stopPropagation()}>
             <h3 className="modal-title">{confirmModal.title}</h3>
             <p className="modal-message">{confirmModal.message}</p>
             <div className="modal-actions">
               <button
                 type="button"
                 className="button button-light"
                 onClick={() => setConfirmModal(null)}
               >
                 Cancel
               </button>
               <button
                 type="button"
                 className="modal-button"
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
     <div className="modal-backdrop" onClick={onClose}>
       <div className="modal-card manage-images-modal-card" onClick={e => e.stopPropagation()}>
         <div className="modal-header">
           <div>
             <h3 className="modal-title">
               📸 Manage Product Images &amp; Variations
             </h3>
             <p className="modal-subtitle">
               {product.title}
             </p>
           </div>
           <button type="button" className="modal-close-button" onClick={onClose}>✕</button>
        </div>

        {/* Existing Images Grid */}
        <div className="image-grid-section">
          <label className="image-grid-label">
            Current Photos ({imageList.length}) · Leftmost is Primary
          </label>
          <div className="image-grid">
            {imageList.map((imgUrl, idx) => (
              <div key={idx} className={`image-item ${idx === 0 ? 'primary' : ''}`}>
                <img src={imgUrl} alt={`Photo ${idx + 1}`} className="image-preview" />
                {idx === 0 && (
                  <span className="cover-badge">
                    COVER
                  </span>
                )}
                <button
                  type="button"
                  onClick={() => handleRemoveImage(idx)}
                  title="Remove this photo"
                  className="remove-button"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Add New URLs Form */}
        <div className="add-urls-form">
          <label className="form-label">
            ➕ Add More Image URLs (Meesho / Myntra / Amazon variation links)
          </label>
          <textarea
            rows={3}
            value={urlsInput}
            onChange={e => setUrlsInput(e.target.value)}
            placeholder="Paste image URLs here (one per line or comma-separated)&#10;e.g. https://images.meesho.com/images/products/..."
            className="image-urls-textarea"
          />
          <div className="form-actions">
            <button
              type="button"
              onClick={handleAddUrls}
              className="button button-light"
            >
              Add to Photos
            </button>
          </div>
        </div>

        {/* Modal Actions */}
        <div className="modal-actions">
          <button type="button" className="button button-light" onClick={onClose} disabled={saving}>
            Cancel
          </button>
          <button
            type="button"
            className="button button-dark save-button"
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? 'Saving...' : '💾 Save Photos & Clear AI Flag'}
          </button>
        </div>
      </div>
    </div>
  );
}
