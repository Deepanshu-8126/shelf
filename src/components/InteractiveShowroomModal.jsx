import React, { useEffect, useRef, useState, useMemo } from 'react';
import * as THREE from 'three';
import Icon from './Icon.jsx';
import { getProductClickUrl } from '../affiliate.js';

function money(value) {
  return `₹${Number(value || 0).toLocaleString('en-IN')}`;
}

export default function InteractiveShowroomModal({ products = [], initialProduct = null, onClose, onOpenProduct }) {
  const mountRef = useRef(null);
  const [selectedProduct, setSelectedProduct] = useState(() => initialProduct || products[0] || null);
  const [stageColor, setStageColor] = useState('noir'); // 'noir', 'ivory', 'sage', 'sand'
  const [autoRotate, setAutoRotate] = useState(true);
  const [activeCategory, setActiveCategory] = useState('All');
  const [canvasReady, setCanvasReady] = useState(false);

  useEffect(() => {
    if (initialProduct) {
      setSelectedProduct(initialProduct);
    }
  }, [initialProduct]);

  // Filter products for showroom
  const showroomItems = useMemo(() => {
    return products.filter((p) => {
      if (activeCategory === 'All') return true;
      const cat = (p.category || '').toLowerCase();
      return cat.includes(activeCategory.toLowerCase());
    });
  }, [products, activeCategory]);

  useEffect(() => {
    if (!selectedProduct && showroomItems.length > 0) {
      setSelectedProduct(showroomItems[0]);
    }
  }, [showroomItems, selectedProduct]);

  // Three.js Interactive Cursor-Reactive Studio Stage
  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    let animId;
    const width = container.clientWidth || 600;
    const height = container.clientHeight || 520;

    // Scene
    const scene = new THREE.Scene();
    const bgColors = {
      noir: 0x090a0f,
      ivory: 0xfbf9f5,
      sage: 0xf1f5ed,
      sand: 0xf8f4ec
    };
    scene.background = new THREE.Color(bgColors[stageColor] || 0x090a0f);

    // Camera
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(0, 1.2, 3.8);

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    container.innerHTML = '';
    container.appendChild(renderer.domElement);
    setCanvasReady(true);

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
    scene.add(ambientLight);

    const mainSpot = new THREE.DirectionalLight(0xfff5ea, 1.2);
    mainSpot.position.set(2, 4, 3);
    mainSpot.castShadow = true;
    mainSpot.shadow.mapSize.width = 1024;
    mainSpot.shadow.mapSize.height = 1024;
    scene.add(mainSpot);

    const softFill = new THREE.DirectionalLight(0xdbe6d8, 0.6);
    softFill.position.set(-3, 2, -2);
    scene.add(softFill);

    // Plinth / Stage Platform
    const plinthGeo = new THREE.CylinderGeometry(1.2, 1.3, 0.15, 48);
    const plinthMat = new THREE.MeshStandardMaterial({
      color: 0xede8df,
      roughness: 0.4,
      metalness: 0.05
    });
    const plinth = new THREE.Mesh(plinthGeo, plinthMat);
    plinth.position.y = -0.65;
    plinth.receiveShadow = true;
    scene.add(plinth);

    // Subtle Ground Glow Ring
    const ringGeo = new THREE.RingGeometry(1.25, 1.32, 48);
    const ringMat = new THREE.MeshBasicMaterial({ color: 0x829a7d, side: THREE.DoubleSide, transparent: true, opacity: 0.35 });
    const ring = new THREE.Mesh(ringGeo, ringMat);
    ring.rotation.x = -Math.PI / 2;
    ring.position.y = -0.64;
    scene.add(ring);

    // Fashion Mannequin / Sculptural Silhouette Group
    const mannequinGroup = new THREE.Group();

    // Procedural Haute-Couture Torso & Sculpture
    const matSculpt = new THREE.MeshStandardMaterial({
      color: 0xf5eee6,
      roughness: 0.25,
      metalness: 0.08
    });
    const matWood = new THREE.MeshStandardMaterial({
      color: 0x3d352e,
      roughness: 0.7
    });
    const matBrass = new THREE.MeshStandardMaterial({
      color: 0xc8a96e,
      metalness: 0.85,
      roughness: 0.2
    });

    // Neck & Head abstract oval
    const headGeo = new THREE.SphereGeometry(0.18, 32, 32);
    headGeo.scale(0.85, 1.15, 0.9);
    const head = new THREE.Mesh(headGeo, matSculpt);
    head.position.y = 1.05;
    mannequinGroup.add(head);

    const neckGeo = new THREE.CylinderGeometry(0.065, 0.08, 0.2, 32);
    const neck = new THREE.Mesh(neckGeo, matSculpt);
    neck.position.y = 0.85;
    mannequinGroup.add(neck);

    // Torso (Fashion form)
    const torsoGeo = new THREE.CylinderGeometry(0.24, 0.2, 0.8, 32);
    torsoGeo.scale(1.1, 1, 0.7);
    const torso = new THREE.Mesh(torsoGeo, matSculpt);
    torso.position.y = 0.42;
    torso.castShadow = true;
    mannequinGroup.add(torso);

    // Hip sculpture
    const hipGeo = new THREE.CylinderGeometry(0.2, 0.26, 0.45, 32);
    hipGeo.scale(1.15, 1, 0.75);
    const hip = new THREE.Mesh(hipGeo, matSculpt);
    hip.position.y = -0.15;
    hip.castShadow = true;
    mannequinGroup.add(hip);

    // Brass Neck finial
    const finialGeo = new THREE.CylinderGeometry(0.08, 0.08, 0.04, 32);
    const finial = new THREE.Mesh(finialGeo, matBrass);
    finial.position.y = 0.96;
    mannequinGroup.add(finial);

    // Stand Rod & Base
    const rodGeo = new THREE.CylinderGeometry(0.02, 0.02, 0.5, 16);
    const rod = new THREE.Mesh(rodGeo, matBrass);
    rod.position.y = -0.42;
    mannequinGroup.add(rod);

    scene.add(mannequinGroup);

    // Cursor Reactive Parallax & Drag State
    let mouseX = 0;
    let mouseY = 0;
    let targetRotationY = 0;
    let targetRotationX = 0;
    let isDragging = false;
    let prevMouseX = 0;
    let currentRotY = 0;

    const handleMouseMove = (e) => {
      const rect = container.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const y = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
      mouseX = x;
      mouseY = y;
      if (!isDragging) {
        targetRotationY = currentRotY + mouseX * 0.18;
        targetRotationX = -mouseY * 0.08;
      }
    };

    const handleMouseDown = (e) => {
      isDragging = true;
      prevMouseX = e.clientX;
    };

    const handleMouseUp = () => {
      isDragging = false;
      currentRotY = mannequinGroup.rotation.y;
    };

    const handleMouseDrag = (e) => {
      if (!isDragging) return;
      const delta = e.clientX - prevMouseX;
      prevMouseX = e.clientX;
      currentRotY += delta * 0.012;
      targetRotationY = currentRotY;
    };

    const handleTouchStart = (e) => {
      if (e.touches && e.touches.length === 1) {
        isDragging = true;
        prevMouseX = e.touches[0].clientX;
      }
    };

    const handleTouchMove = (e) => {
      if (!isDragging || !e.touches || e.touches.length !== 1) return;
      const delta = e.touches[0].clientX - prevMouseX;
      prevMouseX = e.touches[0].clientX;
      currentRotY += delta * 0.015;
      targetRotationY = currentRotY;
    };

    const handleTouchEnd = () => {
      isDragging = false;
      currentRotY = mannequinGroup.rotation.y;
    };

    container.addEventListener('mousemove', handleMouseMove);
    container.addEventListener('mousedown', handleMouseDown);
    window.addEventListener('mouseup', handleMouseUp);
    window.addEventListener('mousemove', handleMouseDrag);
    container.addEventListener('touchstart', handleTouchStart, { passive: true });
    window.addEventListener('touchmove', handleTouchMove, { passive: true });
    window.addEventListener('touchend', handleTouchEnd);

    // Resize Observer
    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', handleResize);

    // Animation Loop
    const clock = new THREE.Clock();
    const animate = () => {
      animId = requestAnimationFrame(animate);
      const delta = clock.getDelta();

      if (autoRotate && !isDragging) {
        currentRotY += delta * 0.35;
        targetRotationY = currentRotY + mouseX * 0.15;
      }

      // Smooth Spring-like Lerping
      mannequinGroup.rotation.y += (targetRotationY - mannequinGroup.rotation.y) * 0.08;
      mannequinGroup.rotation.x += (targetRotationX - mannequinGroup.rotation.x) * 0.08;
      
      // Floating Micro-breath Motion
      mannequinGroup.position.y = Math.sin(clock.getElapsedTime() * 1.8) * 0.02;

      renderer.render(scene, camera);
    };

    animate();

    return () => {
      cancelAnimationFrame(animId);
      container.removeEventListener('mousemove', handleMouseMove);
      container.removeEventListener('mousedown', handleMouseDown);
      window.removeEventListener('mouseup', handleMouseUp);
      window.removeEventListener('mousemove', handleMouseDrag);
      container.removeEventListener('touchstart', handleTouchStart);
      window.removeEventListener('touchmove', handleTouchMove);
      window.removeEventListener('touchend', handleTouchEnd);
      window.removeEventListener('resize', handleResize);

      // Disposal
      renderer.dispose();
      scene.clear();
      if (container) container.innerHTML = '';
    };
  }, [stageColor, autoRotate]);

  return (
    <div className="modal-backdrop tryon-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-card showroom-modal-card" onClick={(e) => e.stopPropagation()}>
        {/* Header Bar */}
        <div className="showroom-modal-header">
          <div className="showroom-brand-pill">
            <span className="showroom-sparkle">✦</span>
            <span>INTERACTIVE 3D STYLE STUDIO</span>
          </div>
          <button className="icon-button showroom-close-btn" type="button" onClick={onClose} aria-label="Close 3D Showroom">
            ✕
          </button>
        </div>

        {/* Subtitle & Palette Controls */}
        <div className="showroom-subbar">
          <div>
            <h2>Editorial 3D Look Showroom</h2>
            <p>Interactive spatial fashion stage · Cursor-reactive 3D preview of curated creator picks</p>
          </div>
          <div className="showroom-stage-controls">
            <span className="stage-ctrl-label">Stage Ambience:</span>
            <div className="stage-palette-pills">
              <button 
                type="button" 
                className={`stage-pill-btn${stageColor === 'noir' ? ' is-active' : ''}`}
                onClick={() => setStageColor('noir')}
                title="Deep Noir Cyber Studio"
              >
                <span className="palette-swatch" style={{ background: '#090A0F', border: '1px solid #3b82f6' }} /> Noir
              </button>
              <button 
                type="button" 
                className={`stage-pill-btn${stageColor === 'ivory' ? ' is-active' : ''}`}
                onClick={() => setStageColor('ivory')}
                title="Warm Ivory Studio"
              >
                <span className="palette-swatch" style={{ background: '#FBF9F5' }} /> Ivory
              </button>
              <button 
                type="button" 
                className={`stage-pill-btn${stageColor === 'sage' ? ' is-active' : ''}`}
                onClick={() => setStageColor('sage')}
                title="Botanical Sage Studio"
              >
                <span className="palette-swatch" style={{ background: '#F1F5ED' }} /> Sage
              </button>
              <button 
                type="button" 
                className={`stage-pill-btn${stageColor === 'sand' ? ' is-active' : ''}`}
                onClick={() => setStageColor('sand')}
                title="Warm Sand Studio"
              >
                <span className="palette-swatch" style={{ background: '#F8F4EC' }} /> Sand
              </button>
            </div>
          </div>
        </div>

        {/* Main 2-Column Showroom Area */}
        <div className="showroom-main-grid">
          {/* Left: 3D Stage Viewport */}
          <div className="showroom-canvas-wrapper">
            <div ref={mountRef} className="showroom-three-stage" />
            
            {/* Interactive Stage Overlay Badges */}
            <div className="showroom-stage-overlay">
              <div className="showroom-floating-hint">
                <Icon name="sparkles" size={13} />
                <span>Move cursor to tilt · Drag to rotate</span>
              </div>
              <div className="showroom-stage-actions">
                <button
                  type="button"
                  className={`showroom-action-pill${autoRotate ? ' is-active' : ''}`}
                  onClick={() => setAutoRotate(!autoRotate)}
                >
                  {autoRotate ? '⏸ Pause Rotate' : '▶ Auto Rotate'}
                </button>
              </div>
            </div>

            {/* Selected Look floating card */}
            {selectedProduct && (
              <div className="showroom-active-look-card">
                <img src={selectedProduct.image} alt={selectedProduct.title} />
                <div className="look-card-info">
                  <span className="look-card-kicker">✦ STYLE PREVIEW</span>
                  <strong>{selectedProduct.title}</strong>
                  <span className="look-card-price">{money(selectedProduct.price)}</span>
                </div>
                <a
                  href={getProductClickUrl(selectedProduct)}
                  target="_blank"
                  rel="noreferrer"
                  className="button button-dark button-sm showroom-buy-btn"
                >
                  Shop this pick <Icon name="arrowUpRight" size={13} />
                </a>
              </div>
            )}
          </div>

          {/* Right: Curated Product Rail Selector */}
          <div className="showroom-sidebar-rail">
            <div className="showroom-rail-head">
              <strong>Select Item to Style</strong>
              <div className="showroom-cat-filters">
                {['All', 'Tops', 'Kurtis', 'Dresses', 'Bottomwear'].map((cat) => (
                  <button
                    key={cat}
                    type="button"
                    className={`showroom-cat-btn${activeCategory === cat ? ' is-active' : ''}`}
                    onClick={() => setActiveCategory(cat)}
                  >
                    {cat}
                  </button>
                ))}
              </div>
            </div>

            <div className="showroom-items-list">
              {showroomItems.map((prod) => {
                const isSelected = selectedProduct?.id === prod.id;
                return (
                  <div
                    key={prod.id}
                    className={`showroom-item-card${isSelected ? ' is-selected' : ''}`}
                    onClick={() => setSelectedProduct(prod)}
                  >
                    <div className="showroom-thumb-box">
                      <img src={prod.image} alt={prod.title} loading="lazy" />
                      {isSelected && <span className="selected-check">✓</span>}
                    </div>
                    <div className="showroom-item-meta">
                      <span className="showroom-item-cat">{prod.category || 'Fashion'}</span>
                      <strong className="showroom-item-title">{prod.title}</strong>
                      <div className="showroom-item-price-row">
                        <span className="item-price">{money(prod.price)}</span>
                        {prod.rating && <span className="item-rating">⭐ {prod.rating}</span>}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="showroom-disclaimer-note">
              <span>ⓘ Style preview for visual inspiration · Genuine verified catalog listings.</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
