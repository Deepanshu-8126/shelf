import React, { useState, useMemo, useEffect } from 'react';
import Icon from './Icon.jsx';
import { getProductClickUrl } from '../affiliate.js';

function money(value) {
  return `₹${Number(value || 0).toLocaleString('en-IN')}`;
}

export default function OutfitBuilderModal({ allProducts = [], onClose }) {
  // 1. Separate exact categories with precision
  const topsList = useMemo(() => {
    return allProducts.filter((p) => {
      const cat = (p.category || '').toLowerCase();
      const title = (p.title || '').toLowerCase();
      return cat.includes('top') || cat.includes('tunic') || title.includes('top') || title.includes('shirt') || title.includes('t-shirt') || title.includes('tee') || title.includes('crop');
    });
  }, [allProducts]);

  const kurtisList = useMemo(() => {
    return allProducts.filter((p) => {
      const cat = (p.category || '').toLowerCase();
      const title = (p.title || '').toLowerCase();
      return cat.includes('kurti') || cat.includes('ethnic') || title.includes('kurti') || title.includes('anarkali') || title.includes('kurta');
    });
  }, [allProducts]);

  const dressesList = useMemo(() => {
    return allProducts.filter((p) => {
      const cat = (p.category || '').toLowerCase();
      const title = (p.title || '').toLowerCase();
      return cat.includes('dress') || title.includes('dress') || title.includes('bodycon') || title.includes('maxi');
    });
  }, [allProducts]);

  const bottomsAndLayersList = useMemo(() => {
    return allProducts.filter((p) => {
      const cat = (p.category || '').toLowerCase();
      const title = (p.title || '').toLowerCase();
      return cat.includes('bottom') || cat.includes('winter') || cat.includes('pant') || cat.includes('skirt') || cat.includes('palazzo') || cat.includes('cardigan') || cat.includes('puffer') || cat.includes('jacket') || title.includes('cargo') || title.includes('pant') || title.includes('skirt') || title.includes('palazzo') || title.includes('cardigan') || title.includes('puffer');
    });
  }, [allProducts]);

  const accessoriesList = useMemo(() => {
    const accFromProducts = allProducts.filter((p) => {
      const cat = (p.category || '').toLowerCase();
      const title = (p.title || '').toLowerCase();
      return cat.includes('accessories') || cat.includes('beauty') || title.includes('hoop') || title.includes('ring') || title.includes('bag') || title.includes('earring') || title.includes('necklace') || title.includes('sunglass');
    });
    if (accFromProducts.length > 0) return accFromProducts;
    return [
      { id: 'acc-1', title: 'Vintage Chunky Gold Hoops', category: 'Accessories', price: 199, image: '/images/gold-hoops.jpg' },
      { id: 'acc-2', title: 'Minimalist Baguette Shoulder Bag', category: 'Accessories', price: 449, image: '/images/crossbody-bag.jpg' },
      { id: 'acc-3', title: 'Pearl Choker Necklace', category: 'Accessories', price: 249, image: '/images/linen-set.jpg' },
    ];
  }, [allProducts]);

  // Selected state
  const [selectedMainType, setSelectedMainType] = useState('tops'); // 'tops', 'kurtis', 'dresses'
  const [selectedMain, setSelectedMain] = useState(() => topsList[0] || dressesList[0] || allProducts[0] || null);
  const [selectedBottom, setSelectedBottom] = useState(() => bottomsAndLayersList[0] || null);
  const [selectedAcc, setSelectedAcc] = useState(() => accessoriesList[0] || null);

  // Lock body scroll while modal is open
  useEffect(() => {
    const origOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      document.body.style.overflow = origOverflow;
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [onClose]);

  const rawTotal = (Number(selectedMain?.price || 0) + Number(selectedBottom?.price || 0) + Number(selectedAcc?.price || 0));

  const activeMainList = selectedMainType === 'tops' ? topsList : selectedMainType === 'kurtis' ? kurtisList : dressesList;

  return (
    <div className="modal-backdrop outfit-builder-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-card outfit-builder-card" onClick={(e) => e.stopPropagation()}>
        <button className="icon-button detail-close-btn" type="button" onClick={onClose} aria-label="Close outfit builder">
          ✕
        </button>

        <div className="outfit-builder-header">
          <div className="outfit-kicker-pill">
            <span className="sparkle-icon">✦</span>
            <span>MIX & MATCH STYLE STUDIO</span>
          </div>
          <h2>Outfit Lookbook Builder</h2>
          <p>Curate your head-to-toe ensemble · Handpicked aesthetic pairing from your verified shelf catalog.</p>
        </div>

        <div className="outfit-builder-layout">
          {/* Left: Live Curated Lookbook Stage */}
          <div className="outfit-canvas-stage">
            <div className="outfit-stage-title">
              <span>Curated Outfit Look</span>
              <span className="items-count-tag">3 Pieces Selected</span>
            </div>
            
            <div className="outfit-stacked-pieces">
              {/* Piece 1: Main Top / Dress / Kurti */}
              {selectedMain && (
                <div className="outfit-piece-card">
                  <span className="piece-tag">Piece 1 · {selectedMain.category || 'Main Fit'}</span>
                  <div className="piece-inner">
                    <div className="piece-image-wrap">
                      <img src={selectedMain.image} alt={selectedMain.title} loading="lazy" />
                    </div>
                    <div className="piece-meta">
                      <strong>{selectedMain.title}</strong>
                      <span className="piece-price">{money(selectedMain.price)}</span>
                      <a 
                        href={getProductClickUrl(selectedMain)} 
                        target="_blank" 
                        rel="noreferrer" 
                        className="piece-shop-link"
                      >
                        Shop this item <Icon name="arrowUpRight" size={11} />
                      </a>
                    </div>
                  </div>
                </div>
              )}

              {/* Piece 2: Layer / Bottomwear */}
              {selectedBottom && (
                <div className="outfit-piece-card">
                  <span className="piece-tag">Piece 2 · {selectedBottom.category || 'Layer / Bottom'}</span>
                  <div className="piece-inner">
                    <div className="piece-image-wrap">
                      <img src={selectedBottom.image} alt={selectedBottom.title} loading="lazy" />
                    </div>
                    <div className="piece-meta">
                      <strong>{selectedBottom.title}</strong>
                      <span className="piece-price">{money(selectedBottom.price)}</span>
                      <a 
                        href={getProductClickUrl(selectedBottom)} 
                        target="_blank" 
                        rel="noreferrer" 
                        className="piece-shop-link"
                      >
                        Shop this item <Icon name="arrowUpRight" size={11} />
                      </a>
                    </div>
                  </div>
                </div>
              )}

              {/* Piece 3: Accent Accessory */}
              {selectedAcc && (
                <div className="outfit-piece-card">
                  <span className="piece-tag">Piece 3 · {selectedAcc.category || 'Accessory'}</span>
                  <div className="piece-inner">
                    <div className="piece-image-wrap">
                      <img src={selectedAcc.image} alt={selectedAcc.title} loading="lazy" />
                    </div>
                    <div className="piece-meta">
                      <strong>{selectedAcc.title}</strong>
                      <span className="piece-price">{money(selectedAcc.price)}</span>
                      {selectedAcc.productUrl || selectedAcc.affiliateUrl ? (
                        <a 
                          href={getProductClickUrl(selectedAcc)} 
                          target="_blank" 
                          rel="noreferrer" 
                          className="piece-shop-link"
                        >
                          Shop this item <Icon name="arrowUpRight" size={11} />
                        </a>
                      ) : null}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Total Pricing Bar */}
            <div className="outfit-pricing-summary">
              <div className="pricing-left">
                <span className="summary-label">Estimated Total (3 Items):</span>
                <div className="summary-prices">
                  <strong>{money(rawTotal)}</strong>
                  <span className="sold-separately-note">Sold separately via individual store links</span>
                </div>
              </div>
            </div>
          </div>

          {/* Right: Pickers for each slot */}
          <div className="outfit-selectors-col">
            {/* Slot 1: Category tabs + Main Selector */}
            <div className="selector-group">
              <div className="selector-head-row">
                <label className="selector-title">1. Main Garment</label>
                <div className="main-cat-pills">
                  <button
                    type="button"
                    className={`cat-pill-btn${selectedMainType === 'tops' ? ' is-active' : ''}`}
                    onClick={() => { setSelectedMainType('tops'); if (topsList[0]) setSelectedMain(topsList[0]); }}
                  >
                    Tops & Tunics ({topsList.length})
                  </button>
                  <button
                    type="button"
                    className={`cat-pill-btn${selectedMainType === 'kurtis' ? ' is-active' : ''}`}
                    onClick={() => { setSelectedMainType('kurtis'); if (kurtisList[0]) setSelectedMain(kurtisList[0]); }}
                  >
                    Kurtis ({kurtisList.length})
                  </button>
                  <button
                    type="button"
                    className={`cat-pill-btn${selectedMainType === 'dresses' ? ' is-active' : ''}`}
                    onClick={() => { setSelectedMainType('dresses'); if (dressesList[0]) setSelectedMain(dressesList[0]); }}
                  >
                    Dresses ({dressesList.length})
                  </button>
                </div>
              </div>

              <div className="selector-scroll-strip">
                {activeMainList.map((prod) => (
                  <button
                    key={prod.id}
                    type="button"
                    className={`selector-item-btn${selectedMain?.id === prod.id ? ' is-selected' : ''}`}
                    onClick={() => setSelectedMain(prod)}
                  >
                    <div className="item-btn-img-box">
                      <img src={prod.image} alt={prod.title} loading="lazy" />
                    </div>
                    <span className="item-btn-title">{prod.title}</span>
                    <span className="item-btn-price">{money(prod.price)}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Slot 2: Layers & Bottoms */}
            <div className="selector-group">
              <label className="selector-title">2. Bottomwear & Outerwear ({bottomsAndLayersList.length})</label>
              <div className="selector-scroll-strip">
                {bottomsAndLayersList.map((bot) => (
                  <button
                    key={bot.id}
                    type="button"
                    className={`selector-item-btn${selectedBottom?.id === bot.id ? ' is-selected' : ''}`}
                    onClick={() => setSelectedBottom(bot)}
                  >
                    <div className="item-btn-img-box">
                      <img src={bot.image} alt={bot.title} loading="lazy" />
                    </div>
                    <span className="item-btn-title">{bot.title}</span>
                    <span className="item-btn-price">{money(bot.price)}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Slot 3: Accent Accessories */}
            <div className="selector-group">
              <label className="selector-title">3. Jewelry & Accessories</label>
              <div className="selector-scroll-strip">
                {accessoriesList.map((acc) => (
                  <button
                    key={acc.id}
                    type="button"
                    className={`selector-item-btn${selectedAcc?.id === acc.id ? ' is-selected' : ''}`}
                    onClick={() => setSelectedAcc(acc)}
                  >
                    <div className="item-btn-img-box">
                      <img src={acc.image} alt={acc.title} loading="lazy" />
                    </div>
                    <span className="item-btn-title">{acc.title}</span>
                    <span className="item-btn-price">{money(acc.price)}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
