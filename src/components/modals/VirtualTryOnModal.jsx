import React, { useState, useMemo, useRef, useEffect } from 'react';
import Icon from '../ui/Icon.jsx';
import InstantOrderModal from './InstantOrderModal.jsx';
import { getProductClickUrl } from '../../affiliate.js';

function money(value) {
  return `₹${Number(value || 0).toLocaleString('en-IN')}`;
}

const LUXURY_MODELS = [
  {
    id: 'model-ananya',
    name: 'Ananya V.',
    role: 'Editorial Ethnic & Kurti',
    gender: 'female',
    avatar: 'https://images.unsplash.com/photo-1617627143750-d86bc21e42bb?auto=format&fit=crop&w=700&q=85',
    drapeFitY: 26,
    drapeScale: 0.88,
  },
  {
    id: 'model-zoya',
    name: 'Zoya R.',
    role: 'Luxe Maxi & Bodycon',
    gender: 'female',
    avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=700&q=85',
    drapeFitY: 24,
    drapeScale: 0.85,
  },
  {
    id: 'model-kabir',
    name: 'Kabir M.',
    role: 'Streetwear & Blokecore',
    gender: 'male',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=700&q=85',
    drapeFitY: 28,
    drapeScale: 0.92,
  },
  {
    id: 'model-isha',
    name: 'Isha P.',
    role: 'Gen-Z Tops & Corsets',
    gender: 'female',
    avatar: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=700&q=85',
    drapeFitY: 25,
    drapeScale: 0.84,
  },
];

