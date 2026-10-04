import React, { useState, useEffect, useMemo } from 'react';
import Icon from './Icon.jsx';

export default function ShelfProductStage({
  product,
  onAddToCart,
  onToggleWishlist,
  isWishlisted = false,
  onOpenInstantOrder
}) {
  if (!product) return null;

  // Build authentic multi-angle gallery from product's real images
  const gallery = useMemo(() => {
    const rawImages = (Array.isArray(product.galleryImages) && product.galleryImages.length > 0)
      ? product.galleryImages
      : (Array.isArray(product.images) && product.images.length > 0)
        ? product.images
        : [product.image || product.main_image];

    const uniqueImages = [...new Set(rawImages.filter(Boolean))];

    if (uniqueImages.length >= 4) {
      return uniqueImages.slice(0, 5);
    }

    const base = uniqueImages[0] || '/images/meesho-yellow-side-dori-top.webp';
    return [
      base,
      uniqueImages[1] || base,
      uniqueImages[2] || uniqueImages[1] || base,
      uniqueImages[3] || base,
    ];
  }, [product]);

  const [activeAngleIndex, setActiveAngleIndex] = useState(0);
  const [selectedColor, setSelectedColor] = useState('Navy');
  const [selectedSize, setSelectedSize] = useState('M');
  const [activeAccordion, setActiveAccordion] = useState('details');
  const [isDragging, setIsDragging] = useState(false);
  const [startX, setStartX] = useState(0);
  const [showSizeGuide, setShowSizeGuide] = useState(false);
  const [addedAnimation, setAddedAnimation] = useState(false);

  // Available Sizes
  const sizes = ['S', 'M', 'L', 'XL', 'XXL'];

  // Available Colors
  const colors = useMemo(() => {
    if (Array.isArray(product.colors) && product.colors.length > 0) {
      return product.colors.map(c => typeof c === 'string' ? { name: c, hex: getColorHex(c) } : c);
    }
    return [
      { name: 'Navy', hex: '#1e293b' },
      { name: 'Black', hex: '#111111' },
      { name: 'Forest Green', hex: '#2d5a3f' },
      { name: 'Warm Beige', hex: '#d4b996' }
    ];
  }, [product]);

  useEffect(() => {
    setActiveAngleIndex(0);
    setSelectedSize('M');
    if (colors.length > 0) setSelectedColor(colors[0].name);
  }, [product.id, colors]);

  const prevAngle = () => {
    setActiveAngleIndex((prev) => (prev - 1 + gallery.length) % gallery.length);
  };

  const nextAngle = () => {
    setActiveAngleIndex((prev) => (prev + 1) % gallery.length);
  };

  // Horizontal Mouse & Touch 360 Turntable Drag Scrubber
  const handleDragStart = (e) => {
    setIsDragging(true);
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    setStartX(clientX);
  };

  const handleDragMove = (e) => {
    if (!isDragging) return;
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const deltaX = clientX - startX;
    const DRAG_THRESHOLD = 30;

    if (Math.abs(deltaX) > DRAG_THRESHOLD) {
      if (deltaX > 0) {
        prevAngle();
      } else {
        nextAngle();
      }
      setStartX(clientX);
    }
  };

  const handleDragEnd = () => {
    setIsDragging(false);
  };

  const handleCartClick = () => {
    setAddedAnimation(true);
    if (onAddToCart) onAddToCart({ ...product, selectedColor, selectedSize });
    setTimeout(() => setAddedAnimation(false), 1200);
  };

  const displayPrice = Number(product.price || 999);
  const displayOriginalPrice = Number(product.originalPrice || product.original_price || displayPrice * 1.3);

  return (
    <section className="shelf-stage-wrap">
      <div className="shelf-product-grid">
        {/* Left Column: 60% Luxury 3D Gallery Stage */}
        <div className="shelf-gallery-column">
          {/* Main 4/5 Viewport */}
          <div
            className={`shelf-viewport ${isDragging ? 'is-dragging' : ''}`}
            onMouseDown={handleDragStart}
            onMouseMove={handleDragMove}
            onMouseUp={handleDragEnd}
            onMouseLeave={handleDragEnd}
            onTouchStart={handleDragStart}
            onTouchMove={handleDragMove}
            onTouchEnd={handleDragEnd}
          >
            {/* 3D Interactive Badge */}
            <div className="shelf-badge-3d">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z" />
                <path d="m3.3 7 8.7 5 8.7-5" />
                <path d="M12 22V12" />
              </svg>
              <span>3D Interactive Viewer</span>
            </div>

            {/* Left Nav Arrow */}
            <button
              type="button"
              className="shelf-arrow-btn shelf-arrow-left"
              onClick={(e) => { e.stopPropagation(); prevAngle(); }}
              aria-label="Previous angle"
            >
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="m15 18-6-6 6-6" />
              </svg>
            </button>

            {/* Center Product Image */}
            <div className="shelf-image-canvas">
              <img
                src={gallery[activeAngleIndex] || gallery[0]}
                alt={`${product.title || 'Product'} - Angle ${activeAngleIndex + 1}`}
                className="shelf-main-photo"
                draggable={false}
              />
            </div>

            {/* Right Nav Arrow */}
            <button
              type="button"
              className="shelf-arrow-btn shelf-arrow-right"
              onClick={(e) => { e.stopPropagation(); nextAngle(); }}
              aria-label="Next angle"
            >
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="m9 18 6-6-6-6" />
              </svg>
            </button>
          </div>

          {/* 4 Thumbnails Below (80x80) */}
          <div className="shelf-thumbnails-row">
            {gallery.map((imgUrl, idx) => {
              const isActive = idx === activeAngleIndex;
              return (
                <button
                  key={idx}
                  type="button"
                  className={`shelf-thumb-card ${isActive ? 'active' : ''}`}
                  onClick={() => setActiveAngleIndex(idx)}
                >
                  <img src={imgUrl} alt={`Thumbnail ${idx + 1}`} />
                </button>
              );
            })}
          </div>

          {/* 3D Scrubber Hint Pill */}
          <div className="shelf-scrub-hint">
            <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
              <path d="M3 3v5h5" />
              <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" />
              <path d="M16 21h5v-5" />
            </svg>
            <span>Drag to rotate • Scroll to zoom</span>
          </div>
        </div>

        {/* Right Column: 40% Minimal Product Details */}
        <div className="shelf-details-column">
          {/* Title */}
          <h1 className="shelf-product-title">{product.title || 'Classic Embroidered Kurti'}</h1>

          {/* Star Rating & Reviews */}
          <div className="shelf-reviews-row">
            <div className="shelf-stars">
              {'★★★★★'.split('').map((s, i) => (
                <span key={i} className="star-gold">{s}</span>
              ))}
            </div>
            <span className="shelf-rating-val">{product.rating || '4.7'}</span>
            <span className="shelf-review-count">({product.reviewsCount || product.reviews_count || 120} reviews)</span>
          </div>

          {/* Price Block */}
          <div className="shelf-price-block">
            <div className="shelf-price-row">
              <span className="shelf-price-primary">Rs {displayPrice.toLocaleString('en-IN')}</span>
              {displayOriginalPrice > displayPrice && (
                <span className="shelf-price-strike">Rs {Math.round(displayOriginalPrice).toLocaleString('en-IN')}</span>
              )}
            </div>
            <p className="shelf-price-tax-note">Inclusive of all taxes • Free shipping over Rs 1,999</p>
          </div>

          {/* Color Swatches */}
          <div className="shelf-option-group">
            <div className="shelf-option-label-row">
              <span className="shelf-option-label">Color</span>
              <span className="shelf-option-selected-name">{selectedColor}</span>
            </div>
            <div className="shelf-swatches-row">
              {colors.map((c) => {
                const isSelected = selectedColor === c.name;
                return (
                  <button
                    key={c.name}
                    type="button"
                    className={`shelf-color-circle ${isSelected ? 'active' : ''}`}
                    style={{ backgroundColor: c.hex }}
                    onClick={() => setSelectedColor(c.name)}
                    aria-label={c.name}
                    title={c.name}
                  >
                    {isSelected && (
                      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke={c.hex === '#FFFFFF' ? '#111' : '#FFF'} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Size Pills */}
          <div className="shelf-option-group">
            <div className="shelf-option-label-row">
              <span className="shelf-option-label">Size</span>
              <button
                type="button"
                className="shelf-size-guide-link"
                onClick={() => setShowSizeGuide(!showSizeGuide)}
              >
                Size guide
              </button>
            </div>
            <div className="shelf-sizes-row">
              {sizes.map((s) => {
                const isSelected = selectedSize === s;
                return (
                  <button
                    key={s}
                    type="button"
                    className={`shelf-size-pill ${isSelected ? 'active' : ''}`}
                    onClick={() => setSelectedSize(s)}
                  >
                    {s}
                  </button>
                );
              })}
            </div>

            {/* Size Guide Drawer */}
            {showSizeGuide && (
              <div className="shelf-size-guide-box">
                <table>
                  <thead>
                    <tr><th>Size</th><th>Bust (in)</th><th>Waist (in)</th><th>Length (in)</th></tr>
                  </thead>
                  <tbody>
                    <tr><td>S</td><td>36</td><td>32</td><td>44</td></tr>
                    <tr><td>M</td><td>38</td><td>34</td><td>44</td></tr>
                    <tr><td>L</td><td>40</td><td>36</td><td>45</td></tr>
                    <tr><td>XL</td><td>42</td><td>38</td><td>45</td></tr>
                    <tr><td>XXL</td><td>44</td><td>40</td><td>46</td></tr>
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Action CTAs */}
          <div className="shelf-cta-stack">
            {/* Primary Add to Cart */}
            <button
              type="button"
              className={`shelf-btn-add-cart ${addedAnimation ? 'added' : ''}`}
              onClick={handleCartClick}
            >
              {addedAnimation ? (
                <>
                  <svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  <span>Added to Bag</span>
                </>
              ) : (
                <span>Add to Cart</span>
              )}
            </button>

            {/* Secondary Wishlist */}
            <button
              type="button"
              className={`shelf-btn-wishlist ${isWishlisted ? 'wishlisted' : ''}`}
              onClick={() => onToggleWishlist && onToggleWishlist(product.id)}
            >
              <svg viewBox="0 0 24 24" width="16" height="16" fill={isWishlisted ? '#111111' : 'none'} stroke="currentColor" strokeWidth="2">
                <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" />
              </svg>
              <span>{isWishlisted ? 'Wishlisted' : 'Wishlist'}</span>
            </button>

            {/* Instant COD Order Button */}
            {onOpenInstantOrder && (
              <button
                type="button"
                className="shelf-btn-cod"
                onClick={() => onOpenInstantOrder(product)}
              >
                <span>⚡ Instant COD / WhatsApp Order</span>
              </button>
            )}
          </div>

          {/* Trust Badges */}
          <div className="shelf-trust-list">
            <div className="shelf-trust-item">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect width="16" height="13" x="1" y="5" rx="2" />
                <path d="M16 8h4l3 3v5h-7V8z" />
                <circle cx="5.5" cy="18.5" r="2.5" />
                <circle cx="18.5" cy="18.5" r="2.5" />
              </svg>
              <span>Free delivery • 3–5 business days</span>
            </div>
            <div className="shelf-trust-item">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
                <path d="M3 3v5h5" />
              </svg>
              <span>30-day returns & easy exchanges</span>
            </div>
            <div className="shelf-trust-item">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10" />
                <path d="m9 12 2 2 4-4" />
              </svg>
              <span>100% Authentic verified fabrics • Designed in India</span>
            </div>
          </div>

          {/* Accordions */}
          <div className="shelf-accordions">
            <div className="shelf-acc-item">
              <button
                type="button"
                className="shelf-acc-header"
                onClick={() => setActiveAccordion(activeAccordion === 'details' ? '' : 'details')}
              >
                <span>Product Details</span>
                <span className={`shelf-acc-arrow ${activeAccordion === 'details' ? 'open' : ''}`}>∨</span>
              </button>
              {activeAccordion === 'details' && (
                <div className="shelf-acc-body">
                  <p>
                    {product.subtitle || 'Crafted from premium authentic natural fabrics. Tailored for breathable comfort, everyday luxury, and timeless silhouettes.'}
                  </p>
                  <ul>
                    <li>Category: {product.category || 'Women Fashion'}</li>
                    <li>Fit: Regular comfortable relaxed fit</li>
                    <li>Care: Gentle machine wash or hand wash cold</li>
                  </ul>
                </div>
              )}
            </div>

            <div className="shelf-acc-item">
              <button
                type="button"
                className="shelf-acc-header"
                onClick={() => setActiveAccordion(activeAccordion === 'care' ? '' : 'care')}
              >
                <span>Fabric & Care</span>
                <span className={`shelf-acc-arrow ${activeAccordion === 'care' ? 'open' : ''}`}>∨</span>
              </button>
              {activeAccordion === 'care' && (
                <div className="shelf-acc-body">
                  <p>100% Breathable fabric. Hand wash cold or gentle machine wash inside out. Warm iron on reverse. Do not bleach.</p>
                </div>
              )}
            </div>

            <div className="shelf-acc-item">
              <button
                type="button"
                className="shelf-acc-header"
                onClick={() => setActiveAccordion(activeAccordion === 'shipping' ? '' : 'shipping')}
              >
                <span>Shipping & Returns</span>
                <span className={`shelf-acc-arrow ${activeAccordion === 'shipping' ? 'open' : ''}`}>∨</span>
              </button>
              {activeAccordion === 'shipping' && (
                <div className="shelf-acc-body">
                  <p>All orders dispatched within 24 hours. Express doorstep delivery across India. Free reverse pickups for exchange.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function getColorHex(name) {
  const map = {
    'Navy': '#1e293b',
    'Black': '#111111',
    'Forest Green': '#2d5a3f',
    'Warm Beige': '#d4b996',
    'White': '#ffffff',
    'Red': '#dc2626',
    'Yellow': '#eab308',
    'Pink': '#ec4899',
    'Peach': '#fb923c',
    'Wine': '#831843'
  };
  return map[name] || '#334155';
}
