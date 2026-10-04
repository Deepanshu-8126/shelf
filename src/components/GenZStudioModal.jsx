import React, { useState, useMemo } from 'react';
import Icon from './Icon.jsx';
import ProductCard from './ProductCard.jsx';

export default function GenZStudioModal({ isOpen, onClose, products, savedIds, onToggleSaved, onInstantOrder, onViewDetail }) {
  const [activeTab, setActiveTab] = useState('all'); // 'all', 'jerseys', 'spider', 'accessories', 'cargos', 'dresses'
  const [activeColor, setActiveColor] = useState('all');
  const [searchFilter, setSearchFilter] = useState('');

  // Extract all Pinterest Gen-Z drops
  const genZProducts = useMemo(() => {
    return products.filter((p) => {
      const isPinterest = Boolean(
        p.isPinterestCombo ||
        p.isTrending ||
        (p.collectionId || '').includes('pinterest') ||
        (p.collectionId || '').includes('brasilcore') ||
        (p.collectionId || '').includes('blokecore') ||
        (p.title || '').toLowerCase().includes('jersey') ||
        (p.title || '').toLowerCase().includes('spider') ||
        (p.title || '').toLowerCase().includes('y2k') ||
        (p.title || '').toLowerCase().includes('ferrari') ||
        (p.title || '').toLowerCase().includes('cargo') ||
        (p.title || '').toLowerCase().includes('ring') ||
        (p.title || '').toLowerCase().includes('hoop') ||
        (p.category || '').toLowerCase().includes('accessories') ||
        (p.category || '').toLowerCase().includes('baby tees')
      );
      return isPinterest;
    });
  }, [products]);

  const filteredItems = useMemo(() => {
    return genZProducts.filter((p) => {
      const title = (p.title || '').toLowerCase();
      const cat = (p.category || '').toLowerCase();
      const coll = (p.collectionId || '').toLowerCase();
      const color = (p.primaryColor || '').toLowerCase();
      const colors = Array.isArray(p.colors) ? p.colors.join(' ').toLowerCase() : '';

      // Tab filter
      if (activeTab === 'jerseys' && !title.includes('jersey') && !coll.includes('blokecore')) return false;
      if (activeTab === 'spider' && !title.includes('spider') && !title.includes('graphic') && !title.includes('tee')) return false;
      if (activeTab === 'accessories' && !cat.includes('accessories') && !title.includes('ring') && !title.includes('sunglass') && !title.includes('hoop')) return false;
      if (activeTab === 'cargos' && !title.includes('cargo') && !title.includes('baggy') && !title.includes('pant') && !title.includes('jorts')) return false;
      if (activeTab === 'dresses' && !cat.includes('dresses') && !title.includes('bodycon') && !title.includes('dress')) return false;

      // Color filter
      if (activeColor !== 'all') {
        const targetColor = activeColor.toLowerCase();
        if (!color.includes(targetColor) && !colors.includes(targetColor) && !title.includes(targetColor)) return false;
      }

      // Search filter
      if (searchFilter.trim()) {
        const q = searchFilter.toLowerCase();
        if (!title.includes(q) && !cat.includes(q) && !coll.includes(q)) return false;
      }

      return true;
    });
  }, [genZProducts, activeTab, activeColor, searchFilter]);

  if (!isOpen) return null;

  return (
    <div className="genz-modal-backdrop" onClick={onClose}>
      <div className="genz-studio-container" onClick={(e) => e.stopPropagation()}>
        {/* Header Strip */}
        <div className="genz-studio-header">
          <div className="genz-header-left">
            <span className="genz-live-badge">PINTEREST 2026 · GEN-Z CURATION</span>
            <h2>Viral Streetwear & Aesthetic Vault</h2>
            <p>Curated from Pinterest global feeds · Blokecore jerseys, graphic tees, baggy cargos & statement jewelry.</p>
          </div>
          <button type="button" className="genz-close-btn" onClick={onClose} aria-label="Close Studio">
            ✕
          </button>
        </div>

        {/* Tab & Color Bar */}
        <div className="genz-controls-strip">
          <div className="genz-tabs-row">
            {[
              { id: 'all', label: 'All Viral', count: genZProducts.length },
              { id: 'jerseys', label: 'Blokecore Jerseys' },
              { id: 'spider', label: 'Graphic & Spider Tees' },
              { id: 'accessories', label: 'Rings & Jewelry' },
              { id: 'cargos', label: 'Baggy Cargos & Jorts' },
              { id: 'dresses', label: 'Party Bodycons' },
            ].map((tab) => (
              <button
                key={tab.id}
                type="button"
                className={`genz-tab-pill${activeTab === tab.id ? ' is-active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <span>{tab.label}</span>
                {tab.count !== undefined && <span className="tab-badge">{tab.count}</span>}
              </button>
            ))}
          </div>

          <div className="genz-right-search-row">
            {/* Color Swatch Row */}
            <div className="genz-color-swatches" title="Filter by colorway shade">
              {[
                { name: 'all', hex: 'conic-gradient(red, yellow, lime, aqua, blue, magenta, red)' },
                { name: 'black', hex: '#18181b' },
                { name: 'white', hex: '#f8fafc' },
                { name: 'pink', hex: '#fda4af' },
                { name: 'green', hex: '#86efac' },
                { name: 'brown', hex: '#a8715a' },
                { name: 'red', hex: '#e11d48' },
                { name: 'yellow', hex: '#fef08a' }
              ].map((c) => (
                <button
                  key={c.name}
                  type="button"
                  className={`genz-color-dot${activeColor === c.name ? ' is-active' : ''}`}
                  style={{ background: c.hex }}
                  onClick={() => setActiveColor(activeColor === c.name ? 'all' : c.name)}
                />
              ))}
            </div>

            <div className="genz-search-input-wrap">
              <Icon name="search" size={14} />
              <input
                type="text"
                placeholder="Search Gen-Z drops..."
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
              />
              {searchFilter && (
                <button type="button" className="genz-search-clear" onClick={() => setSearchFilter('')}>✕</button>
              )}
            </div>
          </div>
        </div>

        {/* Product Grid */}
        <div className="genz-products-scrollable-area">
          <div className="genz-stats-meta">
            <span>Showing <strong>{filteredItems.length}</strong> verified Gen-Z aesthetic drops</span>
            {(activeTab !== 'all' || activeColor !== 'all' || searchFilter) && (
              <button
                type="button"
                className="genz-reset-btn"
                onClick={() => { setActiveTab('all'); setActiveColor('all'); setSearchFilter(''); }}
              >
                Reset Studio Filters ✕
              </button>
            )}
          </div>

          {filteredItems.length > 0 ? (
            <div className="product-grid genz-product-grid">
              {filteredItems.map((product) => (
                <ProductCard
                  key={product.id}
                  product={{ ...product, saved: savedIds.includes(product.id) }}
                  isPublic
                  onToggleSaved={onToggleSaved}
                  onInstantOrder={onInstantOrder}
                  onViewDetail={onViewDetail}
                />
              ))}
            </div>
          ) : (
            <div className="genz-empty-state">
              <span className="empty-icon">🛹</span>
              <h3>No Gen-Z drops found</h3>
              <p>Try switching categories or colorway filters above.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
