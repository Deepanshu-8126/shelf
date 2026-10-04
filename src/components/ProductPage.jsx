import React, { useState, useEffect, useMemo } from 'react';
import Icon from './Icon.jsx';
import ProductCard, { getColorHex } from './ProductCard.jsx';
import InstantOrderModal from './InstantOrderModal.jsx';

function money(value) {
  return `₹${Number(value || 0).toLocaleString('en-IN')}`;
}

export default function ProductPage({ 
  productId, 
  allProducts = [], 
  onBack, 
  onSelectProduct,
  savedIds = [],
  onToggleSaved
}) {
  const product = useMemo(() => {
    if (!productId) return null;
    return allProducts.find((p) => String(p.id) === String(productId)) || null;
  }, [allProducts, productId]);

  const [activeImage, setActiveImage] = useState(0);
  const [selectedColor, setSelectedColor] = useState('Standard');
  const [selectedSize, setSelectedSize] = useState('M');
  const [pincode, setPincode] = useState('');
  const [orderModalOpen, setOrderModalOpen] = useState(false);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    setActiveImage(0);
    setSelectedSize('M');
    if (product && Array.isArray(product.colors) && product.colors.length) {
      setSelectedColor(product.colors[0]);
    }
  }, [productId, product]);

  if (!product) {
    return (
      <div className="product-page-empty" style={{ minHeight: '80vh', display: 'flex', flexDirection: 'column' }}>
        <header className="product-page-header" style={{ borderBottom: '1px solid var(--line)' }}>
          <button className="page-back-button" type="button" onClick={onBack} aria-label="Go back">
            <Icon name="arrowLeft" size={16} />
            <span>Back to storefront</span>
          </button>
          <div className="product-page-brand">
            <span className="brand-mark"><i /><i /><i /></span>
            <span>shelf<span className="brand-period">.</span></span>
          </div>
        </header>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', padding: '60px 24px' }}>
          <span style={{ fontSize: '42px', marginBottom: '16px' }}>🏷️</span>
          <h2 style={{ fontSize: '22px', fontWeight: 800, marginBottom: '8px', color: 'var(--ink)' }}>Piece Unavailable or Sold Out</h2>
          <p style={{ color: 'var(--muted)', fontSize: '13.5px', maxWidth: '420px', lineHeight: 1.5, marginBottom: '24px' }}>
            The item requested via this link is no longer available in the active collection. Explore current trending drops below.
          </p>
          <button className="button button-dark" type="button" onClick={onBack} style={{ padding: '0 24px', height: '42px', fontSize: '13px', fontWeight: 700 }}>
            Browse Active Collection ↗
          </button>
        </div>
      </div>
    );
  }

  // Real-time Indian Pincode Validator (1-9 followed by 5 digits)
  const pincodeStatus = useMemo(() => {
    const clean = pincode.trim();
    if (clean.length === 6) {
      if (/^[1-9][0-9]{5}$/.test(clean)) {
        return { valid: true, message: '✓ Cash on Delivery Available · Express Delivery (3-4 Days)' };
      }
      return { valid: false, message: 'Invalid Indian Pincode (must not start with 0)' };
    }
    if (clean.length > 0 && clean.length < 6) {
      return { valid: false, message: 'Enter full 6-digit delivery pincode' };
    }
    return null;
  }, [pincode]);

  const gallery = Array.isArray(product.galleryImages) && product.galleryImages.length 
    ? product.galleryImages 
    : (Array.isArray(product.gallery) && product.gallery.length ? product.gallery : [product.image]);

  const uniqueImages = [...new Set([product.image, ...gallery])].filter(Boolean);
  const colors = Array.isArray(product.colors) && product.colors.length ? product.colors : ['Classic'];
  const sizes = Array.isArray(product.sizes) && product.sizes.length ? product.sizes : ['S', 'M', 'L', 'XL', 'XXL'];
  const discount = product.oldPrice && product.price
    ? Math.max(1, Math.round((1 - Number(product.price) / Number(product.oldPrice)) * 100))
    : 0;

  // Strict category matching for related products
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

  const isSaved = savedIds.includes(product.id);

  return (
    <div className="dedicated-product-page">
      {/* Product Page Navigation Header */}
      <header className="product-page-header">
        <button className="page-back-button" type="button" onClick={onBack} aria-label="Go back">
          <Icon name="arrowLeft" size={16} />
          <span>Back to collection</span>
        </button>

        <div className="product-page-brand">
          <span className="brand-mark"><i /><i /><i /></span>
          <span>shelf<span className="brand-period">.</span></span>
        </div>

        <button 
          className={`page-wishlist-button${isSaved ? ' is-saved' : ''}`}
          type="button" 
          onClick={() => onToggleSaved?.(product.id)}
          aria-label="Save this item"
        >
          <Icon name="heart" size={16} strokeWidth={isSaved ? 2.2 : 1.8} />
          <span>{isSaved ? 'Saved' : 'Save'}</span>
        </button>
      </header>

      {/* Main Product Showcase Layout */}
      <main className="product-page-main">
        <div className="product-page-container">
          <div className="product-showcase-grid">
            {/* Left: Interactive Media Gallery */}
            <div className="showcase-gallery-col">
              <div className="showcase-main-wrap">
                <img 
                  src={uniqueImages[activeImage] || product.image} 
                  alt={product.title} 
                  className="showcase-main-photo" 
                />
                {discount > 0 && <span className="showcase-badge-discount">-{discount}% OFF</span>}
                <span className="showcase-badge-verified">Verified Quality</span>
              </div>
              
              {uniqueImages.length > 1 && (
                <div className="showcase-thumbnails-strip">
                  {uniqueImages.map((img, idx) => (
                    <button
                      key={img + idx}
                      type="button"
                      className={`showcase-thumb-box${activeImage === idx ? ' is-active' : ''}`}
                      onClick={() => setActiveImage(idx)}
                    >
                      <img src={img} alt={`View angle ${idx + 1}`} />
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Right: Curated Product Details & Purchase Action */}
            <div className="showcase-info-col">
              <div className="showcase-breadcrumbs">
                <span>Women</span>
                <span className="crumb-sep">/</span>
                <span>{product.category || 'Dresses'}</span>
                <span className="crumb-sep">/</span>
                <span className="crumb-current">{product.title}</span>
              </div>

              <h1 className="showcase-title">{product.title}</h1>
              <p className="showcase-subtitle">{product.subtitle || 'Handpicked luxury trend edit'}</p>

              {product.rating && (
                <div className="showcase-rating-row">
                  <span className="showcase-star-pill">★ {product.rating}</span>
                  <span className="showcase-rating-count">
                    {product.ratingCount ? `${Number(product.ratingCount).toLocaleString('en-IN')} verified reviews` : 'Top-rated favorite'}
                  </span>
                  <span className="showcase-trust-dot">·</span>
                  <span className="showcase-dispatch-tag">Express 3-Day Dispatch</span>
                </div>
              )}

              <div className="showcase-price-card">
                <div className="price-main-block">
                  <span className="showcase-selling-price">{money(product.price)}</span>
                  {product.oldPrice && <del className="showcase-mrp-price">{money(product.oldPrice)}</del>}
                  {discount > 0 && <span className="showcase-save-pill">Save {discount}%</span>}
                </div>
                <span className="showcase-tax-note">Inclusive of all taxes & doorstep delivery</span>
              </div>

              {/* Color Selection */}
              {colors.length > 1 && (
                <div className="showcase-option-block">
                  <label className="showcase-option-label">Color: <strong>{selectedColor}</strong></label>
                  <div className="showcase-pills-row">
                    {colors.map((c) => (
                      <button
                        key={c}
                        type="button"
                        className={`showcase-pill-opt${selectedColor === c ? ' is-active' : ''}`}
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

              {/* Size Selection */}
              <div className="showcase-option-block">
                <div className="showcase-size-topline">
                  <label className="showcase-option-label">Size: <strong>{selectedSize}</strong></label>
                  <span className="showcase-fit-note">True to Indian Size</span>
                </div>
                <div className="showcase-pills-row">
                  {sizes.map((s) => (
                    <button
                      key={s}
                      type="button"
                      className={`showcase-size-pill${selectedSize === s ? ' is-active' : ''}`}
                      onClick={() => setSelectedSize(s)}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>

              {/* Live Delivery Pincode Check */}
              <div className="showcase-pincode-card">
                <div className="pincode-header">
                  <Icon name="check" size={14} />
                  <span>Check Express Delivery & Cash on Delivery (COD)</span>
                </div>
                <div className="pincode-input-row">
                  <input 
                    type="text" 
                    maxLength={6}
                    placeholder="Enter 6-digit Pincode (e.g. 110001)"
                    value={pincode}
                    onChange={(e) => setPincode(e.target.value.replace(/\D/g, ''))}
                  />
                </div>
                {pincodeStatus && (
                  <span className={`pincode-feedback ${pincodeStatus.valid ? 'is-valid' : 'is-pending'}`}>
                    {pincodeStatus.message}
                  </span>
                )}
              </div>

              {/* Trust Badges */}
              <div className="showcase-perks-strip">
                <div className="perk-item">
                  <span className="perk-icon">✦</span>
                  <div>
                    <strong>Free Express Delivery</strong>
                    <small>Direct to your doorstep in 3-4 days</small>
                  </div>
                </div>
                <div className="perk-item">
                  <span className="perk-icon">✦</span>
                  <div>
                    <strong>7-Day Easy Exchange</strong>
                    <small>Hassle-free size replacement guarantee</small>
                  </div>
                </div>
                <div className="perk-item">
                  <span className="perk-icon">✦</span>
                  <div>
                    <strong>Pay on Delivery (COD)</strong>
                    <small>Cash or UPI upon receiving the parcel</small>
                  </div>
                </div>
              </div>

              {/* Primary Action Button */}
              <div className="showcase-action-bar">
                <button 
                  className="button button-dark showcase-buy-btn" 
                  type="button"
                  onClick={() => setOrderModalOpen(true)}
                >
                  <span>Order Now · {money(product.price)}</span>
                  <Icon name="arrowRight" size={17} />
                </button>
              </div>
            </div>
          </div>

          {/* Similar & Related Looks Section */}
          {relatedProducts.length > 0 && (
            <section className="showcase-related-section">
              <div className="section-heading-row">
                <div>
                  <p className="eyebrow">COMPLETE YOUR LOOK</p>
                  <h2>Similar & Related Edits</h2>
                </div>
                <button 
                  className="text-button" 
                  type="button" 
                  onClick={onBack}
                >
                  Browse all {product.category || 'picks'} <Icon name="arrowRight" size={16} />
                </button>
              </div>

              <div className="product-grid public-product-grid">
                {relatedProducts.map((rel) => (
                  <ProductCard 
                    key={rel.id} 
                    product={{ ...rel, saved: savedIds.includes(rel.id) }} 
                    isPublic 
                    onToggleSaved={onToggleSaved}
                    onViewDetail={(p) => onSelectProduct(p.id)}
                    onInstantOrder={() => {
                      onSelectProduct(rel.id);
                      setOrderModalOpen(true);
                    }} 
                  />
                ))}
              </div>
            </section>
          )}
        </div>
      </main>

      {/* Checkout Modal */}
      {orderModalOpen && (
        <InstantOrderModal 
          product={{ ...product, selectedSize, selectedColor }} 
          onClose={() => setOrderModalOpen(false)} 
        />
      )}
    </div>
  );
}
