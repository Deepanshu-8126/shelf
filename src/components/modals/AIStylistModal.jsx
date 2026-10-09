import React, { useState, useMemo } from 'react';
import Icon from '../ui/Icon.jsx';
import ProductCard from '../ui/ProductCard.jsx';

function money(value) {
  return `₹${Number(value || 0).toLocaleString('en-IN')}`;
}

export default function AIStylistModal({ allProducts = [], onClose, onViewProduct, onInstantOrder }) {
  const [prompt, setPrompt] = useState('');
  const [activeTag, setActiveTag] = useState('All');

  const QUICK_INTENT_PROMPTS = [
    { label: '✨ Date Night Bodycon', query: 'bodycon' },
    { label: '🔥 Viral Gen-Z Jerseys', query: 'jersey' },
    { label: '🌸 Aesthetic Summer Tops', query: 'peplum' },
    { label: '💰 Best Outfits Under ₹499', query: 'under499' },
    { label: '👑 Luxury Festive Kurtis', query: 'kurti' },
    { label: '❄️ Cozy Winter Layers', query: 'puffer' },
  ];

  const matchedProducts = useMemo(() => {
    const q = prompt.trim().toLowerCase();
    if (!q) {
      // Default: Return top 6 highest trend scored picks
      return allProducts.slice(0, 6);
    }

    if (q === 'under499' || q.includes('under 499') || q.includes('under 500')) {
      return allProducts.filter((p) => Number(p.price) <= 499).slice(0, 6);
    }

    return allProducts.filter((p) => {
      const fullText = `${p.title} ${p.subtitle} ${p.category}`.toLowerCase();
      return q.split(' ').some((word) => word.length > 2 && fullText.includes(word));
    }).slice(0, 6);
  }, [allProducts, prompt]);

  return (
    <div className="modal-backdrop stylist-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-card stylist-card" onClick={(e) => e.stopPropagation()}>
        <button className="icon-button detail-close-btn" type="button" onClick={onClose} aria-label="Close AI Stylist">
          ✕
        </button>

        <div className="stylist-header">
          <div className="stylist-badge">
            <span className="stylist-sparkle">✦</span>
            <span>GEN-Z AI PERSONAL STYLIST</span>
          </div>
          <h2>What vibe are you dressing for?</h2>
          <p>Tell the AI stylist your occasion, mood, or budget to get instant tailored outfit recommendations.</p>
        </div>

        {/* Search / Intent Input Box */}
        <div className="stylist-input-wrap">
          <Icon name="search" size={18} />
          <input 
            type="text" 
            placeholder="e.g. 'Viral college fest outfit under ₹500' or 'Maroon bodycon for party'"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            autoFocus
          />
          {prompt && (
            <button className="search-clear-btn" type="button" onClick={() => setPrompt('')}>✕</button>
          )}
        </div>

        {/* Quick Vibe Chips */}
        <div className="stylist-quick-tags">
          <span className="quick-tags-label">Quick Intent:</span>
          {QUICK_INTENT_PROMPTS.map((item) => (
            <button
              key={item.label}
              type="button"
              className={`stylist-tag-btn${prompt === item.query ? ' is-active' : ''}`}
              onClick={() => setPrompt(item.query)}
            >
              {item.label}
            </button>
          ))}
        </div>

        {/* Curated Recommendations Output */}
        <div className="stylist-results-section">
          <div className="results-topline">
            <strong>AI Curated Recommendations ({matchedProducts.length})</strong>
            <span>Verified 4.2★+ Quality & Free Delivery</span>
          </div>

          <div className="product-grid public-product-grid" style={{ gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: '14px' }}>
            {matchedProducts.map((p) => (
              <ProductCard
                key={p.id}
                product={p}
                isPublic
                onViewDetail={(prod) => {
                  onClose();
                  onViewProduct?.(prod.id);
                }}
                onInstantOrder={(prod) => {
                  onClose();
                  onInstantOrder?.(prod);
                }}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
