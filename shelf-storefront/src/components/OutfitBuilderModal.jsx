import React, { useState, useMemo } from 'react';
import Icon from './Icon.jsx';
import InstantOrderModal from './InstantOrderModal.jsx';

function money(value) {
  return `₹${Number(value || 0).toLocaleString('en-IN')}`;
}

export default function OutfitBuilderModal({ allProducts = [], onClose }) {
  // Categorize available items
  const topsAndDresses = useMemo(() => {
    return allProducts.filter((p) => {
      const cat = (p.category || '').toLowerCase();
      return cat.includes('dress') || cat.includes('top') || cat.includes('kurti');
    });
  }, [allProducts]);

  const bottomsAndLayers = useMemo(() => {
    const list = allProducts.filter((p) => {
      const cat = (p.category || '').toLowerCase();
      return cat.includes('bottom') || cat.includes('winter') || cat.includes('ethnic') || cat.includes('cardigan') || cat.includes('puffer');
    });
    return list.length ? list : topsAndDresses.slice().reverse();
  }, [allProducts, topsAndDresses]);

  const accessories = useMemo(() => {
    return [
      { id: 'acc-1', title: 'Vintage Gold Hoops', category: 'Accessories', price: 199, image: '/images/gold-hoops.jpg' },
      { id: 'acc-2', title: 'Minimalist Baguette Bag', category: 'Accessories', price: 449, image: '/images/crossbody-bag.jpg' },
      { id: 'acc-3', title: 'Pearl Choker Necklace', category: 'Accessories', price: 249, image: '/images/linen-set.jpg' },
    ];
  }, []);

  const [selectedTop, setSelectedTop] = useState(() => topsAndDresses[0] || null);
  const [selectedBottom, setSelectedBottom] = useState(() => bottomsAndLayers[0] || null);
  const [selectedAcc, setSelectedAcc] = useState(() => accessories[0] || null);
  const [orderModalCombo, setOrderModalCombo] = useState(null);

  const rawTotal = (Number(selectedTop?.price || 0) + Number(selectedBottom?.price || 0) + Number(selectedAcc?.price || 0));
  // 15% Combo Discount
  const comboDiscount = Math.round(rawTotal * 0.15);
  const comboFinalPrice = rawTotal - comboDiscount;

  const handleOrderCombo = () => {
    const comboProduct = {
      id: `combo-${Date.now()}`,
      title: `Curated Outfit Combo: ${selectedTop?.title || ''} + ${selectedBottom?.title || ''}`,
      price: comboFinalPrice,
      oldPrice: rawTotal,
      image: selectedTop?.image || '/images/meesho-dress-ae6lv9.webp',
      category: 'Curated 3-Piece Outfit',
      sizes: ['S', 'M', 'L', 'XL'],
      isCombo: true
    };
    setOrderModalCombo(comboProduct);
  };

  return (
    <div className="modal-backdrop outfit-builder-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-card outfit-builder-card" onClick={(e) => e.stopPropagation()}>
        <button className="icon-button detail-close-btn" type="button" onClick={onClose} aria-label="Close outfit builder">
          ✕
        </button>

        <div className="outfit-builder-header">
          <span className="outfit-kicker">✦ STYLE STUDIO</span>
          <h2>Mix & Match Outfit Builder</h2>
          <p>Curate your full head-to-toe look with a matching top, layer & accessory with <strong>15% Combo Savings</strong>.</p>
        </div>

        <div className="outfit-builder-layout">
          {/* Left: Live 3-Piece Canvas Stage */}
          <div className="outfit-canvas-stage">
            <div className="outfit-stage-title">Your Live Outfit Look</div>
            
            <div className="outfit-stacked-pieces">
              {/* Piece 1: Top / Dress */}
              <div className="outfit-piece-card">
                <span className="piece-tag">Piece 1: Main Top / Dress</span>
                <div className="piece-inner">
                  <img src={selectedTop?.image} alt={selectedTop?.title} />
                  <div className="piece-meta">
                    <strong>{selectedTop?.title}</strong>
                    <span>{money(selectedTop?.price)}</span>
                  </div>
                </div>
              </div>

              {/* Piece 2: Layer / Bottom */}
              <div className="outfit-piece-card">
                <span className="piece-tag">Piece 2: Layer / Bottomwear</span>
                <div className="piece-inner">
                  <img src={selectedBottom?.image} alt={selectedBottom?.title} />
                  <div className="piece-meta">
                    <strong>{selectedBottom?.title}</strong>
                    <span>{money(selectedBottom?.price)}</span>
                  </div>
                </div>
              </div>

              {/* Piece 3: Accent Accessory */}
              <div className="outfit-piece-card">
                <span className="piece-tag">Piece 3: Accent Accessory</span>
                <div className="piece-inner">
                  <img src={selectedAcc?.image} alt={selectedAcc?.title} />
                  <div className="piece-meta">
                    <strong>{selectedAcc?.title}</strong>
                    <span>{money(selectedAcc?.price)}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Total Pricing Bar */}
            <div className="outfit-pricing-summary">
              <div className="pricing-left">
                <span className="summary-label">Combo Bundle Price (3 Items):</span>
                <div className="summary-prices">
                  <strong>{money(comboFinalPrice)}</strong>
                  <del>{money(rawTotal)}</del>
                  <span className="combo-savings-badge">Save 15% (₹{comboDiscount})</span>
                </div>
              </div>
              <button 
                className="button button-dark outfit-order-btn" 
                type="button"
                onClick={handleOrderCombo}
              >
                <span>Order Combo (COD) ↗</span>
              </button>
            </div>
          </div>

          {/* Right: Pickers for each slot */}
          <div className="outfit-selectors-col">
            {/* Slot 1: Tops & Dresses */}
            <div className="selector-group">
              <label className="selector-title">1. Choose Main Topwear / Dress</label>
              <div className="selector-scroll-strip">
                {topsAndDresses.slice(0, 8).map((top) => (
                  <button
                    key={top.id}
                    type="button"
                    className={`selector-item-btn${selectedTop?.id === top.id ? ' is-selected' : ''}`}
                    onClick={() => setSelectedTop(top)}
                  >
                    <img src={top.image} alt={top.title} />
                    <span className="item-btn-price">{money(top.price)}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Slot 2: Layers & Bottoms */}
            <div className="selector-group">
              <label className="selector-title">2. Choose Layer / Bottomwear</label>
              <div className="selector-scroll-strip">
                {bottomsAndLayers.slice(0, 8).map((bot) => (
                  <button
                    key={bot.id}
                    type="button"
                    className={`selector-item-btn${selectedBottom?.id === bot.id ? ' is-selected' : ''}`}
                    onClick={() => setSelectedBottom(bot)}
                  >
                    <img src={bot.image} alt={bot.title} />
                    <span className="item-btn-price">{money(bot.price)}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Slot 3: Accessories */}
            <div className="selector-group">
              <label className="selector-title">3. Choose Matching Accessory</label>
              <div className="selector-scroll-strip">
                {accessories.map((acc) => (
                  <button
                    key={acc.id}
                    type="button"
                    className={`selector-item-btn${selectedAcc?.id === acc.id ? ' is-selected' : ''}`}
                    onClick={() => setSelectedAcc(acc)}
                  >
                    <img src={acc.image} alt={acc.title} />
                    <span className="item-btn-price">{money(acc.price)}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {orderModalCombo && (
        <InstantOrderModal 
          product={orderModalCombo} 
          onClose={() => setOrderModalCombo(null)} 
        />
      )}
    </div>
  );
}
