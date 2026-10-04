import React, { useEffect, useMemo, useRef, useState } from 'react';
import Icon from './Icon.jsx';
import StoreBadge from './StoreBadge.jsx';
import { storeSearchUrl } from '../data.js';
import { getProductClickUrl } from '../affiliate.js';

function money(value) {
  return `₹${Number(value || 0).toLocaleString('en-IN')}`;
}

export function getColorHex(colorName = '') {
  const c = String(colorName).toLowerCase().trim();
  const MAP = {
    black: '#18181b',
    white: '#f8fafc',
    peach: '#ffedd5',
    pink: '#f472b6',
    rose: '#fb7185',
    red: '#dc2626',
    maroon: '#881337',
    wine: '#4c0519',
    blue: '#3b82f6',
    navy: '#1e3a8a',
    sky: '#38bdf8',
    green: '#16a34a',
    olive: '#65a30d',
    sage: '#a7f3d0',
    mint: '#6ee7b7',
    yellow: '#eab308',
    mustard: '#ca8a04',
    orange: '#ea580c',
    rust: '#c2410c',
    brown: '#78350f',
    beige: '#f5f5dc',
    cream: '#fef3c7',
    lavender: '#c084fc',
    purple: '#9333ea',
    grey: '#94a3b8',
    gray: '#94a3b8',
    silver: '#cbd5e1',
    gold: '#fbbf24',
    teal: '#0d9488',
  };
  for (const [key, hex] of Object.entries(MAP)) {
    if (c.includes(key)) return hex;
  }
  return '#cbd5e1';
}

