import React, { useState, useEffect, useMemo } from 'react';
import Icon from '../ui/Icon.jsx';
import { getProductClickUrl } from '../../affiliate.js';

export default function ShelfProductStage({
  product,
  onToggleWishlist,
  isWishlisted = false,
  onOpenInstantOrder
}) {
  if (!product) return null;

  // 1. Strict Gallery Deduplication — Zero artificial padding
  const uniqueImages = useMemo(() => {
    const list = [
      product.image,
      product.main_image,
      ...(Array.isArray(product.galleryImages) ? product.galleryImages : []),
      ...(Array.isArray(product.images) ? product.images : []),
      ...(Array.isArray(product.gallery) ? product.gallery : [])
    ].filter(Boolean);

    // Filter out invalid/empty strings and deduplicate
    return [...new Set(list.map((u) => String(u).trim()).filter((u) => u.length > 0))];
  }, [product]);

  const [activeImageIndex, setActiveImageIndex] = useState(0);
  const [selectedColor, setSelectedColor] = useState(() => {
    return Array.isArray(product.colors) && product.colors.length > 0 ? product.colors[0] : null;
  });
  const [selectedSize, setSelectedSize] = useState(() => {
    return Array.isArray(product.sizes) && product.sizes.length > 0 ? product.sizes[0] : null;
  });
  const [activeAccordion, setActiveAccordion] = useState('details');

  // Reset state on product change
  useEffect(() => {
    setActiveImageIndex(0);
    setSelectedColor(Array.isArray(product.colors) && product.colors.length > 0 ? product.colors[0] : null);
    setSelectedSize(Array.isArray(product.sizes) && product.sizes.length > 0 ? product.sizes[0] : null);
  }, [product.id, product.colors, product.sizes]);

  const hasMultipleImages = uniqueImages.length > 1;
  const currentImage = uniqueImages[activeImageIndex] || uniqueImages[0] || null;

  const prevImage = () => {
    if (!hasMultipleImages) return;
    setActiveImageIndex((prev) => (prev - 1 + uniqueImages.length) % uniqueImages.length);
  };

  const nextImage = () => {
    if (!hasMultipleImages) return;
    setActiveImageIndex((prev) => (prev + 1) % uniqueImages.length);
  };

  // Keyboard navigation for gallery accessibility
  const handleKeyDown = (e) => {
    if (e.key === 'ArrowLeft') prevImage();
    if (e.key === 'ArrowRight') nextImage();
  };

  // Real Pricing (Zero Manufactured Multipliers)
  const realPrice = product.price != null && !isNaN(Number(product.price)) ? Number(product.price) : null;
  const realOldPrice = (product.oldPrice != null && !isNaN(Number(product.oldPrice)))
    ? Number(product.oldPrice)
    : (product.originalPrice != null && !isNaN(Number(product.originalPrice)))
      ? Number(product.originalPrice)
      : null;

  const hasDiscount = realPrice != null && realOldPrice != null && realOldPrice > realPrice;
  const discountPercent = hasDiscount
    ? Math.round(((realOldPrice - realPrice) / realOldPrice) * 100)
    : null;

  // Real Ratings (Zero manufactured rating values)
  const realRating = product.rating != null && !isNaN(Number(product.rating)) ? Number(product.rating) : null;
  const realReviewCount = product.ratingCount != null && !isNaN(Number(product.ratingCount))
    ? Number(product.ratingCount)
    : (product.reviewsCount != null && !isNaN(Number(product.reviewsCount)))
      ? Number(product.reviewsCount)
      : null;

  // Real Variants
  const realColors = Array.isArray(product.colors) && product.colors.length > 0 ? product.colors : null;
  const realSizes = Array.isArray(product.sizes) && product.sizes.length > 0 ? product.sizes : null;

  // Real Marketplace Affiliate URL
  const marketplaceUrl = getProductClickUrl(product);
  const storeName = product.store || 'Marketplace';

  return (
    <section className="shelf-stage-wrap" onKeyDown={handleKeyDown} tabIndex={0} aria-label="Product details view">
      <div className="shelf-product-grid">
        {/* Left Column: Media Gallery (approx 60% on desktop) */}
        <div className="shelf-gallery-column">
          <div className="shelf-viewport" role="region" aria-label="Product image gallery">
            {/* Honest Label: Gallery count or Photo */}
            <div className="shelf-badge-gallery">
              <Icon name="collections" size={13} />
              <span>{hasMultipleImages ? `Photo ${activeImageIndex + 1} of ${uniqueImages.length}` : 'Listing Photo'}</span>
            </div>

            {/* Previous Arrow Button (Only if multiple distinct images) */}
            {hasMultipleImages && (
              <button
                type="button"
                className="shelf-arrow-btn shelf-arrow-left"
                onClick={prevImage}
                aria-label="Previous photo"
              >
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="m15 18-6-6 6-6" />
                </svg>
              </button>
            )}

            {/* Main Photo Canvas */}
            <div className="shelf-image-canvas">
              {currentImage ? (
                <img
                  src={currentImage}
                  alt={`${product.title || 'Product photo'} - view ${activeImageIndex + 1}`}
                  className="shelf-main-photo"
                  loading="eager"
                />
              ) : (
                <div className="shelf-photo-empty">
                  <span>Photo not provided</span>
                </div>
              )}
            </div>

            {/* Next Arrow Button (Only if multiple distinct images) */}
            {hasMultipleImages && (
              <button
                type="button"
                className="shelf-arrow-btn shelf-arrow-right"
                onClick={nextImage}
                aria-label="Next photo"
              >
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="m9 18 6-6-6-6" />
                </svg>
              </button>
            )}
          </div>

          {/* Thumbnails Row: ONLY distinct images rendered (1 thumb for 1 photo, 2 for 2, never padded) */}
          {uniqueImages.length > 0 && (
            <div className="shelf-thumbnails-row" role="tablist" aria-label="Gallery thumbnails">
              {uniqueImages.map((imgUrl, idx) => {
                const isActive = idx === activeImageIndex;
                return (
                  <button
                    key={`${imgUrl}-${idx}`}
                    type="button"
                    role="tab"
                    aria-selected={isActive}
                    aria-label={`Show photo ${idx + 1}`}
                    className={`shelf-thumb-card ${isActive ? 'active' : ''}`}
                    onClick={() => setActiveImageIndex(idx)}
                  >
                    <img src={imgUrl} alt={`Thumbnail ${idx + 1}`} loading="lazy" />
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column: Verified Product Information (approx 40% on desktop) */}
        <div className="shelf-details-column">
          {/* Store / Category Breadcrumb */}
          <div className="shelf-meta-breadcrumbs">
            <span>{storeName}</span>
            {product.category && (
              <>
                <span className="shelf-meta-sep">/</span>
                <span>{product.category}</span>
              </>
            )}
          </div>

          {/* Real Product Title */}
          <h1 className="shelf-product-title">{product.title || 'Untitled Listing'}</h1>

          {/* Subtitle / Description note if present */}
          {product.subtitle && (
            <p className="shelf-product-subtitle">{product.subtitle}</p>
          )}

          {/* Real Ratings (Only rendered if sourced in catalog) */}
          {realRating != null && (
            <div className="shelf-reviews-row">
              <span className="shelf-rating-badge">★ {realRating.toFixed(1)}</span>
              {realReviewCount != null && (
                <span className="shelf-review-count">({realReviewCount.toLocaleString('en-IN')} ratings)</span>
              )}
            </div>
          )}

          {/* Real Pricing Block */}
          <div className="shelf-price-block">
            {realPrice != null ? (
              <div className="shelf-price-row">
                <span className="shelf-price-primary">₹{realPrice.toLocaleString('en-IN')}</span>
                {hasDiscount && (
                  <>
                    <del className="shelf-price-strike">₹{realOldPrice.toLocaleString('en-IN')}</del>
                    {discountPercent != null && (
                      <span className="shelf-discount-pill">{discountPercent}% OFF</span>
                    )}
                  </>
                )}
              </div>
            ) : (
              <div className="shelf-price-row">
                <span className="shelf-price-primary">Price on {storeName}</span>
              </div>
            )}
            <p className="shelf-price-note">Verified listing on {storeName}</p>
          </div>

          {/* Real Color Variants (Rendered ONLY if data provides colors) */}
          {realColors && (
            <div className="shelf-option-group">
              <div className="shelf-option-label-row">
                <span className="shelf-option-label">Color</span>
                {selectedColor && <span className="shelf-option-selected-name">{selectedColor}</span>}
              </div>
              <div className="shelf-variants-pill-row">
                {realColors.map((colorName) => {
                  const isSelected = selectedColor === colorName;
                  return (
                    <button
                      key={colorName}
                      type="button"
                      className={`shelf-variant-pill ${isSelected ? 'active' : ''}`}
                      onClick={() => setSelectedColor(colorName)}
                    >
                      {colorName}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Real Size Variants (Rendered ONLY if data provides sizes) */}
          {realSizes && (
            <div className="shelf-option-group">
              <div className="shelf-option-label-row">
                <span className="shelf-option-label">Available Sizes</span>
                {selectedSize && <span className="shelf-option-selected-name">{selectedSize}</span>}
              </div>
              <div className="shelf-sizes-row">
                {realSizes.map((sizeName) => {
                  const isSelected = selectedSize === sizeName;
                  return (
                    <button
                      key={sizeName}
                      type="button"
                      className={`shelf-size-pill ${isSelected ? 'active' : ''}`}
                      onClick={() => setSelectedSize(sizeName)}
                    >
                      {sizeName}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Primary Action Buttons */}
          <div className="shelf-cta-stack">
            {/* Marketplace Direct Link */}
            {marketplaceUrl ? (
              <a
                href={marketplaceUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="shelf-btn-primary"
              >
                <span>Shop this listing on {storeName}</span>
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M7 17 17 7" />
                  <path d="M7 7h10v10" />
                </svg>
              </a>
            ) : (
              <button type="button" className="shelf-btn-primary" disabled>
                <span>Listing URL not available</span>
              </button>
            )}

            {/* Wishlist Button */}
            <button
              type="button"
              className={`shelf-btn-wishlist ${isWishlisted ? 'wishlisted' : ''}`}
              onClick={() => onToggleWishlist && onToggleWishlist(product.id)}
              aria-label={isWishlisted ? 'Remove from wishlist' : 'Save to wishlist'}
            >
              <Icon name="heart" size={16} strokeWidth={isWishlisted ? 2.5 : 1.8} />
              <span>{isWishlisted ? 'Saved in Wishlist' : 'Add to Wishlist'}</span>
            </button>

            {/* Direct Order Modal (Only if project owns checkout callback) */}
            {onOpenInstantOrder && (
              <button
                type="button"
                className="shelf-btn-secondary"
                onClick={() => onOpenInstantOrder(product)}
              >
                <Icon name="check" size={15} />
                <span>Quick WhatsApp / COD Order</span>
              </button>
            )}
          </div>

          {/* Sourced Details Accordion */}
          <div className="shelf-accordions">
            <div className="shelf-acc-item">
              <button
                type="button"
                className="shelf-acc-header"
                onClick={() => setActiveAccordion(activeAccordion === 'details' ? '' : 'details')}
                aria-expanded={activeAccordion === 'details'}
              >
                <span>Listing Details</span>
                <span className={`shelf-acc-arrow ${activeAccordion === 'details' ? 'open' : ''}`}>∨</span>
              </button>
              {activeAccordion === 'details' && (
                <div className="shelf-acc-body">
                  <dl className="shelf-details-list">
                    <div>
                      <dt>Store / Origin:</dt>
                      <dd>{storeName}</dd>
                    </div>
                    {product.category && (
                      <div>
                        <dt>Category:</dt>
                        <dd>{product.category}</dd>
                      </div>
                    )}
                    {product.id && (
                      <div>
                        <dt>Listing ID:</dt>
                        <dd>{String(product.id)}</dd>
                      </div>
                    )}
                    {product.inStock != null && (
                      <div>
                        <dt>Availability:</dt>
                        <dd>{product.inStock ? 'In stock' : 'Check marketplace'}</dd>
                      </div>
                    )}
                  </dl>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