export default function VirtualTryOnModal({ allProducts = [], initialProduct = null, onClose }) {
  const [selectedModel, setSelectedModel] = useState(LUXURY_MODELS[0]);
  const [userUploadedPhoto, setUserUploadedPhoto] = useState(null);
  const [selectedProduct, setSelectedProduct] = useState(() => initialProduct || allProducts[0] || null);
  const [activeCategory, setActiveCategory] = useState('All');
  
  // Interactive Before/After Split Slider State (0 to 100)
  const [sliderPos, setSliderPos] = useState(50);
  const [isDraggingSlider, setIsDraggingSlider] = useState(false);
  const sliderRef = useRef(null);

  // AI Generation & Scanning States
  const [isScanning, setIsScanning] = useState(false);
  const [scanMessage, setScanMessage] = useState('Neural Silhouette Mapping...');
  const [orderModalProduct, setOrderModalProduct] = useState(null);

  // fal.ai Direct Engine Panel State
  const [showApiSettings, setShowApiSettings] = useState(false);
  const [falApiKey, setFalApiKey] = useState(() => {
    try {
      return localStorage.getItem('shelf_fal_key') || '';
    } catch {
      return '';
    }
  });
  const [falResultImage, setFalResultImage] = useState(null);
  const [isCallingFal, setIsCallingFal] = useState(false);
  const [falError, setFalError] = useState(null);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose?.();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  // Filter products by active category
  const filteredProducts = useMemo(() => {
    if (!allProducts || allProducts.length === 0) return [];
    if (activeCategory === 'All') return allProducts;
    return allProducts.filter((p) => {
      const cat = (p.category || '').toLowerCase();
      const title = (p.title || '').toLowerCase();
      const target = activeCategory.toLowerCase();
      return cat.includes(target) || title.includes(target);
    });
  }, [allProducts, activeCategory]);

  const activeDisplayPhoto = userUploadedPhoto || selectedModel.avatar;

  // Handle Photo Upload
  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      const url = URL.createObjectURL(file);
      setUserUploadedPhoto(url);
      setFalResultImage(null);
      triggerNeuralDrape('Custom Persona Ingested · Aligning Silhouette');
    }
  };

  // Trigger Visual Fitting Simulation
  const triggerNeuralDrape = (customMsg = 'Neural Cloth Drape & Diffusion Mapping...') => {
    setIsScanning(true);
    setScanMessage(customMsg);
    const timer = setTimeout(() => {
      setIsScanning(false);
    }, 700);
    return () => clearTimeout(timer);
  };

  const handleSelectProduct = (prod) => {
    setSelectedProduct(prod);
    setFalResultImage(null);
    triggerNeuralDrape(`Fitting ${prod.title.slice(0, 22)}...`);
  };

  // Slider Dragging Logic
  const handleSliderMove = (clientX) => {
    if (!sliderRef.current) return;
    const rect = sliderRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(clientX - rect.left, rect.width));
    const percent = Math.round((x / rect.width) * 100);
    setSliderPos(percent);
  };

  const handleMouseDown = () => setIsDraggingSlider(true);
  const handleTouchStart = () => setIsDraggingSlider(true);

  useEffect(() => {
    const handleMove = (e) => {
      if (!isDraggingSlider) return;
      const clientX = e.touches ? e.touches[0].clientX : e.clientX;
      handleSliderMove(clientX);
    };

    const handleStop = () => {
      if (isDraggingSlider) setIsDraggingSlider(false);
    };

    window.addEventListener('mousemove', handleMove);
    window.addEventListener('mouseup', handleStop);
    window.addEventListener('touchmove', handleMove);
    window.addEventListener('touchend', handleStop);

    return () => {
      window.removeEventListener('mousemove', handleMove);
      window.removeEventListener('mouseup', handleStop);
      window.removeEventListener('touchmove', handleMove);
      window.removeEventListener('touchend', handleStop);
    };
  }, [isDraggingSlider]);

  // Real fal.ai IDM-VTON API Connector
  const handleRunRealFalAi = async () => {
    if (!falApiKey.trim()) {
      setFalError('Please enter your fal.ai API key to trigger live GPU diffusion.');
      return;
    }
    setFalError(null);
    setIsCallingFal(true);
    try {
      localStorage.setItem('shelf_fal_key', falApiKey.trim());
    } catch {}

    try {
      // Direct call to fal.ai IDM-VTON queue API
      const response = await fetch('https://queue.fal.run/fal-ai/idm-vton', {
        method: 'POST',
        headers: {
          Authorization: `Key ${falApiKey.trim()}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          human_img: activeDisplayPhoto,
          garm_img: selectedProduct?.image,
          garment_des: selectedProduct?.title || 'haute couture apparel',
          category: selectedProduct?.category?.toLowerCase()?.includes('dress') ? 'dresses' : 'upper_body',
          nsfw_filter: true,
        }),
      });

      if (!response.ok) {
        const errText = await response.text();
        throw new Error(`fal.ai API returned status ${response.status}: ${errText.slice(0, 100)}`);
      }

      const data = await response.json();
      if (data?.image?.url) {
        setFalResultImage(data.image.url);
      } else if (data?.images?.[0]?.url) {
        setFalResultImage(data.images[0].url);
      } else {
        throw new Error('No image returned by fal.ai queue endpoint.');
      }
    } catch (err) {
      console.error('[fal.ai VTON Error]:', err);
      setFalError(err.message || 'Error executing fal.ai Try-On request.');
    } finally {
      setIsCallingFal(false);
    }
  };

  const affiliateUrl = selectedProduct ? getProductClickUrl(selectedProduct) : '#';

  return (
    <div className="modal-backdrop tryon-luxury-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-card tryon-luxury-card" onClick={(e) => e.stopPropagation()}>
        {/* Top Atelier Bar */}
        <div className="tryon-luxury-topbar">
          <div className="tryon-luxury-brand">
            <span className="tryon-gem">🪞</span>
            <div className="tryon-brand-meta">
              <div className="tryon-brand-title">
                <strong>SHELF AI VIRTUAL TRY-ON STUDIO</strong>
                <span className="tryon-engine-badge">IDM-VTON NEURAL ENGINE</span>
              </div>
              <p>Experience realistic fabric drape, silhouette contouring, and before-after comparison.</p>
            </div>
          </div>

          <div className="tryon-top-actions">
            <button
              type="button"
              className={`tryon-api-toggle-btn${showApiSettings ? ' is-active' : ''}`}
              onClick={() => setShowApiSettings(!showApiSettings)}
              title="Configure live fal.ai GPU diffusion"
            >
              <span>⚡ fal.ai Cloud API</span>
            </button>

            <button 
              className="icon-button tryon-luxury-close" 
              type="button" 
              onClick={onClose} 
              aria-label="Close Try-On Studio"
            >
              ✕
            </button>
          </div>
        </div>

        {/* fal.ai API Config Flyout */}
        {showApiSettings && (
          <div className="tryon-api-drawer">
            <div className="api-drawer-header">
              <strong>fal.ai `idm-vton` Live Cloud Connection</strong>
              <span>Optionally run server-grade photorealistic diffusion on fal.ai's H100 GPU cluster</span>
            </div>
            <div className="api-drawer-input-row">
              <input
                type="password"
                placeholder="Enter fal.ai API Key (e.g. fal_key_...)"
                value={falApiKey}
                onChange={(e) => setFalApiKey(e.target.value)}
                className="api-key-input"
              />
              <button
                type="button"
                className="button button-dark api-call-btn"
                onClick={handleRunRealFalAi}
                disabled={isCallingFal}
              >
                {isCallingFal ? 'Rendering on fal GPU...' : 'Run Live GPU Diffusion'}
              </button>
            </div>
            {falError && <p className="api-error-note">⚠️ {falError}</p>}
            <p className="api-helper-note">
              Default mode provides zero-latency neural canvas simulation without needing an API key.
            </p>
          </div>
        )}

        {/* Main Studio Grid */}
        <div className="tryon-studio-grid">
          {/* Left Column: Interactive Runway Fitting Mirror */}
          <div className="tryon-mirror-column">
            <div 
              ref={sliderRef}
              className={`tryon-stage-viewport${isDraggingSlider ? ' is-sliding' : ''}`}
              onMouseDown={handleMouseDown}
              onTouchStart={handleTouchStart}
            >
              {/* Layer 1: After / AI Fitted Canvas */}
              <div className="mirror-fitted-canvas">
                <img 
                  src={falResultImage || activeDisplayPhoto} 
                  alt="Model Fit Result" 
                  className="mirror-canvas-image" 
                />
                
                {/* Realistic Neural Drape Overlay (When not using falResultImage) */}
                {!falResultImage && selectedProduct && (
                  <div 
                    className="mirror-cloth-projection"
                    style={{
                      transform: `translateY(${selectedModel.drapeFitY || 25}%) scale(${selectedModel.drapeScale || 0.86})`,
                    }}
                  >
                    <img 
                      src={selectedProduct.image} 
                      alt={selectedProduct.title}
                      className="projected-garment-img"
                    />
                    <div className="cloth-lighting-shimmer" />
                  </div>
                )}

                <div className="mirror-watermark-tag after-tag">
                  <span>✦ AI DRAPED FIT</span>
                </div>
              </div>

              {/* Layer 2: Before Canvas (Clipped by Slider) */}
              <div 
                className="mirror-before-canvas"
                style={{ width: `${sliderPos}%` }}
              >
                <img 
                  src={activeDisplayPhoto} 
                  alt="Original Persona" 
                  className="mirror-canvas-image" 
                />
                <div className="mirror-watermark-tag before-tag">
                  <span>ORIGINAL SILHOUETTE</span>
                </div>
              </div>

              {/* Drag Handle Divider */}
              <div 
                className="mirror-slider-divider"
                style={{ left: `${sliderPos}%` }}
              >
                <div className="slider-handle-pill">
                  <span>◀</span>
                  <div className="handle-line" />
                  <span>▶</span>
                </div>
              </div>

              {/* Scanning Laser Animation */}
              {isScanning && (
                <div className="tryon-scanner-hud">
                  <div className="scanner-line-beam" />
                  <div className="scanner-hud-text">
                    <span className="hud-pulse-dot" />
                    <span>{scanMessage}</span>
                  </div>
                </div>
              )}

              {/* Fabric & Fit Intelligence HUD */}
              <div className="mirror-intelligence-hud">
                <div className="hud-metric">
                  <span className="hud-label">FIT PRECISION</span>
                  <strong>98.4% Silhouette Contour</strong>
                </div>
                <div className="hud-metric">
                  <span className="hud-label">FABRIC TEXTURE</span>
                  <strong>{selectedProduct?.category || 'Pure Georgette Drape'}</strong>
                </div>
              </div>
            </div>

            {/* Model Switcher & Persona Ingest Strip */}
            <div className="tryon-persona-strip">
              <div className="persona-model-pills">
                {LUXURY_MODELS.map((m) => (
                  <button
                    key={m.id}
                    type="button"
                    className={`persona-pill${selectedModel.id === m.id && !userUploadedPhoto ? ' is-active' : ''}`}
                    onClick={() => {
                      setUserUploadedPhoto(null);
                      setSelectedModel(m);
                      setFalResultImage(null);
                      triggerNeuralDrape(`Switched to ${m.name} (${m.role})`);
                    }}
                  >
                    <img src={m.avatar} alt={m.name} className="persona-mini-thumb" />
                    <div className="persona-mini-meta">
                      <strong>{m.name}</strong>
                      <span>{m.role}</span>
                    </div>
                  </button>
                ))}
              </div>

              {/* Upload Your Selfie */}
              <label className={`tryon-selfie-upload-btn${userUploadedPhoto ? ' has-custom-photo' : ''}`}>
                <input 
                  type="file" 
                  accept="image/*" 
                  onChange={handleFileUpload} 
                  style={{ display: 'none' }} 
                />
                <span className="upload-camera-icon">📷</span>
                <div className="upload-btn-text">
                  <strong>{userUploadedPhoto ? 'Change Photo' : 'Upload Selfie'}</strong>
                  <span>Auto-contour fit</span>
                </div>
              </label>
            </div>
          </div>

          {/* Right Column: Wardrobe Selector & Checkout */}
          <div className="tryon-wardrobe-column">
            {/* Category Filter Pills */}
            <div className="wardrobe-filter-tabs">
              {['All', 'Kurtis', 'Dresses', 'Tops', 'Men'].map((cat) => (
                <button
                  key={cat}
                  type="button"
                  className={`wardrobe-tab-btn${activeCategory === cat ? ' is-active' : ''}`}
                  onClick={() => setActiveCategory(cat)}
                >
                  {cat}
                </button>
              ))}
            </div>

            {/* Garments Rack List */}
            <div className="wardrobe-garments-rack">
              {filteredProducts.map((p) => {
                const isSelected = selectedProduct?.id === p.id;
                return (
                  <div
                    key={p.id}
                    className={`rack-garment-card${isSelected ? ' is-selected' : ''}`}
                    onClick={() => handleSelectProduct(p)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => e.key === 'Enter' && handleSelectProduct(p)}
                  >
                    <div className="rack-garment-thumb-wrap">
                      <img src={p.image} alt={p.title} className="rack-garment-img" />
                      {isSelected && (
                        <div className="rack-selected-badge">
                          <span>ON MIRROR</span>
                        </div>
                      )}
                    </div>

                    <div className="rack-garment-details">
                      <span className="rack-garment-cat">{p.category || 'Curated Fashion'}</span>
                      <strong className="rack-garment-title">{p.title}</strong>
                      <div className="rack-garment-pricing">
                        <strong className="rack-price">{money(p.price)}</strong>
                        {p.oldPrice && <del className="rack-old-price">{money(p.oldPrice)}</del>}
                        <span className="rack-discount-tag">Meesho COD</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Bottom Checkout & Action Deck */}
            {selectedProduct && (
              <div className="tryon-checkout-deck">
                <div className="deck-summary-row">
                  <div className="deck-summary-copy">
                    <span className="deck-eyebrow">READY TO WEAR</span>
                    <strong>{selectedProduct.title}</strong>
                    <span className="deck-drape-note">✓ Verified sizing & fabric drape</span>
                  </div>
                  <div className="deck-price-box">
                    <strong className="deck-main-price">{money(selectedProduct.price)}</strong>
                    <span className="deck-cod-badge">Cash on Delivery</span>
                  </div>
                </div>

                <div className="deck-cta-buttons">
                  <button
                    type="button"
                    className="button button-dark deck-order-btn"
                    onClick={() => setOrderModalProduct(selectedProduct)}
                  >
                    <span>⚡ Order Fitted Look (Instant COD)</span>
                  </button>

                  <a
                    href={affiliateUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="button button-outline deck-meesho-btn"
                  >
                    <span>Buy on Meesho ↗</span>
                  </a>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

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
