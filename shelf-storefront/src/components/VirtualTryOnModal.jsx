import React, { useState, useMemo } from 'react';
import Icon from './Icon.jsx';
import InstantOrderModal from './InstantOrderModal.jsx';

function money(value) {
  return `₹${Number(value || 0).toLocaleString('en-IN')}`;
}

const DEFAULT_MODELS = [
  {
    id: 'model-female-1',
    name: 'Aanya (Chic / Streetwear)',
    gender: 'female',
    avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=400&q=80',
  },
  {
    id: 'model-male-1',
    name: 'Kabir (Blokecore / Grunge)',
    gender: 'male',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=400&q=80',
  },
];

export default function VirtualTryOnModal({ allProducts = [], onClose }) {
  const [selectedModel, setSelectedModel] = useState(DEFAULT_MODELS[0]);
  const [userUploadedPhoto, setUserUploadedPhoto] = useState(null);
  const [selectedProduct, setSelectedProduct] = useState(() => allProducts[0] || null);
  const [isProcessingFit, setIsProcessingFit] = useState(false);
  const [orderModalProduct, setOrderModalProduct] = useState(null);

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      const url = URL.createObjectURL(file);
      setUserUploadedPhoto(url);
      setIsProcessingFit(true);
      setTimeout(() => setIsProcessingFit(false), 800);
    }
  };

  const handleSelectGarment = (prod) => {
    setSelectedProduct(prod);
    setIsProcessingFit(true);
    setTimeout(() => setIsProcessingFit(false), 600);
  };

  const activeDisplayPhoto = userUploadedPhoto || selectedModel.avatar;

  return (
    <div className="modal-backdrop tryon-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-card tryon-card" onClick={(e) => e.stopPropagation()}>
        <button className="icon-button detail-close-btn" type="button" onClick={onClose} aria-label="Close Try-On Studio">
          ✕
        </button>

        <div className="tryon-header">
          <div className="tryon-badge">
            <span className="tryon-sparkle">🪞</span>
            <span>AI VIRTUAL FIT & TRY-ON STUDIO</span>
          </div>
          <h2>See How It Looks On You In Real Time</h2>
          <p>Switch between models or upload your photo to preview realistic outfit drape and fit before buying.</p>
        </div>

        <div className="tryon-layout-grid">
          {/* Left: Interactive Virtual Fitting Mirror */}
          <div className="tryon-mirror-stage">
            <div className="mirror-viewport">
              <img 
                src={activeDisplayPhoto} 
                alt="Fitting model" 
                className="mirror-base-photo"
              />
              
              {/* Projected Fitted Garment Overlay */}
              {selectedProduct && (
                <div className={`mirror-garment-layer ${isProcessingFit ? 'is-fitting-pulse' : ''}`}>
                  <img src={selectedProduct.image} alt={selectedProduct.title} />
                  <div className="garment-fit-tag">
                    <span>✦ Fitted: {selectedProduct.title}</span>
                  </div>
                </div>
              )}

              {isProcessingFit && (
                <div className="tryon-scanner-overlay">
                  <div className="scanner-laser" />
                  <span className="scanner-text">AI Neural Drape Fitting...</span>
                </div>
              )}
            </div>

            {/* Upload or Switch Model Controls */}
            <div className="mirror-controls-strip">
              <div className="model-switch-pills">
                {DEFAULT_MODELS.map((m) => (
                  <button
                    key={m.id}
                    type="button"
                    className={`model-pill-btn${selectedModel.id === m.id && !userUploadedPhoto ? ' is-active' : ''}`}
                    onClick={() => {
                      setUserUploadedPhoto(null);
                      setSelectedModel(m);
                      setIsProcessingFit(true);
                      setTimeout(() => setIsProcessingFit(false), 500);
                    }}
                  >
                    {m.name}
                  </button>
                ))}
              </div>

              <label className="tryon-upload-btn">
                <span>📷 Upload Your Photo</span>
                <input type="file" accept="image/*" onChange={handleFileUpload} style={{ display: 'none' }} />
              </label>
            </div>
          </div>

          {/* Right: Wardrobe Picker & 1-Click Buy */}
          <div className="tryon-wardrobe-panel">
            <div className="wardrobe-section-title">
              <strong>Select Item To Try On ({allProducts.length})</strong>
              <span>Tap any piece to project live</span>
            </div>

            <div className="wardrobe-scroll-grid">
              {allProducts.slice(0, 16).map((p) => (
                <button
                  key={p.id}
                  type="button"
                  className={`wardrobe-item-card${selectedProduct?.id === p.id ? ' is-selected' : ''}`}
                  onClick={() => handleSelectGarment(p)}
                >
                  <img src={p.image} alt={p.title} />
                  <div className="wardrobe-item-info">
                    <strong>{p.title}</strong>
                    <span>{money(p.price)}</span>
                  </div>
                </button>
              ))}
            </div>

            {/* Selected Garment Action Card */}
            {selectedProduct && (
              <div className="tryon-action-card">
                <div className="action-price-wrap">
                  <div>
                    <span className="action-label">Selected Fit:</span>
                    <strong>{selectedProduct.title}</strong>
                  </div>
                  <div className="action-price">
                    <strong>{money(selectedProduct.price)}</strong>
                    <del>{money(selectedProduct.oldPrice || Number(selectedProduct.price) * 1.6)}</del>
                  </div>
                </div>

                <button 
                  className="button button-dark tryon-order-btn" 
                  type="button"
                  onClick={() => setOrderModalProduct(selectedProduct)}
                >
                  <span>Order Fitted Look (COD) ↗</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {orderModalProduct && (
        <InstantOrderModal 
          product={orderModalProduct} 
          onClose={() => setOrderModalProduct(null)} 
        />
      )}
    </div>
  );
}
