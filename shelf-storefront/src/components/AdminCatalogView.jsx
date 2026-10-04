import React, { useEffect, useMemo, useRef, useState } from 'react';
import Icon from './Icon.jsx';
import './AdminManagers.css';

const CATEGORY_GROUPS = [
  'Tops & Tunics', 'Kurtis', 'Women Dresses', 'Bottomwear',
  'Layers & Outerwear', 'Accessories', 'Innerwear', 'Ethnic Wear',
  'Winter', 'Beauty', 'Home'
];
const BASE_MARKETPLACES = ['Meesho', 'Amazon', 'Flipkart', 'Myntra'];
const PAGE_SIZES = [15, 30, 60];

function normalizeText(value) {
  return String(value ?? '').trim().toLowerCase().replace(/\s+/g, ' ');
}

function canonicalCategory(value) {
  const category = normalizeText(value);
  if (category === 'dresses' || category === 'women dresses' || category === 'women\'s dresses') return 'women dresses';
  if (category === 'layers' || category === 'outerwear' || category === 'layers and outerwear') return 'layers & outerwear';
  return category;
}

function displayCategory(value) {
  return normalizeText(value) === 'women dresses' ? 'Dresses' : (value || 'Uncategorized');
}

function keyOf(product) {
  // Selection and database mutations must use the persisted record id, never a partial title/ext_id match.
  return product?.id === null || product?.id === undefined ? '' : String(product.id).trim();
}

function productImage(product) {
  const candidate = product?.image || product?.imageUrl || product?.thumbnail || (Array.isArray(product?.images) ? product.images[0] : '');
  const value = String(candidate || '').trim();
  return !value || /placeholder|no[-_ ]?image/i.test(value) ? '' : value;
}

function statusOf(product) {
  const value = normalizeText(product?.status || product?.publishStatus || '');
  if (['published', 'live', 'active'].includes(value)) return 'published';
  if (['draft', 'pending_review', 'pending review', 'review'].includes(value)) return 'draft';
  if (['archived', 'archive', 'trash'].includes(value)) return 'archived';
  return 'unspecified';
}

function isPinterestDrop(product) {
  const tags = Array.isArray(product?.tags) ? product.tags.map(normalizeText) : [];
  const collection = normalizeText(product?.collectionId || product?.collection_id || '');
  return product?.isPinterestCombo === true ||
    tags.includes('pinterest-viral') || tags.includes('pinterest viral') ||
    collection === 'pinterest-viral' || collection === 'pinterest-viral-drops';
}

function getRating(product) {
  const value = product?.rating;
  if (value === null || value === undefined || String(value).trim() === '') return null;
  const number = Number(value);
  return Number.isFinite(number) && number > 0 ? number : null;
}

function numericPrice(value) {
  if (value === null || value === undefined || String(value).trim() === '') return null;
  const number = typeof value === 'number' ? value : Number(String(value).replace(/[^\d.]/g, ''));
  return Number.isFinite(number) ? number : null;
}

function formatMoney(value) {
  const number = numericPrice(value);
  if (number === null) return '—';
  return `₹${number.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
}

function csvEscape(value) {
  const text = value === null || value === undefined ? '' : String(value);
  return `"${text.replace(/"/g, '""')}"`;
}

// RFC-4180-style parser: supports quoted commas, escaped quotes and newlines.
function parseCsv(input) {
  const text = String(input || '').replace(/^\uFEFF/, '');
  const rows = [];
  let row = [];
  let field = '';
  let quoted = false;

  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    if (quoted) {
      if (char === '"' && text[index + 1] === '"') {
        field += '"';
        index += 1;
      } else if (char === '"') {
        quoted = false;
      } else {
        field += char;
      }
    } else if (char === '"' && field.length === 0) {
      quoted = true;
    } else if (char === ',') {
      row.push(field);
      field = '';
    } else if (char === '\n' || char === '\r') {
      if (char === '\r' && text[index + 1] === '\n') index += 1;
      row.push(field);
      if (row.some((cell) => String(cell).trim() !== '')) rows.push(row);
      row = [];
      field = '';
    } else {
      field += char;
    }
  }
  if (quoted) throw new Error('The CSV has an unclosed quoted field. Please export it again as a valid CSV.');
  row.push(field);
  if (row.some((cell) => String(cell).trim() !== '')) rows.push(row);
  return rows;
}

function normalizeHeader(value) {
  return normalizeText(value).replace(/[\s-]+/g, '_');
}

function cellFor(row, indexByHeader, aliases) {
  for (const alias of aliases) {
    const index = indexByHeader.get(alias);
    if (index !== undefined) return String(row[index] || '').trim();
  }
  return '';
}

function extractExtIdFromUrl(rawUrl) {
  const value = String(rawUrl || '').trim();
  if (!value) return '';
  try {
    const url = new URL(value, typeof window !== 'undefined' ? window.location.origin : 'https://example.invalid');
    const explicit = url.searchParams.get('ext_id');
    if (explicit) return explicit.trim();
    const path = url.pathname.split('/').filter(Boolean);
    const productMarker = path.lastIndexOf('p');
    if (productMarker >= 0 && path[productMarker + 1]) return decodeURIComponent(path[productMarker + 1]).trim();
  } catch {
    return '';
  }
  return '';
}

