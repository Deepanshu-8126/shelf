import React, { useState, useEffect, useMemo } from 'react';
import Icon from './Icon.jsx';
import ShelfHeader from './ShelfHeader.jsx';
import ShelfProductStage from './ShelfProductStage.jsx';
import InstantOrderModal from './InstantOrderModal.jsx';

export default function ProductPage({
  productId,
  allProducts = [],
  onBack,
  onSelectProduct,
  savedIds = [],
  onToggleSaved
}) {
  const [orderModalProduct, setOrderModalProduct] = useState(null);
  const [cartCount, setCartCount] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('shelf_cart_count') || '0');
    } catch {
      return 0;
    }
  });

  const product = useMemo(() => {
    if (!productId) return null;
    return allProducts.find((p) => String(p.id) === String(productId)) || null;
  }, [allProducts, productId]);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [productId]);

  // Strict category matching for related pieces
  const relatedProducts = useMemo(() => {
    if (!product) return [];
    const targetCat = (product.category || '').trim().toLowerCase();
    return allProducts
      .filter((p) => {
        if (p.id === product.id) return false;
        const pCat = (p.category || '').trim().toLowerCase();
        return targetCat && pCat === targetCat;
      })
      .slice(0, 4);
  }, [allProducts, product]);

  if (!product) {
    return (
      <div className="shelf-clean-storefront">
        <ShelfHeader
          wishlistCount={savedIds.length}
          cartCount={cartCount}
          onOpenWishlist={onBack}
        />
        <div style={{
          minHeight: '60vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          textAlign: 'center',
          padding: '60px 24px'
        }}>
          <h2 style={{ fontSize: '22px', fontWeight: 600, color: 'var(--shelf-text-primary)', marginBottom: '8px' }}>
            Listing Not Found
          </h2>
          <p style={{ color: 'var(--shelf-text-secondary)', fontSize: '14px', maxWidth: '400px', lineHeight: 1.5, marginBottom: '24px' }}>
            The requested piece is either unavailable or has been archived from the active catalog.
          </p>
          <button
            type="button"
            className="shelf-btn-primary"
            style={{ width: 'auto', padding: '0 24px', height: '42px' }}
            onClick={onBack}
          >
            ← Return to Storefront
          </button>
        </div>
      </div>
    );
  }

  const isWishlisted = savedIds.includes(product.id);

  return (
    <div className="shelf-clean-storefront">
      {/* 1. Clean Editorial Header (shelf.) */}
      <ShelfHeader
        activeCategory={product.category || 'All Picks'}
        onSelectCategory={() => onBack && onBack()}
        wishlistCount={savedIds.length}
        cartCount={cartCount}
        onOpenWishlist={onBack}
      />

      {/* 2. Luxury 2-Column Product Detail Stage (60% Media / 40% Information) */}
      <ShelfProductStage
        product={product}
        onAddToCart={() => {
          setCartCount((prev) => {
            const next = prev + 1;
            try { localStorage.setItem('shelf_cart_count', next); } catch {}
            return next;
          });
        }}
        onToggleWishlist={(id) => onToggleSaved && onToggleSaved(id)}
        isWishlisted={isWishlisted}
        onOpenInstantOrder={(prod) => setOrderModalProduct(prod)}
      />

      {/* 3. Related Pieces from the same verified category */}
      {relatedProducts.length > 0 && (
        <section className="shelf-collection-section">
          <div className="shelf-collection-heading">
            <h2>More from {product.category || 'this collection'}</h2>
            <span className="shelf-collection-count">{relatedProducts.length} pieces</span>
          </div>

          <div className="shelf-cards-grid">
            {relatedProducts.map((rel) => {
              const hasRealPrice = rel.price != null && !isNaN(Number(rel.price));
              const hasRealOldPrice = rel.originalPrice != null && !isNaN(Number(rel.originalPrice)) && Number(rel.originalPrice) > Number(rel.price);

              return (
                <article
                  key={rel.id}
                  className="shelf-item-card"
                  onClick={() => {
                    if (onSelectProduct) {
                      onSelectProduct(rel.id);
                    }
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                  }}
                >
                  <div className="shelf-item-img-box">
                    <img src={rel.image || rel.main_image} alt={rel.title || 'Product'} loading="lazy" />
                  </div>
                  <div className="shelf-item-info">
                    <h3 className="shelf-item-title">{rel.title || 'Untitled Listing'}</h3>
                    <div className="shelf-item-price-row">
                      {hasRealPrice ? (
                        <span className="shelf-item-price">₹{Number(rel.price).toLocaleString('en-IN')}</span>
                      ) : (
                        <span className="shelf-item-price">View price</span>
                      )}
                      {hasRealOldPrice && (
                        <span className="shelf-item-mrp">₹{Math.round(Number(rel.originalPrice)).toLocaleString('en-IN')}</span>
                      )}
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        </section>
      )}

      {/* Instant Order Modal */}
      {orderModalProduct && (
        <InstantOrderModal
          product={orderModalProduct}
          onClose={() => setOrderModalProduct(null)}
        />
      )}
    </div>
  );
}
