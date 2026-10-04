import React, { useEffect } from 'react';
import ShelfProductStage from './ShelfProductStage.jsx';

export default function ProductDetailModal({
  product,
  onClose,
  onInstantOrder,
  onToggleWishlist,
  isWishlisted = false
}) {
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose?.();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!product) return null;

  return (
    <div
      className="shelf-modal-backdrop"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label={`${product.title || 'Product'} details`}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        zIndex: 1000,
        backgroundColor: 'rgba(0, 0, 0, 0.55)',
        backdropFilter: 'blur(8px)',
        WebkitBackdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
        overflowY: 'auto'
      }}
    >
      <div
        className="shelf-modal-surface"
        onClick={(e) => e.stopPropagation()}
        style={{
          width: '100%',
          maxWidth: '1080px',
          maxHeight: '90vh',
          backgroundColor: '#FFFFFF',
          borderRadius: '20px',
          overflowY: 'auto',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
          border: '1px solid rgba(0, 0, 0, 0.08)',
          position: 'relative'
        }}
      >
        {/* Modal Top Header */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '16px 24px',
          borderBottom: '1px solid #E5E7EB',
          position: 'sticky',
          top: 0,
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(10px)',
          zIndex: 20
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '18px', fontWeight: 700, letterSpacing: '-0.03em', color: '#111111' }}>
              shelf<span style={{ color: '#8b5cf6' }}>.</span>
            </span>
            <span style={{ fontSize: '12px', color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 500 }}>
              Curated Details
            </span>
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label="Close dialog"
            style={{
              width: '34px',
              height: '34px',
              borderRadius: '50%',
              border: '1px solid #E5E7EB',
              background: '#F9F9F9',
              color: '#111111',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '15px',
              cursor: 'pointer',
              transition: 'background 0.15s ease'
            }}
          >
            ✕
          </button>
        </div>

        {/* Embedded Luxury Product Stage */}
        <div style={{ padding: '8px 12px' }}>
          <ShelfProductStage
            product={product}
            onToggleWishlist={onToggleWishlist}
            isWishlisted={isWishlisted}
            onOpenInstantOrder={onInstantOrder}
          />
        </div>
      </div>
    </div>
  );
}
