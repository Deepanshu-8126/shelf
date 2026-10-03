import React, { useEffect, useMemo, useRef, useState } from 'react';
import Icon from './Icon.jsx';
import StoreBadge from './StoreBadge.jsx';
import { storeSearchUrl } from '../data.js';
import { getProductClickUrl } from '../affiliate.js';

function money(value) {
  return `₹${Number(value || 0).toLocaleString('en-IN')}`;
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
  
  return first ? first.replace(/\bAnd\b/g, '&') : str.slice(0, 36);
}

export default function ProductCard({ product, isPublic = false, onToggleSaved, onAddLink, onInstantOrder, onViewDetail }) {
  const [activeImage, setActiveImage] = useState(0);
  const [galleryPaused, setGalleryPaused] = useState(false);
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
    }, 3000);
    return () => window.clearInterval(timer);
  }, [galleryPaused, imageSlides.length, isPublic]);

  const changeImage = (direction) => {
    if (imageSlides.length < 2) return;
    setActiveImage((current) => (current + direction + imageSlides.length) % imageSlides.length);
  };

  const handleTilt = (event) => {
    if (isPublic) return;
    const rect = event.currentTarget.getBoundingClientRect();
    const x = (event.clientX - rect.left) / rect.width;
    const y = (event.clientY - rect.top) / rect.height;
    event.currentTarget.style.setProperty('--tilt-x', `${(0.5 - y) * 4}deg`);
    event.currentTarget.style.setProperty('--tilt-y', `${(x - 0.5) * 5}deg`);
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

  return (
    <article
      className={`product-card${isPublic ? ' product-card-public' : ''}`}
      onMouseMove={handleTilt}
      onMouseLeave={resetTilt}
    >
      <div
        className={`product-image-shell tint-${product.tint || 'sage'}`}
        onMouseEnter={() => { if (isPublic && imageSlides.length > 1) setGalleryPaused(true); }}
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
      >
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
        {discount > 0 && <span className="discount-chip">-{discount}%</span>}
        {product.festiveBadge && <span className="festive-badge-chip">{product.festiveBadge}</span>}
        {product.isRealListing && <span className="live-listing-chip">LIVE LISTING</span>}
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
            <span className="colorway-badge" title={product.colors.join(', ')} style={{ fontSize: '9px', color: 'var(--muted)', fontWeight: 650, display: 'inline-flex', alignItems: 'center', gap: '3px' }}>
              <span style={{ display: 'inline-block', width: '6px', height: '6px', borderRadius: '50%', background: 'var(--primary)' }} />
              {product.colors.length} shades
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