function productExtId(product) {
  const explicit = product?.ext_id || product?.extId || product?.externalId;
  if (explicit) return normalizeText(explicit);
  return normalizeText(extractExtIdFromUrl(product?.productUrl || product?.product_url || product?.originalUrl));
}

function affiliateUrlFrom(product) {
  return String(product?.affiliateUrl || product?.affiliate_url || '').trim();
}

function isSafeAffiliateUrl(value) {
  const url = String(value || '').trim();
  if (!url) return false;
  if (url.startsWith('/') && !url.startsWith('//')) return true;
  try {
    const parsed = new URL(url);
    return parsed.protocol === 'https:' || parsed.protocol === 'http:';
  } catch {
    return false;
  }
}

export default function AdminCatalogView({
  products = [],
  onApproveProduct,
  onDeleteProduct,
  onUpdateProduct,
  onBulkUpdateProducts,
  onBulkDeleteProducts,
  onOpenAddProduct,
  onOpenEditProduct
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All Categories');
  const [selectedStore, setSelectedStore] = useState('All Stores');
  const [statusFilter, setStatusFilter] = useState('all');
  const [ratingFilter, setRatingFilter] = useState('all');
  const [sortBy, setSortBy] = useState('recent');
  const [selectedIds, setSelectedIds] = useState(() => new Set());
  const [pageSize, setPageSize] = useState(15);
  const [page, setPage] = useState(1);
  const [copiedId, setCopiedId] = useState('');
  const [bulkCategoryTarget, setBulkCategoryTarget] = useState('Tops & Tunics');
  const [confirmModal, setConfirmModal] = useState(null);
  const [busyAction, setBusyAction] = useState(false);
  const [notice, setNotice] = useState(null);
  const [importPreview, setImportPreview] = useState(null);
  const [importBusy, setImportBusy] = useState(false);
  const fileInputRef = useRef(null);

  const safeProducts = Array.isArray(products) ? products : [];
  const liveCount = safeProducts.filter((product) => statusOf(product) === 'published').length;
  const draftCount = safeProducts.filter((product) => statusOf(product) === 'draft').length;
  const archivedCount = safeProducts.filter((product) => statusOf(product) === 'archived').length;
  const untrackedCount = safeProducts.filter((product) => statusOf(product) === 'unspecified').length;
  const missingLinkCount = safeProducts.filter((product) => !affiliateUrlFrom(product)).length;
  const missingImageCount = safeProducts.filter((product) => !productImage(product)).length;

  const marketplaceOptions = useMemo(() => {
    const values = safeProducts.map((product) => String(product?.store || '').trim()).filter(Boolean);
    return ['All Stores', ...new Set([...BASE_MARKETPLACES, ...values].sort((a, b) => a.localeCompare(b)))];
  }, [safeProducts]);

  const filteredProducts = useMemo(() => {
    const query = normalizeText(searchQuery);
    const result = safeProducts.filter((product) => {
      if (query) {
        const searchable = [product?.title, product?.category, product?.id, product?.ext_id, product?.store, product?.productUrl]
          .map(normalizeText).join(' ');
        if (!searchable.includes(query)) return false;
      }

      if (selectedCategory === 'Pinterest Viral Drops') {
        if (!isPinterestDrop(product)) return false;
      } else if (selectedCategory !== 'All Categories') {
        if (canonicalCategory(product?.category) !== canonicalCategory(selectedCategory)) return false;
      }

      if (selectedStore !== 'All Stores' && normalizeText(product?.store) !== normalizeText(selectedStore)) return false;

      const status = statusOf(product);
      if (statusFilter === 'published' && status !== 'published') return false;
      if (statusFilter === 'draft' && status !== 'draft') return false;
      if (statusFilter === 'archived' && status !== 'archived') return false;
      if (statusFilter === 'untracked' && status !== 'unspecified') return false;
      if (statusFilter === 'missing_link' && affiliateUrlFrom(product)) return false;
      if (statusFilter === 'missing_image' && productImage(product)) return false;

      const rating = getRating(product);
      if (ratingFilter === 'unrated' && rating !== null) return false;
      if (ratingFilter !== 'all' && ratingFilter !== 'unrated' && (rating === null || rating < Number(ratingFilter))) return false;
      return true;
    });

    const compare = (a, b) => {
      if (sortBy === 'price-low') return (numericPrice(a?.price) ?? Number.POSITIVE_INFINITY) - (numericPrice(b?.price) ?? Number.POSITIVE_INFINITY);
      if (sortBy === 'price-high') return (numericPrice(b?.price) ?? -1) - (numericPrice(a?.price) ?? -1);
      if (sortBy === 'rating') return (getRating(b) || -1) - (getRating(a) || -1);
      if (sortBy === 'title') return String(a?.title || '').localeCompare(String(b?.title || ''));
      return 0;
    };
    return sortBy === 'recent' ? result : [...result].sort(compare);
  }, [safeProducts, searchQuery, selectedCategory, selectedStore, statusFilter, ratingFilter, sortBy]);

  const totalPages = Math.max(1, Math.ceil(filteredProducts.length / pageSize));
  const paginatedProducts = useMemo(() => {
    const start = (page - 1) * pageSize;
    return filteredProducts.slice(start, start + pageSize);
  }, [filteredProducts, page, pageSize]);

  useEffect(() => {
    setPage((current) => Math.min(current, totalPages));
  }, [totalPages]);

  useEffect(() => {
    const validKeys = new Set(safeProducts.map(keyOf).filter(Boolean));
    setSelectedIds((previous) => new Set([...previous].filter((key) => validKeys.has(key))));
  }, [safeProducts]);

  const setFilter = (setter, value) => {
    setter(value);
    setPage(1);
    setNotice(null);
  };

  const toggleSelect = (id) => {
    const key = String(id ?? '').trim();
    if (!key) return;
    setSelectedIds((previous) => {
      const next = new Set(previous);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const toggleSelectPage = () => {
    const pageKeys = paginatedProducts.map(keyOf).filter(Boolean);
    const allSelected = pageKeys.length > 0 && pageKeys.every((key) => selectedIds.has(key));
    setSelectedIds((previous) => {
      const next = new Set(previous);
      pageKeys.forEach((key) => allSelected ? next.delete(key) : next.add(key));
      return next;
    });
  };

  const toggleSelectAllFiltered = () => {
    const filteredKeys = filteredProducts.map(keyOf).filter(Boolean);
    const allSelected = filteredKeys.length > 0 && filteredKeys.every((key) => selectedIds.has(key));
    setSelectedIds((previous) => {
      const next = new Set(previous);
      filteredKeys.forEach((key) => allSelected ? next.delete(key) : next.add(key));
      return next;
    });
  };

  const selectedProducts = useMemo(() => safeProducts.filter((product) => keyOf(product) && selectedIds.has(keyOf(product))), [safeProducts, selectedIds]);
  const selectablePageKeys = paginatedProducts.map(keyOf).filter(Boolean);
  const selectableFilteredKeys = filteredProducts.map(keyOf).filter(Boolean);
  const allPageSelected = selectablePageKeys.length > 0 && selectablePageKeys.every((key) => selectedIds.has(key));
  const allFilteredSelected = selectableFilteredKeys.length > 0 && selectableFilteredKeys.every((key) => selectedIds.has(key));

  const updateProducts = async (targets, patchOrFactory) => {
    if (targets.length === 0) return { succeeded: [], failed: [] };
    if (targets.some((product) => product?.id === null || product?.id === undefined || String(product.id).trim() === '')) {
      throw new Error('One or more selected products have no database id. They cannot be safely changed until the catalog returns an id.');
    }
    const updates = targets.map((product) => ({
      id: product.id,
      patch: typeof patchOrFactory === 'function' ? patchOrFactory(product) : patchOrFactory
    }));

    if (typeof onBulkUpdateProducts === 'function') {
      const result = await onBulkUpdateProducts(updates);
      if (result === false || result?.ok === false || result?.success === false) {
        throw new Error(result?.message || 'The server rejected the bulk update.');
      }
      const failedKeys = new Set((result?.failedIds || []).map(String));
      return {
        succeeded: targets.filter((product) => !failedKeys.has(String(product.id))),
        failed: targets.filter((product) => failedKeys.has(String(product.id)))
      };
    }

    if (typeof onUpdateProduct !== 'function') throw new Error('Product update is not connected. Add the onUpdateProduct callback or a bulk update endpoint.');
    const results = await Promise.allSettled(updates.map(({ id, patch }) => onUpdateProduct(id, patch)));
    const succeeded = [];
    const failed = [];
    results.forEach((result, index) => (result.status === 'fulfilled' ? succeeded : failed).push(targets[index]));
    return { succeeded, failed };
  };

  const deleteProducts = async (targets) => {
    if (targets.length === 0) return { succeeded: [], failed: [] };
    if (targets.some((product) => product?.id === null || product?.id === undefined || String(product.id).trim() === '')) {
      throw new Error('One or more selected products have no database id. They cannot be safely deleted.');
    }
    if (typeof onBulkDeleteProducts === 'function') {
      const result = await onBulkDeleteProducts(targets.map((product) => product.id));
      if (result === false || result?.ok === false || result?.success === false) {
        throw new Error(result?.message || 'The server rejected the delete request.');
      }
      const failedKeys = new Set((result?.failedIds || []).map(String));
      return {
        succeeded: targets.filter((product) => !failedKeys.has(String(product.id))),
        failed: targets.filter((product) => failedKeys.has(String(product.id)))
      };
    }
    if (typeof onDeleteProduct !== 'function') throw new Error('Permanent delete is not connected. Add the onDeleteProduct callback or a bulk delete endpoint.');
    const results = await Promise.allSettled(targets.map((product) => onDeleteProduct(product.id)));
    const succeeded = [];
    const failed = [];
    results.forEach((result, index) => (result.status === 'fulfilled' ? succeeded : failed).push(targets[index]));
    return { succeeded, failed };
  };

  const finishBatch = (label, result) => {
    setSelectedIds((previous) => {
      const next = new Set(previous);
      result.succeeded.forEach((product) => next.delete(keyOf(product)));
      return next;
    });
    if (result.failed.length) {
      setNotice({ type: 'warning', text: `${label}: ${result.succeeded.length} succeeded, ${result.failed.length} failed. Failed items remain selected so you can retry.` });
    } else {
      setNotice({ type: 'success', text: `${label}: ${result.succeeded.length} product${result.succeeded.length === 1 ? '' : 's'} updated.` });
    }
  };

  const handleBulkArchive = () => {
    const targets = selectedProducts.filter((product) => statusOf(product) !== 'archived');
    if (!targets.length) {
      setNotice({ type: 'warning', text: 'No non-archived products are selected.' });
      return;
    }
    setConfirmModal({
      title: 'Move selected products to archive?',
      message: `This changes the selected products to archived through the configured update callback. ${targets.length} item(s) will be affected.`, 
      confirmLabel: 'Move to archive',
      confirmTone: 'danger',
      run: async () => {
        const result = await updateProducts(targets, { status: 'archived' });
        finishBatch('Archive', result);
      }
    });
  };

  const handleBulkRestore = () => {
    const targets = selectedProducts.filter((product) => statusOf(product) === 'archived');
    if (!targets.length) {
      setNotice({ type: 'warning', text: 'No archived products are selected.' });
      return;
    }
    setConfirmModal({
      title: 'Restore selected products?',
      message: `${targets.length} archived product(s) will be set to published.`,
      confirmLabel: 'Restore to live',
      confirmTone: 'primary',
      run: async () => {
        const result = await updateProducts(targets, (product) => ({ status: product.previousStatus || 'published' }));
        finishBatch('Restore', result);
      }
    });
  };

  const handleBulkPermanentDelete = () => {
    if (!selectedProducts.length) return;
    setConfirmModal({
      title: 'Permanently delete selected products?',
      message: `This action cannot be undone. The configured delete callback will be called for ${selectedProducts.length} product(s).`,
      confirmLabel: 'Delete permanently',
      confirmTone: 'danger',
      run: async () => {
        const result = await deleteProducts(selectedProducts);
        finishBatch('Delete', result);
      }
    });
  };

  const handleBulkChangeCategory = async () => {
    if (!selectedProducts.length) return;
    setBusyAction(true);
    setNotice(null);
    try {
      const result = await updateProducts(selectedProducts, { category: bulkCategoryTarget });
      finishBatch('Category change', result);
    } catch (error) {
      setNotice({ type: 'error', text: error?.message || 'Could not update the selected categories.' });
    } finally {
      setBusyAction(false);
    }
  };

  const runConfirmation = async () => {
    if (!confirmModal?.run) return;
    setBusyAction(true);
    setNotice(null);
    try {
      await confirmModal.run();
      setConfirmModal(null);
    } catch (error) {
      setNotice({ type: 'error', text: error?.message || 'The action failed. No success was reported.' });
    } finally {
      setBusyAction(false);
    }
  };

  const approveProduct = async (product) => {
    setBusyAction(true);
    setNotice(null);
    try {
      if (product?.id === null || product?.id === undefined || String(product.id).trim() === '') {
        throw new Error('This product has no database id, so it cannot be safely approved.');
      }
      if (typeof onApproveProduct === 'function') {
        const result = await onApproveProduct(product.id);
        if (result === false || result?.ok === false || result?.success === false) throw new Error(result?.message || 'Approval was not confirmed.');
      } else {
        const result = await updateProducts([product], { status: 'published' });
        if (result.failed.length) throw new Error('Product could not be published.');
      }
      setNotice({ type: 'success', text: `“${product.title || 'Product'}” approved.` });
    } catch (error) {
      setNotice({ type: 'error', text: error?.message || 'Could not approve this product.' });
    } finally {
      setBusyAction(false);
    }
  };

  const copyAffiliate = async (product) => {
    const url = affiliateUrlFrom(product);
    if (!url) return;
    try {
      await navigator.clipboard.writeText(url);
      const id = keyOf(product);
      setCopiedId(id);
      window.setTimeout(() => setCopiedId(''), 1800);
    } catch {
      setNotice({ type: 'error', text: 'Clipboard access was blocked. Copy the affiliate URL from the edit form instead.' });
    }
  };

  const exportCSV = () => {
    const items = selectedProducts.length ? selectedProducts : filteredProducts;
    if (!items.length) {
      setNotice({ type: 'warning', text: 'There are no products to export for the current selection.' });
      return;
    }
    const headers = ['ID', 'Ext ID', 'Title', 'Category', 'Store', 'Price', 'Rating', 'Image URL', 'Product URL', 'Affiliate URL', 'Status'];
    const rows = items.map((product) => [
      product.id ?? '', product.ext_id ?? '', product.title ?? '', product.category ?? '', product.store ?? '',
      product.price ?? '', product.rating ?? '', productImage(product), product.productUrl ?? '',
      affiliateUrlFrom(product), product.status ?? ''
    ]);
    const csv = [headers, ...rows].map((row) => row.map(csvEscape).join(',')).join('\r\n');
    const blob = new Blob(['\uFEFF', csv], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `catalog_export_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  };

  const handleCSVUpload = (event) => {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;
    setNotice(null);
    const reader = new FileReader();
    reader.onerror = () => setNotice({ type: 'error', text: 'Could not read the CSV file.' });
    reader.onload = () => {
      try {
        const rows = parseCsv(reader.result);
        if (rows.length < 2) throw new Error('CSV is empty or has no data rows.');
        const headers = rows[0].map(normalizeHeader);
        const headerIndex = new Map(headers.map((header, index) => [header, index]));
        const extHeaderAliases = ['ext_id', 'external_id', 'meesho_ext_id', 'product_slug'];
        const urlHeaderAliases = ['product_url', 'original_url', 'source_url', 'meesho_url'];
        const affiliateAliases = ['affiliate_url', 'affiliate_link', 'creator_link', 'creator_affiliate_url', 'link'];
        const hasIdentifierColumn = extHeaderAliases.some((header) => headerIndex.has(header)) || urlHeaderAliases.some((header) => headerIndex.has(header));
        const hasAffiliateColumn = affiliateAliases.some((header) => headerIndex.has(header));
        if (!hasIdentifierColumn || !hasAffiliateColumn) {
          throw new Error('Expected an exact ext_id/product URL column and an affiliate_url/link column. A p_id-only CSV is not safe to match.');
        }

        const productsByExtId = new Map();
        safeProducts.forEach((product) => {
          const extId = productExtId(product);
          if (!extId) return;
          const existing = productsByExtId.get(extId) || [];
          existing.push(product);
          productsByExtId.set(extId, existing);
        });
        const csvExtIdCounts = new Map();
        const normalizedRows = rows.slice(1).map((row, index) => {
          const directExtId = cellFor(row, headerIndex, extHeaderAliases);
          const productUrl = cellFor(row, headerIndex, urlHeaderAliases);
          const extId = normalizeText(directExtId || extractExtIdFromUrl(productUrl));
          const affiliateUrl = cellFor(row, headerIndex, affiliateAliases);
          if (extId) csvExtIdCounts.set(extId, (csvExtIdCounts.get(extId) || 0) + 1);
          return { rowNumber: index + 2, extId, productUrl, affiliateUrl };
        });
        const previewRows = normalizedRows.map((row) => {
          if (!row.extId) return { ...row, status: 'missing-id', product: null };
          if (!row.affiliateUrl) return { ...row, status: 'missing-link', product: null };
          if (!isSafeAffiliateUrl(row.affiliateUrl)) return { ...row, status: 'invalid-link', product: null };
          if (csvExtIdCounts.get(row.extId) > 1) return { ...row, status: 'duplicate-csv-id', product: null };
          const matches = productsByExtId.get(row.extId) || [];
          if (matches.length === 0) return { ...row, status: 'not-found', product: null };
          if (matches.length > 1) return { ...row, status: 'ambiguous', product: null };
          return { ...row, status: 'matched', product: matches[0] };
        });
        if (!previewRows.some((row) => row.affiliateUrl)) throw new Error('No affiliate links were found in the CSV.');
        setImportPreview({ fileName: file.name, rows: previewRows });
      } catch (error) {
        setNotice({ type: 'error', text: error?.message || 'Could not parse this CSV.' });
      }
    };
    reader.readAsText(file);
  };

  const applyAffiliateImport = async () => {
    if (!importPreview) return;
    const matches = importPreview.rows.filter((row) => row.status === 'matched' && row.product && row.affiliateUrl);
    if (!matches.length) {
      setNotice({ type: 'warning', text: 'There are no exact, unique product matches to update.' });
      return;
    }
    if (typeof onBulkUpdateProducts !== 'function' && typeof onUpdateProduct !== 'function') {
      setNotice({ type: 'error', text: 'Affiliate import is preview-only until the product update callback is connected.' });
      return;
    }
    setImportBusy(true);
    setNotice(null);
    try {
      const result = await updateProducts(matches.map((row) => row.product), (product) => {
        const row = matches.find((candidate) => candidate.product === product);
        return { affiliateUrl: row?.affiliateUrl || '' };
      });
      setImportPreview(null);
      finishBatch('Affiliate link import', result);
    } catch (error) {
      setNotice({ type: 'error', text: error?.message || 'Affiliate links were not saved.' });
    } finally {
      setImportBusy(false);
    }
  };

  const statusLabel = (product) => {
    const status = statusOf(product);
    if (status === 'published') return 'Live';
    if (status === 'draft') return 'Draft / review';
    if (status === 'archived') return 'Archived';
    return 'Unspecified';
  };

  return (
    <div className="admin-catalog-view am-page">
      <header className="am-page-header">
        <div>
          <div className="am-eyebrow">CATALOG OPERATIONS</div>
          <h1>Master Catalog</h1>
          <p>Search, review, categorize and manage products. Counts and status reflect the data supplied by the connected catalog.</p>
        </div>
        <div className="am-header-actions">
          <input ref={fileInputRef} type="file" accept=".csv,text/csv" hidden onChange={handleCSVUpload} />
          <button type="button" className="am-button am-button-light" onClick={() => fileInputRef.current?.click()}>
            <Icon name="download" size={15} /> Import affiliate CSV
          </button>
          <button type="button" className="am-button am-button-light" onClick={exportCSV}>
            <Icon name="arrowDown" size={15} /> Export CSV{selectedProducts.length ? ` (${selectedProducts.length})` : ''}
          </button>
          <button type="button" className="am-button am-button-primary" onClick={onOpenAddProduct} disabled={!onOpenAddProduct}>
            <Icon name="plus" size={15} /> Add product
          </button>
        </div>
      </header>

      {notice && <div className={`am-notice is-${notice.type}`} role="status" aria-live="polite">{notice.text}</div>}

      <div className="am-stat-row" aria-label="Catalog status filters">
        <button type="button" className={`am-stat-chip${statusFilter === 'all' ? ' is-selected' : ''}`} onClick={() => setFilter(setStatusFilter, 'all')}><strong>{safeProducts.length}</strong><span>All products</span></button>
        <button type="button" className={`am-stat-chip${statusFilter === 'published' ? ' is-selected' : ''}`} onClick={() => setFilter(setStatusFilter, 'published')}><strong>{liveCount}</strong><span>Live</span></button>
        <button type="button" className={`am-stat-chip${statusFilter === 'draft' ? ' is-selected' : ''}`} onClick={() => setFilter(setStatusFilter, 'draft')}><strong>{draftCount}</strong><span>Draft / review</span></button>
        <button type="button" className={`am-stat-chip${statusFilter === 'archived' ? ' is-selected' : ''}`} onClick={() => setFilter(setStatusFilter, 'archived')}><strong>{archivedCount}</strong><span>Archived</span></button>
        <button type="button" className={`am-stat-chip${statusFilter === 'missing_link' ? ' is-selected' : ''}`} onClick={() => setFilter(setStatusFilter, 'missing_link')}><strong>{missingLinkCount}</strong><span>Missing affiliate link</span></button>
        <button type="button" className={`am-stat-chip${statusFilter === 'missing_image' ? ' is-selected' : ''}`} onClick={() => setFilter(setStatusFilter, 'missing_image')}><strong>{missingImageCount}</strong><span>Missing image</span></button>
        {untrackedCount > 0 && <button type="button" className={`am-stat-chip${statusFilter === 'untracked' ? ' is-selected' : ''}`} onClick={() => setFilter(setStatusFilter, 'untracked')}><strong>{untrackedCount}</strong><span>Status unspecified</span></button>}
      </div>

      <section className="am-panel am-catalog-filters" aria-label="Catalog filters">
        <label className="am-search-field">
          <Icon name="search" size={16} />
          <input type="search" value={searchQuery} onChange={(event) => { setSearchQuery(event.target.value); setPage(1); }} placeholder="Search title, category, store or exact product ID…" />
          {searchQuery && <button type="button" aria-label="Clear search" onClick={() => setFilter(setSearchQuery, '')}><Icon name="close" size={14} /></button>}
        </label>
        <select value={selectedCategory} onChange={(event) => setFilter(setSelectedCategory, event.target.value)} aria-label="Filter by category">
          <option>All Categories</option>
          <option value="Pinterest Viral Drops">Pinterest Viral Drops</option>
          {CATEGORY_GROUPS.map((category) => <option key={category} value={category}>{displayCategory(category)}</option>)}
        </select>
        <select value={selectedStore} onChange={(event) => setFilter(setSelectedStore, event.target.value)} aria-label="Filter by marketplace">
          {marketplaceOptions.map((store) => <option key={store} value={store}>{store}</option>)}
        </select>
        <select value={ratingFilter} onChange={(event) => setFilter(setRatingFilter, event.target.value)} aria-label="Filter by rating">
          <option value="all">All ratings</option>
          <option value="3.8">3.8+ rating</option>
          <option value="4">4.0+ rating</option>
          <option value="4.3">4.3+ rating</option>
          <option value="unrated">Unrated only</option>
        </select>
        <select value={sortBy} onChange={(event) => setFilter(setSortBy, event.target.value)} aria-label="Sort products">
          <option value="recent">Catalog order</option>
          <option value="title">Title A–Z</option>
          <option value="price-low">Price: low to high</option>
          <option value="price-high">Price: high to low</option>
          <option value="rating">Rating: high to low</option>
        </select>
      </section>

      {selectedIds.size > 0 && (
        <section className="am-bulk-toolbar" aria-label="Bulk actions">
          <div className="am-bulk-selection">
            <strong>{selectedIds.size} selected</strong>
            <button type="button" className="am-text-button" onClick={toggleSelectAllFiltered}>
              {allFilteredSelected ? 'Deselect filtered' : `Select all ${filteredProducts.length} filtered`}
            </button>
            <button type="button" className="am-text-button" onClick={() => setSelectedIds(new Set())}>Clear</button>
          </div>
          <div className="am-bulk-actions">
            <select value={bulkCategoryTarget} onChange={(event) => setBulkCategoryTarget(event.target.value)} aria-label="Bulk category target">
              {CATEGORY_GROUPS.map((category) => <option key={category} value={category}>Move to: {displayCategory(category)}</option>)}
            </select>
            <button type="button" className="am-button am-button-light" onClick={handleBulkChangeCategory} disabled={busyAction || (!onUpdateProduct && !onBulkUpdateProducts)}>Apply category</button>
            {statusFilter === 'archived' ? (
              <button type="button" className="am-button am-button-primary" onClick={handleBulkRestore} disabled={busyAction || (!onUpdateProduct && !onBulkUpdateProducts)}>Restore to live</button>
            ) : (
              <button type="button" className="am-button am-button-light" onClick={handleBulkArchive} disabled={busyAction || (!onUpdateProduct && !onBulkUpdateProducts)}>Archive</button>
            )}
            <button type="button" className="am-button am-button-danger" onClick={handleBulkPermanentDelete} disabled={busyAction || (!onDeleteProduct && !onBulkDeleteProducts)}>Delete permanently</button>
          </div>
        </section>
      )}

      <section className="am-panel am-catalog-table-panel" aria-label="Product catalog">
        <div className="am-table-scroll">
          <table className="am-catalog-table">
            <thead>
              <tr>
                <th className="am-check-col"><input type="checkbox" checked={allPageSelected} onChange={toggleSelectPage} aria-label="Select current page" /></th>
                <th>Product</th><th>Category</th><th>Price</th><th>Affiliate link</th><th>Status</th><th className="am-actions-col">Actions</th>
              </tr>
            </thead>
            <tbody>
              {paginatedProducts.length === 0 ? (
                <tr><td colSpan={7}><div className="am-empty-state"><Icon name="search" size={22} /><strong>No matching products</strong><span>Try clearing a filter or adjusting the search.</span></div></td></tr>
              ) : paginatedProducts.map((product, rowIndex) => {
                const id = keyOf(product);
                const selected = selectedIds.has(id);
                const image = productImage(product);
                const rating = getRating(product);
                const status = statusOf(product);
                const affiliateUrl = affiliateUrlFrom(product);
                return (
                  <tr key={id || `unkeyed-row-${rowIndex}`} className={selected ? 'is-selected' : ''}>
                    <td className="am-check-col"><input type="checkbox" checked={selected} onChange={() => toggleSelect(id)} disabled={!id} title={!id ? 'This row has no persisted database id and cannot be selected for bulk actions.' : ''} aria-label={`Select ${product.title || 'product'}`} /></td>
                    <td>
                      <div className="am-product-cell">
                        <div className="am-product-thumb">{image ? <img src={image} alt="" loading="lazy" /> : <Icon name="image" size={19} />}</div>
                        <div className="am-product-copy">
                          <strong title={product.title || ''}>{product.title || 'Untitled product'}</strong>
                          <span>{product.store || 'Store not set'} · ID: {product.ext_id || product.id || 'Not set'}{rating !== null ? ` · ★ ${rating}` : ' · Unrated'}</span>
                        </div>
                      </div>
                    </td>
                    <td><span className="am-category-badge">{displayCategory(product.category)}</span></td>
                    <td className="am-price-cell">{formatMoney(product.price)}</td>
                    <td>
                      {affiliateUrl ? (
                        <button type="button" className="am-link-pill" onClick={() => copyAffiliate(product)} title="Copy affiliate URL">
                          <Icon name={copiedId === id ? 'check' : 'link'} size={13} /> {copiedId === id ? 'Copied' : 'Ready'}
                        </button>
                      ) : <span className="am-missing-pill">Missing link</span>}
                    </td>
                    <td><span className={`am-status-badge is-${status}`}>{statusLabel(product)}</span></td>
                    <td className="am-actions-col">
                      <div className="am-row-actions">
                        {status === 'draft' && (onApproveProduct || onUpdateProduct || onBulkUpdateProducts) && (
                          <button type="button" className="am-icon-button is-approve" onClick={() => approveProduct(product)} disabled={busyAction || !id} title="Approve / publish" aria-label={`Approve ${product.title || 'product'}`}><Icon name="check" size={15} /></button>
                        )}
                        <button type="button" className="am-icon-button" onClick={() => onOpenEditProduct?.(product)} disabled={!onOpenEditProduct || !id} title="Edit product" aria-label={`Edit ${product.title || 'product'}`}><span aria-hidden="true">✎</span></button>
                        <button type="button" className="am-icon-button is-danger" disabled={!id || (!onDeleteProduct && !onBulkDeleteProducts)} onClick={() => setConfirmModal({
                          title: 'Delete this product?',
                          message: `This action cannot be undone. The configured delete callback will be called for “${product.title || 'Untitled product'}”.`,
                          confirmLabel: 'Delete permanently',
                          confirmTone: 'danger',
                          run: async () => {
                            const result = await deleteProducts([product]);
                            finishBatch('Delete', result);
                          }
                        })} title="Delete product" aria-label={`Delete ${product.title || 'product'}`}><Icon name="close" size={15} /></button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div className="am-pagination">
          <span>Showing {filteredProducts.length ? (page - 1) * pageSize + 1 : 0}–{Math.min(page * pageSize, filteredProducts.length)} of {filteredProducts.length}</span>
          <div className="am-pagination-controls">
            <label>Rows
              <select value={pageSize} onChange={(event) => { setPageSize(Number(event.target.value)); setPage(1); }} aria-label="Rows per page">
                {PAGE_SIZES.map((size) => <option key={size} value={size}>{size}</option>)}
              </select>
            </label>
            <button type="button" className="am-icon-button" onClick={() => setPage((value) => Math.max(1, value - 1))} disabled={page <= 1} aria-label="Previous page"><Icon name="chevronLeft" size={15} /></button>
            <span>Page {page} of {totalPages}</span>
            <button type="button" className="am-icon-button" onClick={() => setPage((value) => Math.min(totalPages, value + 1))} disabled={page >= totalPages} aria-label="Next page"><Icon name="chevronRight" size={15} /></button>
          </div>
        </div>
      </section>

      {confirmModal && (
        <div className="am-modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget && !busyAction) setConfirmModal(null); }}>
          <div className="am-modal" role="dialog" aria-modal="true" aria-labelledby="am-confirm-title">
            <span className="am-modal-icon"><Icon name={confirmModal.confirmTone === 'danger' ? 'shield' : 'check'} size={20} /></span>
            <h2 id="am-confirm-title">{confirmModal.title}</h2>
            <p>{confirmModal.message}</p>
            <div className="am-modal-actions">
              <button type="button" className="am-button am-button-light" onClick={() => setConfirmModal(null)} disabled={busyAction}>Cancel</button>
              <button type="button" className={`am-button ${confirmModal.confirmTone === 'danger' ? 'am-button-danger' : 'am-button-primary'}`} onClick={runConfirmation} disabled={busyAction}>
                {busyAction ? 'Working…' : confirmModal.confirmLabel || 'Confirm'}
              </button>
            </div>
          </div>
        </div>
      )}

      {importPreview && (
        <div className="am-modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget && !importBusy) setImportPreview(null); }}>
          <div className="am-modal am-import-modal" role="dialog" aria-modal="true" aria-labelledby="am-import-title">
            <div className="am-modal-heading">
              <div><span className="am-section-kicker">BATCH LINK MATCH</span><h2 id="am-import-title">Review affiliate CSV</h2></div>
              <button type="button" className="am-icon-button" onClick={() => setImportPreview(null)} disabled={importBusy} aria-label="Close import preview"><Icon name="close" size={16} /></button>
            </div>
            <p className="am-import-file">{importPreview.fileName} · {importPreview.rows.length} rows. Only exact, unique ext_id matches will be updated. A numeric <code>p_id</code> alone is not treated as a product match.</p>
            <div className="am-import-table-wrap">
              <table className="am-import-table">
                <thead><tr><th>CSV row</th><th>Product</th><th>Ext ID</th><th>Affiliate URL</th><th>Match</th></tr></thead>
                <tbody>
                  {importPreview.rows.map((row) => (
                    <tr key={`${row.rowNumber}-${row.extId}`}>
                      <td>{row.rowNumber}</td>
                      <td>{row.product?.title || (row.status === 'matched' ? 'Matched product' : '—')}</td>
                      <td><code>{row.extId || '—'}</code></td>
                      <td className="am-import-url" title={row.affiliateUrl}>{row.affiliateUrl || '—'}</td>
                      <td><span className={`am-import-status is-${row.status}`}>{row.status === 'matched' ? 'Exact match' : row.status.replace(/-/g, ' ')}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="am-modal-actions">
              <button type="button" className="am-button am-button-light" onClick={() => setImportPreview(null)} disabled={importBusy}>Cancel</button>
              <button type="button" className="am-button am-button-primary" onClick={applyAffiliateImport} disabled={importBusy || !importPreview.rows.some((row) => row.status === 'matched') || (!onUpdateProduct && !onBulkUpdateProducts)}>
                {importBusy ? 'Applying…' : `Apply ${importPreview.rows.filter((row) => row.status === 'matched').length} exact match(es)`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
