import React, { useState, useEffect, useMemo, useRef } from 'react';
import Icon from './Icon.jsx';
import ProductCard, { getColorHex } from './ProductCard.jsx';

function money(value) {
  return `₹${Number(value || 0).toLocaleString('en-IN')}`;
}

export default function ProductDetailModal({ product: initialProduct, allProducts = [], onClose, onInstantOrder, onTryOnProduct }) {
  const [product, setProduct] = useState(initialProduct);
  const [activeImage, setActiveImage] = useState(0);
  const [selectedColor, setSelectedColor] = useState('Standard');
  const [selectedSize, setSelectedSize] = useState(() => initialProduct?.sizes?.[0] || 'M');
  const [viewMode, setViewMode] = useState('2d'); // '2d' | '3d'
  
  // 3D Turntable Stage States
  const [stageRotX, setStageRotX] = useState(6);
  const [stageRotY, setStageRotY] = useState(0);
  const [isDragging3D, setIsDragging3D] = useState(false);
  const [autoSpin3D, setAutoSpin3D] = useState(false);
  const [lightMode3D, setLightMode3D] = useState(0); // 0: Studio White, 1: Cyber Neon, 2: Noir Gold
  const dragStartPos = useRef({ x: 0, y: 0 });
  const modalTopRef = useRef(null);

  // Auto-Spin Animation
  useEffect(() => {
    if (!autoSpin3D || viewMode !== '3d') return undefined;
    const interval = setInterval(() => {
      setStageRotY((prev) => (prev + 1.2) % 360);
    }, 25);
    return () => clearInterval(interval);
  }, [autoSpin3D, viewMode]);

  useEffect(() => {
    if (initialProduct) {
      setProduct(initialProduct);
      setActiveImage(0);
      setSelectedSize(initialProduct.sizes?.[0] || 'M');
      if (Array.isArray(initialProduct.colors) && initialProduct.colors.length) {
        setSelectedColor(initialProduct.colors[0]);
      }
    }
  }, [initialProduct]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose?.();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!product) return null;

  // Gallery & Cloud Images
  const gallery = Array.isArray(product.galleryImages) && product.galleryImages.length 
    ? product.galleryImages 
    : (Array.isArray(product.gallery) && product.gallery.length ? product.gallery : [product.image]);

  const uniqueImages = [...new Set([product.image, ...gallery])].filter(Boolean);
  const colors = Array.isArray(product.colors) && product.colors.length ? product.colors : ['Classic'];
  const sizes = Array.isArray(product.sizes) && product.sizes.length ? product.sizes : ['S', 'M', 'L', 'XL'];
  const discount = product.oldPrice && product.price
    ? Math.max(1, Math.round((1 - Number(product.price) / Number(product.oldPrice)) * 100))
    : 0;

  // Strict Category Matching for Related Looks
  const relatedProducts = useMemo(() => {
    const targetCat = (product.category || '').trim().toLowerCase();
    return allProducts
      .filter((p) => {
        if (p.id === product.id) return false;
        const pCat = (p.category || '').trim().toLowerCase();
        return pCat === targetCat;
      })
      .sort((a, b) => Number(b.rating || 4.2) - Number(a.rating || 4.2))
      .slice(0, 4);
  }, [allProducts, product]);

  const isInStock = product.inStock !== false;

  const handleSelectRelated = (relProduct) => {
    setProduct(relProduct);
    setActiveImage(0);
    setSelectedSize('M');
    if (Array.isArray(relProduct.colors) && relProduct.colors.length) {
      setSelectedColor(relProduct.colors[0]);
    }
    modalTopRef.current?.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // 3D Turntable Drag Handlers
  const handleStageMouseDown = (e) => {
    setIsDragging3D(true);
    setAutoSpin3D(false);
    dragStartPos.current = { x: e.clientX, y: e.clientY };
  };

  const handleStageMouseMove = (e) => {
    if (!isDragging3D) return;
    const deltaX = e.clientX - dragStartPos.current.x;
    const deltaY = e.clientY - dragStartPos.current.y;
    setStageRotY((prev) => prev + deltaX * 0.7);
    setStageRotX((prev) => Math.max(-35, Math.min(35, prev - deltaY * 0.4)));
    dragStartPos.current = { x: e.clientX, y: e.clientY };
  };

  const handleStageMouseUp = () => {
    setIsDragging3D(false);
  };

  const handleStageTouchStart = (e) => {
    if (e.touches.length === 1) {
      setIsDragging3D(true);
      setAutoSpin3D(false);
      dragStartPos.current = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    }
  };

  const handleStageTouchMove = (e) => {
    if (!isDragging3D || e.touches.length !== 1) return;
    const deltaX = e.touches[0].clientX - dragStartPos.current.x;
    const deltaY = e.touches[0].clientY - dragStartPos.current.y;
    setStageRotY((prev) => prev + deltaX * 0.8);
    setStageRotX((prev) => Math.max(-35, Math.min(35, prev - deltaY * 0.5)));
    dragStartPos.current = { x: e.touches[0].clientX, y: e.touches[0].clientY };
  };

  return (
    <div className="modal-backdrop product-detail-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-card product-detail-card" ref={modalTopRef} onClick={(e) => e.stopPropagation()}>
        <button className="icon-button detail-close-btn" type="button" onClick={onClose} aria-label="Close product view">
          ✕
        </button>

        <div className="product-detail-layout">
          {/* Left: Gallery & 3D Spatial Turntable Stage */}
          <div className="detail-media-column">
            {/* View Mode Segmented Control */}
            <div className="detail-view-toggle-bar">
              <button 
                type="button" 
                className={`detail-toggle-btn${viewMode === '2d' ? ' is-active' : ''}`}
                onClick={() => setViewMode('2d')}
              >
                📸 Editorial Gallery
              </button>
              <button 
                type="button" 
                className={`detail-toggle-btn btn-3d${viewMode === '3d' ? ' is-active' : ''}`}
                onClick={() => setViewMode('3d')}
              >
                🧊 3D Spatial Turntable
              </button>
            </div>

            {viewMode === '2d' ? (
              <>
                <div className="detail-main-image-wrap">
                  <img 
                    src={uniqueImages[activeImage] || product.image} 
                    alt={product.title} 
                    className="detail-main-img" 
                  />
                  {discount > 0 && <span className="detail-discount-chip">-{discount}% OFF</span>}
                  {!isInStock && <span className="detail-soldout-chip">Sold Out</span>}
                </div>
                {uniqueImages.length > 1 && (
                  <div className="detail-thumbnails-row">
                    {uniqueImages.map((img, idx) => (
                      <button
                        key={img + idx}
                        type="button"
                        className={`detail-thumb-btn${activeImage === idx ? ' is-active' : ''}`}
                        onClick={() => setActiveImage(idx)}
                      >
                        <img src={img} alt="thumbnail" />
                      </button>
                    ))}
                  </div>
                )}
              </>
            ) : (
              /* ─── 3D SPATIAL TURNTABLE STAGE ─── */
              <div 
                className="detail-3d-turntable-stage"
                onMouseDown={handleStageMouseDown}
                onMouseMove={handleStageMouseMove}
                onMouseUp={handleStageMouseUp}
                onMouseLeave={handleStageMouseUp}
                onTouchStart={handleStageTouchStart}
                onTouchMove={handleStageTouchMove}
                onTouchEnd={handleStageMouseUp}
              >
                {/* Glowing Ground Disk */}
                <div 
                  className="turntable-platform-disk" 
                  style={{
                    background: lightMode3D === 1 
                      ? 'radial-gradient(ellipse at center, rgba(236,72,153,0.55) 0%, rgba(56,189,248,0.2) 50%, transparent 75%)'
                      : lightMode3D === 2
                      ? 'radial-gradient(ellipse at center, rgba(245,158,11,0.5) 0%, rgba(234,88,12,0.18) 50%, transparent 75%)'
                      : 'radial-gradient(ellipse at center, rgba(59,130,246,0.45) 0%, rgba(236,72,153,0.2) 50%, transparent 75%)',
                    boxShadow: lightMode3D === 1
                      ? '0 0 40px rgba(236,72,153,0.5)'
                      : lightMode3D === 2
                      ? '0 0 35px rgba(245,158,11,0.45)'
                      : '0 0 35px rgba(59,130,246,0.4)'
                  }}
                />

                {/* 3D Rotating Garment Card */}
                <div 
                  className="turntable-garment-card"
                  style={{
                    transform: `rotateY(${stageRotY}deg) rotateX(${stageRotX}deg)`
                  }}
                >
                  <img 
                    src={uniqueImages[activeImage] || product.image} 
                    alt={product.title} 
                  />
                  <div className="card-shine-glare" style={{ opacity: 0.8 }} />
                </div>

                {/* Stage Floating Action Controls */}
                <div className="turntable-controls-bar">
                  <div className="turntable-btn-group">
                    <button
                      type="button"
                      className={`turntable-pill-btn${autoSpin3D ? ' is-active' : ''}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        setAutoSpin3D(!autoSpin3D);
                      }}
                    >
                      {autoSpin3D ? '⏸ Pause' : '🔄 Auto-Spin'}
                    </button>
                    <button
                      type="button"
                      className="turntable-pill-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        setLightMode3D((prev) => (prev + 1) % 3);
                      }}
                    >
                      {lightMode3D === 1 ? '⚡ Cyber Neon' : lightMode3D === 2 ? '🌙 Noir Gold' : '💡 Studio Light'}
                    </button>
                    <button
                      type="button"
                      className="turntable-pill-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        setStageRotX(6);
                        setStageRotY(0);
                      }}
                    >
                      🎯 Center
                    </button>
                  </div>
                  <span className="turntable-orbit-hint">Drag to orbit 360°</span>
                </div>
              </div>
            )}
          </div>

          {/* Right: Info & Actions */}
          <div className="detail-info-column">
            <span className="detail-eyebrow">{product.category || 'CURATED FASHION'}</span>
            <h1 className="detail-title">{product.title}</h1>
            
            {product.rating && (
              <div className="detail-rating-row">
                <span className="rating-pill">★ {product.rating}</span>
                <span className="rating-count-text">
                  {product.ratingCount ? `${Number(product.ratingCount).toLocaleString('en-IN')} verified customer ratings` : 'Highly rated pick'}
                </span>
              </div>
            )}

            <div className="detail-price-box">
              <span className="detail-current-price">{money(product.price)}</span>
              {product.oldPrice && <del className="detail-old-price">{money(product.oldPrice)}</del>}
              {discount > 0 && <span className="detail-save-badge">Save {discount}%</span>}
            </div>
            <p className="detail-shipping-note">✨ Free Express Delivery & 7-Day Hassle-Free Exchange</p>

            {/* Colors */}
            {colors.length > 1 && (
              <div className="detail-option-group">
                <label className="option-label">Available Colors: <strong>{selectedColor}</strong></label>
                <div className="detail-color-pills">
                  {colors.map((c) => (
                    <button
                      key={c}
                      type="button"
                      className={`detail-color-pill${selectedColor === c ? ' is-active' : ''}`}
                      onClick={() => setSelectedColor(c)}
                      style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
                    >
                      <span style={{ display: 'inline-block', width: '9px', height: '9px', borderRadius: '50%', background: getColorHex(c), border: '1px solid rgba(0,0,0,0.15)' }} />
                      <span>{c}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Sizes */}
            <div className="detail-option-group">
              <div className="size-header-row">
                <label className="option-label">Select Size: <strong>{selectedSize}</strong></label>
                <span className="size-guide-text">True to fit</span>
              </div>
              <div className="detail-size-pills">
                {sizes.map((s) => (
                  <button
                    key={s}
                    type="button"
                    className={`detail-size-btn${selectedSize === s ? ' is-active' : ''}`}
                    onClick={() => setSelectedSize(s)}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>

            {/* Order Action Button */}
            <div className="detail-action-strip" style={{ display: 'grid', gridTemplateColumns: onTryOnProduct ? '1fr 1.35fr' : '1fr', gap: '10px' }}>
              {onTryOnProduct && (
                <button 
                  className="button button-light detail-tryon-btn"
                  type="button"
                  style={{ borderRadius: '12px', fontSize: '13px', fontWeight: '750', gap: '6px' }}
                  onClick={() => {
                    onClose();
                    onTryOnProduct(product);
                  }}
                >
                  <span>🪞 Try On Me</span>
                </button>
              )}

              {isInStock ? (
                <button 
                  className="button button-dark detail-order-btn" 
                  type="button"
                  onClick={() => {
                    onClose();
                    onInstantOrder({ ...product, selectedSize, selectedColor });
                  }}
                >
                  <span>Order Now · {money(product.price)}</span>
                  <Icon name="arrowRight" size={16} />
                </button>
              ) : (
                <button 
                  className="button button-light detail-preorder-btn" 
                  type="button"
                  onClick={() => {
                    const msg = encodeURIComponent(`Hi, I would like to pre-order or get notified when "${product.title}" is back in stock!`);
                    const storePhone = import.meta.env.VITE_STORE_WHATSAPP || localStorage.getItem('shelf_store_whatsapp') || '';
                    const cleanStore = storePhone.replace(/\D/g, '');
                    const notifyUrl = cleanStore 
                      ? `https://wa.me/${cleanStore}?text=${msg}` 
                      : `https://api.whatsapp.com/send?text=${msg}`;
                    window.open(notifyUrl, '_blank');
                  }}
                >
                  <span>Notify Me on WhatsApp (Sold Out)</span>
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Related / Similar Looks (Seamless Drill-Down) */}
        {relatedProducts.length > 0 && (
          <div className="detail-related-section">
            <div className="related-heading-row">
              <h3>Similar & Related Edits</h3>
              <span className="related-sub">Tap any look to view details</span>
            </div>
            <div className="related-grid">
              {relatedProducts.map((rel) => (
                <ProductCard 
                  key={rel.id} 
                  product={rel} 
                  isPublic 
                  onViewDetail={(p) => handleSelectRelated(p)}
                  onInstantOrder={(p) => {
                    onClose();
                    onInstantOrder(p);
                  }} 
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