export function cleanDisplayTitle(rawTitle) {
  if (!rawTitle) return 'Curated Find';
  let str = String(rawTitle).trim();
  if (str.length <= 36 && !str.includes('|') && !str.includes(';')) return str;
  
  const chunks = str.split(/[|;]+/).map((c) => c.trim()).filter(Boolean);
  let first = chunks[0] || str;
  first = first.replace(/^[A-Z0-9]{3,}\s+(?:Fashion|Creation|Enterprises|Textile|Collection|Brand|Studio)?\s*/i, '');
  first = first.replace(/\b(women's|womens|girls|for women|for girls|premium|exclusive|trending|stylish|designer|latest|heavy|pure|original|casual|formal|professional|western|daily wear|office & party|party wear|for office & party|one piece for women|one piece|combo pack|pack of \d+|\d+\s*gsm)\b/gi, ' ');
  first = first.replace(/\s+/g, ' ').trim().replace(/^[ -_,;.|]+|[ -_,;.|]+$/g, '');
  
  const words = first.split(' ');
  if (words.length > 5 || first.length > 38) {
    first = words.slice(0, 5).join(' ');
  }
  first = first.trim().replace(/^[ -_,;.|]+|[ -_,;.|]+$/g, '');
  
  if (!first || first.length < 3) {
    return str.slice(0, 38).trim() || 'Curated Fashion Find';
  }
  return first.replace(/\bAnd\b/g, '&');
}

export default function ProductCard({ 
  product, 
  isPublic = false, 
  isAdmin = false,
  showStudioControls = false,
  onToggleSaved, 
  onAddLink, 
  onInstantOrder, 
  onViewDetail,
  onOpen3DView,
  onDeleteProduct,
  onTogglePublish,
  onEditProduct
}) {
  const [activeImage, setActiveImage] = useState(0);
  const [galleryPaused, setGalleryPaused] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const touchStartX = useRef(null);
  const imageSlides = useMemo(() => {
    const seen = new Set();
    const gallery = Array.isArray(product.galleryImages) ? product.galleryImages : [];
    const supplied = product.galleryUseAsPrimary && gallery.length ? gallery : [product.image, ...gallery];
    return supplied.filter((image) => {
      const key = String(image || '').trim().split(/[?#]/)[0].toLowerCase();
      if (!key || seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }, [product.image, product.galleryImages, product.galleryUseAsPrimary]);

  useEffect(() => {
    setActiveImage(0);
    setGalleryPaused(false);
  }, [product.id]);

  useEffect(() => {
    if (!isPublic || imageSlides.length < 2 || galleryPaused) return undefined;
    const timer = window.setInterval(() => {
      setActiveImage((current) => (current + 1) % imageSlides.length);
    }, 3500);
    return () => window.clearInterval(timer);
  }, [galleryPaused, imageSlides.length, isPublic]);

  const changeImage = (direction) => {
    if (imageSlides.length < 2) return;
    setActiveImage((current) => (current + direction + imageSlides.length) % imageSlides.length);
  };

  const handleTilt = (event) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width));
    const y = Math.max(0, Math.min(1, (event.clientY - rect.top) / rect.height));

    // Dynamic 3D perspective tilt
    const tiltX = (0.5 - y) * 13;
    const tiltY = (x - 0.5) * 15;
    event.currentTarget.style.setProperty('--tilt-x', `${tiltX.toFixed(1)}deg`);
    event.currentTarget.style.setProperty('--tilt-y', `${tiltY.toFixed(1)}deg`);
    event.currentTarget.style.setProperty('--shine-x', `${(x * 100).toFixed(0)}%`);
    event.currentTarget.style.setProperty('--shine-y', `${(y * 100).toFixed(0)}%`);

    // Multi-angle photo switching on hover if genuine multiple images exist
    if (imageSlides.length > 1) {
      const angleIdx = Math.min(imageSlides.length - 1, Math.floor(x * imageSlides.length));
      if (angleIdx !== activeImage) {
        setActiveImage(angleIdx);
      }
    }
  };

  const resetTilt = (event) => {
    event.currentTarget.style.setProperty('--tilt-x', '0deg');
    event.currentTarget.style.setProperty('--tilt-y', '0deg');
    setGalleryPaused(false);
  };

  const href = getProductClickUrl(product) || storeSearchUrl(product.store, product.title);
  const generatedMeeshoLink = !product.affiliateUrl && product.store === 'Meesho' && Boolean(product.productUrl);
  const ratingCount = Number(product.ratingCount || 0);
  const ratingLabel = ratingCount >= 1000 ? `${(ratingCount / 1000).toFixed(ratingCount >= 10000 ? 0 : 1)}k` : ratingCount;
  const discount = product.oldPrice && product.price
    ? Math.max(1, Math.round((1 - Number(product.price) / Number(product.oldPrice)) * 100))
    : 0;

  const handleTouchStart = (event) => {
    if (imageSlides.length < 2) return;
    touchStartX.current = event.changedTouches?.[0]?.clientX ?? null;
    setGalleryPaused(true);
  };

  const handleTouchEnd = (event) => {
    const endX = event.changedTouches?.[0]?.clientX;
    if (touchStartX.current !== null && Number.isFinite(endX)) {
      const distance = endX - touchStartX.current;
      if (Math.abs(distance) > 36) changeImage(distance > 0 ? -1 : 1);
    }
    touchStartX.current = null;
    setGalleryPaused(false);
  };

  const handleDeleteClick = (e) => {
    e.stopPropagation();
    e.preventDefault();
    if (window.confirm(`Are you sure you want to remove "${product.title.slice(0, 30)}..." from your store?`)) {
      setDeleting(true);
      onDeleteProduct?.(product.id);
    }
  };

  const handleHideClick = (e) => {
    e.stopPropagation();
    e.preventDefault();
    onTogglePublish?.(product);
  };

  const isOwnerAdmin = isAdmin || showStudioControls;

  return (
    <article
      className={`product-card${isPublic ? ' product-card-public' : ''}${isOwnerAdmin ? ' has-admin-controls' : ''}`}
      style={{ opacity: deleting ? 0.3 : 1, transition: 'opacity 0.2s ease' }}
      onMouseMove={handleTilt}
      onMouseLeave={resetTilt}
    >
      <div
        className={`product-image-shell tint-${product.tint || 'sage'}`}
        onMouseEnter={() => { if (isPublic && imageSlides.length > 1) setGalleryPaused(true); }}
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
      >
        {/* ADMIN QUICK ACTION OVERLAY */}
        {isOwnerAdmin && onDeleteProduct && (
          <div 
            className="admin-card-overlay"
            style={{
              position: 'absolute',
              top: '8px',
              left: '8px',
              zIndex: 30,
              display: 'flex',
              gap: '4px',
              background: 'rgba(11, 13, 19, 0.85)',
              backdropFilter: 'blur(10px)',
              padding: '3px 6px',
              borderRadius: '999px',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              boxShadow: '0 4px 12px rgba(0,0,0,0.5)'
            }}
          >
            <button
              type="button"
              onClick={handleDeleteClick}
              title="Remove product from Storefront"
              style={{
                background: 'rgba(239, 68, 68, 0.25)',
                border: '1px solid rgba(239, 68, 68, 0.5)',
                color: '#f87171',
                borderRadius: '50%',
                width: '24px',
                height: '24px',
                display: 'grid',
                placeItems: 'center',
                fontSize: '11px',
                cursor: 'pointer'
              }}
            >
              🗑️
            </button>
            {onTogglePublish && (
              <button
                type="button"
                onClick={handleHideClick}
                title="Hide / Move to Ingest Drafts"
                style={{
                  background: 'rgba(234, 179, 8, 0.25)',
                  border: '1px solid rgba(234, 179, 8, 0.5)',
                  color: '#fde047',
                  borderRadius: '50%',
                  width: '24px',
                  height: '24px',
                  display: 'grid',
                  placeItems: 'center',
                  fontSize: '11px',
                  cursor: 'pointer'
                }}
              >
                👁️
              </button>
            )}
            {onEditProduct && (
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); onEditProduct(product); }}
                title="Edit Product Price / Details"
                style={{
                  background: 'rgba(56, 189, 248, 0.25)',
                  border: '1px solid rgba(56, 189, 248, 0.5)',
                  color: '#38bdf8',
                  borderRadius: '50%',
                  width: '24px',
                  height: '24px',
                  display: 'grid',
                  placeItems: 'center',
                  fontSize: '11px',
                  cursor: 'pointer'
                }}
              >
                ✏️
              </button>
            )}
          </div>
        )}
        <img
          className={`product-photo${(product.galleryUseAsPrimary ? product.galleryImageFit : product.imageFit) === 'contain' ? ' product-photo-contain' : ''}`}
          src={imageSlides[activeImage] || product.image || '/images/meesho-dress-ae6lv9.webp'}
          alt={product.title}
          style={{ objectPosition: product.imagePosition || 'center' }}
          loading="lazy"
          referrerPolicy="no-referrer"
          draggable="false"
          onError={(e) => {
            e.currentTarget.onerror = null;
            const cat = ((product.category || '') + ' ' + (product.title || '')).toLowerCase();
            if (cat.includes('accessor') || cat.includes('pendant') || cat.includes('airpods') || cat.includes('sunglass') || cat.includes('jewel')) {
              e.currentTarget.src = '/images/meesho-earrings-combo.webp';
            } else if (cat.includes('jacket') || cat.includes('bomber') || cat.includes('hoodie') || cat.includes('winter') || cat.includes('cardigan')) {
              e.currentTarget.src = '/images/meesho-black-cardigan.webp';
            } else if (cat.includes('top') || cat.includes('tee') || cat.includes('jersey') || cat.includes('corset') || cat.includes('cami') || cat.includes('sweat')) {
              e.currentTarget.src = '/images/meesho-yellow-side-dori-top.webp';
            } else if (cat.includes('tote') || cat.includes('bag')) {
              e.currentTarget.src = '/images/meesho-canvas-tote.webp';
            } else {
              e.currentTarget.src = '/images/meesho-dress-ae6lv9.webp';
            }
          }}
        />

        {/* 3D Specular Reflection Shine Glare Layer */}
        <div className="card-shine-glare" />

        {/* Multi-Photo Stepper Badge */}
        {imageSlides.length > 1 && (
          <span className="card-angle-stepper" title={`Photo ${activeImage + 1} of ${imageSlides.length}`}>
            {activeImage + 1}/{imageSlides.length}
          </span>
        )}

        {/* 3D Model Trigger Pill (Rendered ONLY if genuine 3D model exists) */}
        {onOpen3DView && (product.modelUrl || product.is3DModel) && (
          <button
            type="button"
            className="card-3d-trigger-pill"
            onClick={(e) => {
              e.stopPropagation();
              e.preventDefault();
              onOpen3DView(product);
            }}
            title="Open 3D Model Viewer"
          >
            <span>🧊 3D View</span>
          </button>
        )}

        {discount > 0 && <span className="discount-chip">-{discount}%</span>}
        {product.festiveBadge && <span className="festive-badge-chip">{product.festiveBadge}</span>}
        {!isPublic && product.isRealListing && <span className="live-listing-chip">VERIFIED</span>}
        <div className="product-image-topline">
          <StoreBadge store={product.store} compact />
          {onToggleSaved && (
            <button
              className={`save-button${product.saved ? ' is-saved' : ''}`}
              type="button"
              aria-label={product.saved ? 'Remove from saved picks' : 'Save this pick'}
              onClick={() => onToggleSaved(product.id)}
            >
              <Icon name="heart" size={16} strokeWidth={product.saved ? 2.2 : 1.8} />
            </button>
          )}
        </div>

        {isPublic && imageSlides.length > 1 && <>
          <button className="product-gallery-arrow product-gallery-prev" type="button" aria-label="Previous product photo" onClick={() => changeImage(-1)}>
            <Icon name="chevronLeft" size={17} />
          </button>
          <button className="product-gallery-arrow product-gallery-next" type="button" aria-label="Next product photo" onClick={() => changeImage(1)}>
            <Icon name="chevronRight" size={17} />
          </button>
          <div className="product-gallery-dots" aria-label={`Photo ${activeImage + 1} of ${imageSlides.length}`}>
            {imageSlides.map((image, index) => <button
              className={`product-gallery-dot${activeImage === index ? ' is-active' : ''}`}
              key={image}
              type="button"
              aria-label={`Show photo ${index + 1}`}
              aria-current={activeImage === index ? 'true' : undefined}
              onClick={() => setActiveImage(index)}
            />)}
          </div>
        </>}

        {isPublic && onViewDetail ? (
          <button
            className="image-open-button"
            type="button"
            onClick={() => onViewDetail(product)}
            aria-label={`View full details for ${product.title}`}
          >
            <Icon name="arrowUpRight" size={17} />
          </button>
        ) : (
          <a
            className="image-open-button"
            href={href}
            target="_blank"
            rel="noreferrer"
            aria-label={`Open ${product.title} at ${product.store}`}
          >
            <Icon name="arrowUpRight" size={17} />
          </a>
        )}
      </div>

      <div className="product-card-body">
        <div className="product-eyebrow-row">
          <span className="product-category">{product.seasonalTag ? 'WINTER EDIT' : product.category}</span>
          {product.colors && Array.isArray(product.colors) && product.colors.length > 1 ? (
            <span className="colorway-badge" title={product.colors.join(', ')} style={{ fontSize: '11px', color: 'var(--muted)', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
              <span className="color-dots-preview" style={{ display: 'inline-flex', gap: '4px', alignItems: 'center' }}>
                {product.colors.slice(0, 4).map((col, idx) => {
                  const matchingVar = Array.isArray(product.variations) 
                    ? product.variations.find(v => (v.colorName || '').toLowerCase().includes(col.toLowerCase()))
                    : null;
                  return (
                    <button
                      key={idx}
                      type="button"
                      className="card-swatch-dot-btn"
                      title={`Switch to ${col}`}
                      style={{
                        display: 'inline-block',
                        width: '9px',
                        height: '9px',
                        borderRadius: '50%',
                        background: getColorHex(col),
                        border: '1.5px solid rgba(255,255,255,0.7)',
                        boxShadow: '0 1px 3px rgba(0,0,0,0.25)',
                        cursor: 'pointer',
                        padding: 0
                      }}
                      onClick={(e) => {
                        e.stopPropagation();
                        e.preventDefault();
                        if (matchingVar?.image) {
                          const sIdx = imageSlides.indexOf(matchingVar.image);
                          if (sIdx !== -1) setActiveImage(sIdx);
                          else {
                            imageSlides.unshift(matchingVar.image);
                            setActiveImage(0);
                          }
                        }
                      }}
                    />
                  );
                })}
              </span>
              <span>{product.colors.length} shades</span>
            </span>
          ) : product.rating ? (
            <span className="rating-chip"><b>★</b> {product.rating}{ratingCount ? ` · ${ratingLabel}` : ''}</span>
          ) : !isPublic && product.collectionTitle ? (
            <span className="product-collection-label">{product.collectionTitle}</span>
          ) : null}
        </div>
        <h3 className="product-title" title={product.title}>
          {isPublic && onViewDetail ? (
            <button type="button" className="product-title-btn" onClick={() => onViewDetail(product)}>
              {cleanDisplayTitle(product.title)}
            </button>
          ) : (
            <a className="product-title-link" href={href} target="_blank" rel="noreferrer">
              {cleanDisplayTitle(product.title)}
            </a>
          )}
        </h3>
        <p className="product-subtitle">{product.subtitle || product.brand || 'A little find worth sharing'}</p>
        <div className="product-price-row">
          <div className="product-prices">
            <strong>{product.pricePrefix ? `${product.pricePrefix} ` : ''}{money(product.price)}</strong>
            {product.oldPrice && <del>{money(product.oldPrice)}</del>}
          </div>
          {!isPublic && <span className="commission-hint">{product.affiliateUrl ? 'Verify tracking' : generatedMeeshoLink ? 'Generated · verify' : product.isRealListing ? 'Add tracking' : (product.commission || 'Add affiliate link')}</span>}
        </div>
        {isPublic ? (
          <button 
            className="shop-pick-link shop-pick-order-btn" 
            type="button" 
            onClick={() => onInstantOrder ? onInstantOrder(product) : window.open(href, '_blank')}
          >
            <span>Order Now</span>
            <Icon name="arrowUpRight" size={14} />
          </button>
        ) : (
          <div className="product-card-footer">
            <span className="clicks-count"><Icon name="eye" size={14} /> {Number(product.clicks || 0).toLocaleString('en-IN')} views</span>
            <button className={`affiliate-link-action${product.affiliateUrl ? ' has-link' : ''}`} type="button" onClick={() => onAddLink?.(product)}>
              {product.affiliateUrl ? <><Icon name="check" size={14} /> URL saved</> : <><Icon name="link" size={14} /> {generatedMeeshoLink ? 'Set creator URL' : product.isRealListing ? 'Add tracking' : 'Add link'}</>}
            </button>
          </div>
        )}
      </div>
    </article>
  );
}
