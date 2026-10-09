import React, { useEffect, useRef, useState, useMemo } from 'react';
import * as THREE from 'three';
import Icon from '../ui/Icon.jsx';
import { getProductClickUrl } from '../../affiliate.js';

function money(value) {
  return `₹${Number(value || 0).toLocaleString('en-IN')}`;
}

export default function InteractiveShowroomModal({ products = [], initialProduct = null, onClose, onOpenProduct }) {
  const mountRef = useRef(null);

  // Active view: 'mirror_hall' (Screen 1) or 'rack' (Screen 2)
  const [activeView, setActiveView] = useState('mirror_hall'); // 'mirror_hall' | 'rack'
  const [selectedProductIndex, setSelectedProductIndex] = useState(0);
  const [bodyShape, setBodyShape] = useState('regular'); // 'slim', 'regular', 'broad'
  const [selectedSize, setSelectedSize] = useState('M');
  const [selectedColorIndex, setSelectedColorIndex] = useState(0);
  const [cartCount, setCartCount] = useState(1);
  const [isRotating, setIsRotating] = useState(false);

  // Custom Drape Cursor Tracking
  const [cursorPos, setCursorPos] = useState({ x: -100, y: -100 });
  const [cursorHovered, setCursorHovered] = useState(false);
  const [isTouchDevice, setIsTouchDevice] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined' && window.matchMedia('(pointer: coarse)').matches) {
      setIsTouchDevice(true);
      return;
    }
    const handleMove = (e) => {
      setCursorPos({ x: e.clientX, y: e.clientY });
    };
    window.addEventListener('mousemove', handleMove);
    return () => window.removeEventListener('mousemove', handleMove);
  }, []);

  // Seed catalog / products fallback matching the Stitch design
  const showroomProducts = useMemo(() => {
    if (products && products.length >= 4) {
      return products.slice(0, 8);
    }
    return [
      {
        id: 'puffer-1',
        title: 'Puffer down jacket',
        name: 'Puffer down jacket',
        price: 4999,
        category: 'Jackets',
        gsm: '650 Fill Power',
        fabric: 'Weather-resistant ripstop nylon shell with goose down',
        colors: [
          { name: 'Core Black', hex: '#111111' },
          { name: 'Ghost White', hex: '#F3F4F6' },
          { name: 'Cobalt Blue', hex: '#2F6BFF' },
          { name: 'Sunset Amber', hex: '#FF7043' }
        ]
      },
      {
        id: 'hoodie-1',
        title: 'Sky oversized hoodie',
        name: 'Sky oversized hoodie',
        price: 2499,
        category: 'Hoodies',
        gsm: 'Heavyweight 450 gsm',
        fabric: 'Brushed loopback cotton fleece with self-standing cowl',
        colors: [
          { name: 'Sky Oversized', hex: '#6BA4B8' },
          { name: 'Core Black', hex: '#18181B' },
          { name: 'Graphite Heavyweight', hex: '#374151' },
          { name: 'Midnight Nylon', hex: '#1E293B' },
          { name: 'Dusty Berry', hex: '#9D4C6C' }
        ]
      },
      {
        id: 'denim-1',
        title: 'Wide-leg Japanese denim',
        name: 'Wide-leg Japanese denim',
        price: 3299,
        category: 'Denims',
        gsm: '13.5 oz Selvedge',
        fabric: 'Pure ring-spun kurabo denim',
        colors: [
          { name: 'Indigo Washed', hex: '#4B6B94' },
          { name: 'Pitch Black', hex: '#0F1115' }
        ]
      },
      {
        id: 'tee-1',
        title: 'Heavyweight dropped shoulder tee',
        name: 'Heavyweight dropped shoulder tee',
        price: 1299,
        category: 'Streetwear',
        gsm: '280 gsm Combed Cotton',
        fabric: 'Organic long-staple combed cotton',
        colors: [
          { name: 'Bone Cream', hex: '#EBE7DF' },
          { name: 'Washed Ash', hex: '#4B5563' }
        ]
      }
    ];
  }, [products]);

  const currentProduct = showroomProducts[selectedProductIndex] || showroomProducts[0];
  const activeColorList = currentProduct.colors || [
    { name: 'Core Black', hex: '#111111' },
    { name: 'Ghost White', hex: '#F3F4F6' },
    { name: 'Cobalt Blue', hex: '#2F6BFF' },
    { name: 'Sunset Amber', hex: '#FF7043' }
  ];
  const activeColor = activeColorList[selectedColorIndex] || activeColorList[0];

  const handleNextProduct = () => {
    setSelectedProductIndex((prev) => (prev + 1) % showroomProducts.length);
    setSelectedColorIndex(0);
  };

  const handlePrevProduct = () => {
    setSelectedProductIndex((prev) => (prev - 1 + showroomProducts.length) % showroomProducts.length);
    setSelectedColorIndex(0);
  };

  // -------------------------------------------------------------
  // THREE.JS 3D VIEWPORT ENGINE
  // -------------------------------------------------------------
  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    let animId;
    const width = container.clientWidth || window.innerWidth;
    const height = container.clientHeight || 560;

    // 1. Scene
    const scene = new THREE.Scene();

    // 2. Camera
    const camera = new THREE.PerspectiveCamera(42, width / height, 0.1, 100);
    camera.position.set(0, 0.5, 3.8);

    // 3. Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.8));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    const stageGroup = new THREE.Group();
    scene.add(stageGroup);

    const garmentColor = new THREE.Color(activeColor.hex);
    const bodyScale = bodyShape === 'slim' ? 0.88 : bodyShape === 'broad' ? 1.15 : 1.0;

    // =========================================================
    // SCENE LIGHTING & PROPS FOR SCREEN 1 (MIRROR HALL)
    // =========================================================
    let backMannequinGroup = null;

    if (activeView === 'mirror_hall') {
      // Warm Peach Ambient Background
      scene.background = new THREE.Color(0xFCEFED);
      scene.fog = new THREE.Fog(0xFCEFED, 6, 20);

      const ambientLight = new THREE.AmbientLight(0xFFE6E2, 0.9);
      scene.add(ambientLight);

      const dirLight = new THREE.DirectionalLight(0xFFF9F7, 1.4);
      dirLight.position.set(5, 10, 5);
      dirLight.castShadow = true;
      dirLight.shadow.mapSize.set(1024, 1024);
      scene.add(dirLight);

      // Warm Reflective Floor
      const floorGeo = new THREE.PlaneGeometry(50, 50);
      const floorMat = new THREE.MeshStandardMaterial({ color: 0xF4EAE7, roughness: 0.22, metalness: 0.08 });
      const floor = new THREE.Mesh(floorGeo, floorMat);
      floor.rotation.x = -Math.PI / 2;
      floor.position.y = -1.4;
      floor.receiveShadow = true;
      scene.add(floor);

      // Glowing Frosted Lightbox Oval Pedestal (under mannequin)
      const pedestalGeo = new THREE.CylinderGeometry(0.9, 0.95, 0.16, 48);
      const pedestalMat = new THREE.MeshPhysicalMaterial({
        color: 0xFFA07A,
        emissive: 0xFF7043,
        emissiveIntensity: 2.8,
        roughness: 0.16,
        transmission: 0.35,
        thickness: 0.4
      });
      const pedestal = new THREE.Mesh(pedestalGeo, pedestalMat);
      pedestal.position.set(0, -1.32, 0);
      pedestal.scale.set(1.4, 1, 0.85);
      pedestal.receiveShadow = true;
      stageGroup.add(pedestal);

      // Internal Peach Point Light
      const underglow = new THREE.PointLight(0xFF8A65, 3.5, 3.5);
      underglow.position.set(0, -1.1, 0);
      stageGroup.add(underglow);

      // Tall Blue Arch / Mirror Frame behind Mannequin
      const archMat = new THREE.MeshStandardMaterial({ color: 0x2F6BFF, metalness: 0.6, roughness: 0.2 });
      const archGeo = new THREE.BoxGeometry(2.3, 3.2, 0.08);
      const arch = new THREE.Mesh(archGeo, archMat);
      arch.position.set(0, 0.35, -0.3);

      // Semi-translucent Glass Plane
      const glassMat = new THREE.MeshPhysicalMaterial({
        color: 0xE8F0FE,
        roughness: 0.05,
        metalness: 0.9,
        transmission: 0.7,
        transparent: true,
        opacity: 0.82
      });
      const glass = new THREE.Mesh(new THREE.PlaneGeometry(2.1, 3.0), glassMat);
      glass.position.set(0, 0.35, -0.25);
      scene.add(arch, glass);

      // Chrome vertical support stand
      const standMat = new THREE.MeshStandardMaterial({ color: 0xD1D5DB, metalness: 0.95, roughness: 0.1 });
      const stand = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.018, 1.2, 24), standMat);
      stand.position.set(0, -0.7, 0);
      stageGroup.add(stand);

      // Back Mannequin (Mirrored 180 deg)
      backMannequinGroup = new THREE.Group();
      backMannequinGroup.position.set(0, -0.15, -0.85);
      scene.add(backMannequinGroup);
    }

    // =========================================================
    // SCENE LIGHTING & PROPS FOR SCREEN 2 (STUDIO RACK ROOM)
    // =========================================================
    let rackHangers = [];

    if (activeView === 'rack') {
      // Dark Slate Atmosphere
      scene.background = new THREE.Color(0x0F131A);
      scene.fog = new THREE.Fog(0x0F131A, 5, 20);

      const ambientLight = new THREE.AmbientLight(0x222B38, 0.7);
      scene.add(ambientLight);

      // Overhead soft strip lights
      const stripLightL = new THREE.PointLight(0x6BA4B8, 2.5, 8);
      stripLightL.position.set(-2, 3, 1);
      const stripLightR = new THREE.PointLight(0x2F6BFF, 2.0, 8);
      stripLightR.position.set(2, 3, 1);
      scene.add(stripLightL, stripLightR);

      // Polished asphalt floor
      const floorGeo = new THREE.PlaneGeometry(50, 50);
      const floorMat = new THREE.MeshStandardMaterial({ color: 0x121720, roughness: 0.18, metalness: 0.7 });
      const floor = new THREE.Mesh(floorGeo, floorMat);
      floor.rotation.x = -Math.PI / 2;
      floor.position.y = -1.4;
      floor.receiveShadow = true;
      scene.add(floor);

      // Industrial Pipe Rack with Caster Wheels
      const rackMat = new THREE.MeshStandardMaterial({ color: 0x1E2530, metalness: 0.85, roughness: 0.25 });
      const casterMat = new THREE.MeshStandardMaterial({ color: 0x0A0D12, roughness: 0.5 });
      const rackGroup = new THREE.Group();

      // Top Crossbar
      const topBar = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 2.8, 16), rackMat);
      topBar.rotation.z = Math.PI / 2;
      topBar.position.y = 1.1;
      rackGroup.add(topBar);

      // Vertical Uprights
      [-1.35, 1.35].forEach((x) => {
        const post = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 2.5, 16), rackMat);
        post.position.set(x, -0.15, 0);

        const foot = new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.04, 0.7), rackMat);
        foot.position.set(x, -1.35, 0);

        const w1 = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 0.03, 16), casterMat);
        w1.rotation.z = Math.PI / 2;
        w1.position.set(x, -1.38, 0.28);

        const w2 = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 0.03, 16), casterMat);
        w2.rotation.z = Math.PI / 2;
        w2.position.set(x, -1.38, -0.28);

        rackGroup.add(post, foot, w1, w2);
      });
      stageGroup.add(rackGroup);

      // 5 Hanging Garments along the rack
      const hoodieColors = [0x1E1E24, 0x374151, garmentColor.getHex(), 0x1E293B, 0x88385A];
      hoodieColors.forEach((col, i) => {
        const posX = (i - 2) * 0.52;
        const isCenter = i === 2;
        const hGroup = new THREE.Group();
        hGroup.position.set(posX, 0.0, 0);

        // Hanger Wire
        const hangerMat = new THREE.MeshStandardMaterial({ color: 0x888888, metalness: 0.8 });
        const hanger = new THREE.Mesh(new THREE.CylinderGeometry(0.008, 0.008, 0.7, 12), hangerMat);
        hanger.rotation.z = Math.PI / 2;
        hanger.position.set(0, 1.0, 0);
        hGroup.add(hanger);

        // Garment Mesh
        const gMesh = createGarmentMesh(new THREE.Color(col), isCenter ? bodyScale : 0.95);
        gMesh.position.y = -0.1;
        hGroup.add(gMesh);

        stageGroup.add(hGroup);
        rackHangers.push(hGroup);
      });
    }

    // =========================================================
    // GARMENT MESH GENERATOR (Puffer / Cowl Hoodie / Mannequin)
    // =========================================================
    function createGarmentMesh(color, widthScale = 1.0) {
      const g = new THREE.Group();
      g.scale.set(widthScale, 1, 1);

      const mat = new THREE.MeshStandardMaterial({
        color: color,
        roughness: 0.45,
        metalness: 0.12
      });

      // Faceless Mannequin Neck / Head Base
      const headMat = new THREE.MeshStandardMaterial({ color: 0xCBD5E1, roughness: 0.25, metalness: 0.6 });
      const head = new THREE.Mesh(new THREE.SphereGeometry(0.14, 24, 24), headMat);
      head.position.set(0, 0.72, 0);
      g.add(head);

      // Puffy Segment 1 (Chest & Shoulders)
      const seg1 = new THREE.Mesh(new THREE.CylinderGeometry(0.42, 0.46, 0.45, 32), mat);
      seg1.position.set(0, 0.32, 0);
      seg1.castShadow = true;

      // Puffy Segment 2 (Mid-Torso)
      const seg2 = new THREE.Mesh(new THREE.CylinderGeometry(0.46, 0.44, 0.42, 32), mat);
      seg2.position.set(0, -0.08, 0);
      seg2.castShadow = true;

      // Puffy Segment 3 (Waist)
      const seg3 = new THREE.Mesh(new THREE.CylinderGeometry(0.44, 0.41, 0.35, 32), mat);
      seg3.position.set(0, -0.42, 0);
      seg3.castShadow = true;

      // Sleeves with Segmented Puffer Rings
      const sleeveL = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.15, 0.68, 24), mat);
      sleeveL.rotation.z = 0.35;
      sleeveL.position.set(-0.52, 0.15, 0);
      sleeveL.castShadow = true;

      const sleeveR = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.15, 0.68, 24), mat);
      sleeveR.rotation.z = -0.35;
      sleeveR.position.set(0.52, 0.15, 0);
      sleeveR.castShadow = true;

      // Structured Stand-Up Cowl Collar
      const collar = new THREE.Mesh(new THREE.TorusGeometry(0.24, 0.08, 16, 32), mat);
      collar.rotation.x = Math.PI / 2;
      collar.position.set(0, 0.54, 0);

      g.add(seg1, seg2, seg3, sleeveL, sleeveR, collar);
      return g;
    }

    // In Mirror Hall, add the main front garment
    if (activeView === 'mirror_hall') {
      const frontMesh = createGarmentMesh(garmentColor, bodyScale);
      frontMesh.position.set(0, -0.15, 0);
      stageGroup.add(frontMesh);

      if (backMannequinGroup) {
        const backMesh = createGarmentMesh(garmentColor, bodyScale);
        backMannequinGroup.add(backMesh);
      }
    }

    // =========================================================
    // INTERACTION & ANIMATION LOOP
    // =========================================================
    let currentRot = 0;
    let targetRot = 0;
    let prevX = 0;

    const onPointerDown = (e) => {
      setIsRotating(true);
      prevX = e.clientX;
    };

    const onPointerMove = (e) => {
      if (prevX !== 0 && (e.buttons === 1 || e.type === 'touchmove')) {
        const clientX = e.clientX || (e.touches && e.touches[0].clientX) || 0;
        const delta = clientX - prevX;
        targetRot += delta * 0.014;
        prevX = clientX;
      }
    };

    const onPointerUp = () => {
      setIsRotating(false);
      prevX = 0;
    };

    const dom = renderer.domElement;
    dom.addEventListener('mousedown', onPointerDown);
    dom.addEventListener('mousemove', onPointerMove);
    window.addEventListener('mouseup', onPointerUp);

    const clock = new THREE.Clock();
    const animate = () => {
      animId = requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();

      // Smooth Rotation Lerp
      currentRot = THREE.MathUtils.lerp(currentRot, targetRot, 0.08);
      stageGroup.rotation.y = currentRot;

      // Inverted Back Reflection (θ_ref = π - θ)
      if (backMannequinGroup) {
        backMannequinGroup.rotation.y = Math.PI - currentRot;
      }

      // Idle garment sway on rack
      if (rackHangers.length > 0) {
        rackHangers.forEach((h, i) => {
          h.rotation.z = Math.sin(elapsed * 1.6 + i) * 0.025;
        });
      }

      renderer.render(scene, camera);
    };
    animate();

    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animId);
      dom.removeEventListener('mousedown', onPointerDown);
      dom.removeEventListener('mousemove', onPointerMove);
      window.removeEventListener('mouseup', onPointerUp);
      window.removeEventListener('resize', handleResize);
      renderer.dispose();
    };
  }, [activeView, selectedProductIndex, selectedColorIndex, bodyShape]);

  return (
    <div className="fixed inset-0 z-50 w-screen h-screen overflow-hidden flex flex-col select-none">
      
      {/* Custom Drape Dynamic Cursor */}
      {!isTouchDevice && (
        <>
          <div
            className="drape-cursor-dot"
            style={{
              transform: `translate3d(${cursorPos.x - 4}px, ${cursorPos.y - 4}px, 0)`
            }}
          />
          <div
            className={`drape-cursor-ring ${cursorHovered ? 'is-hovered' : ''}`}
            style={{
              transform: `translate3d(${cursorPos.x - (cursorHovered ? 27 : 15)}px, ${cursorPos.y - (cursorHovered ? 27 : 15)}px, 0)`
            }}
          />
        </>
      )}

      {/* Outer Viewport Canvas Fullscreen */}
      <div className={`relative w-full h-full overflow-hidden flex flex-col transition-colors duration-500 ${
        activeView === 'mirror_hall' ? 'bg-[#FCEFED]' : 'bg-[#0F131A] text-white'
      }`}>
        
        {/* =========================================================
            TOPBAR (Matching Stitch Screenshots 1 & 2)
            ========================================================= */}
        <header className="absolute top-0 left-0 right-0 z-30 flex items-center justify-between px-6 py-4 pointer-events-none">
          <div className="flex items-center gap-3 pointer-events-auto">
            <button
              onClick={onClose}
              onMouseEnter={() => setCursorHovered(true)}
              onMouseLeave={() => setCursorHovered(false)}
              className={`flex items-center justify-center w-10 h-10 rounded-full shadow-md transition border ${
                activeView === 'mirror_hall'
                  ? 'bg-white text-[#111111] hover:text-[#2F6BFF] border-[#C9CED8]/40'
                  : 'bg-[#1E2530] text-white hover:text-[#2F6BFF] border-white/10'
              }`}
              aria-label="Back to 2D store"
              title="Return to 2D Storefront"
            >
              <Icon name="arrow-left" size={18} />
            </button>
            <div className="flex items-center gap-2">
              <span className={`text-2xl font-bold tracking-tight ${activeView === 'mirror_hall' ? 'text-[#111111]' : 'text-white'}`}>
                Drape
              </span>
            </div>
          </div>

          {/* Center Breadcrumb Pill */}
          <div className={`hidden sm:flex items-center gap-2 text-xs font-semibold backdrop-blur-md px-4 py-2 rounded-full shadow-sm border pointer-events-auto ${
            activeView === 'mirror_hall'
              ? 'bg-white/80 text-[#6B7380] border-[#C9CED8]/40'
              : 'bg-[#18202C]/80 text-white/60 border-white/10'
          }`}>
            <span>Lobby</span>
            <span>/</span>
            <span>Men</span>
            <span>/</span>
            <span className={`font-bold ${activeView === 'mirror_hall' ? 'text-[#111111]' : 'text-white'}`}>
              {activeView === 'mirror_hall' ? 'Mirror Hall' : 'Streetwear'}
            </span>
          </div>

          {/* Right Controls: Room Switcher, Simple view toggle, Cart, Profile */}
          <div className="flex items-center gap-3 pointer-events-auto">
            <button
              onClick={() => setActiveView(activeView === 'mirror_hall' ? 'rack' : 'mirror_hall')}
              onMouseEnter={() => setCursorHovered(true)}
              onMouseLeave={() => setCursorHovered(false)}
              className={`hidden md:flex items-center gap-1.5 text-xs font-semibold px-4 py-2 rounded-full shadow-sm transition border ${
                activeView === 'mirror_hall'
                  ? 'bg-white text-[#111111] hover:text-[#2F6BFF] border-[#C9CED8]/40'
                  : 'bg-[#1E2530] text-white hover:text-[#2F6BFF] border-white/10'
              }`}
              title="Switch 3D architectural room"
            >
              <span>{activeView === 'mirror_hall' ? '🗄️ Studio Rack' : '🪞 Mirror Hall'}</span>
            </button>

            <button
              onClick={onClose}
              onMouseEnter={() => setCursorHovered(true)}
              onMouseLeave={() => setCursorHovered(false)}
              className={`flex items-center gap-1.5 text-xs font-semibold px-4 py-2 rounded-full shadow-sm transition border ${
                activeView === 'mirror_hall'
                  ? 'bg-white/90 text-[#6B7380] hover:text-[#2F6BFF] border-[#C9CED8]/40'
                  : 'bg-[#1E2530] text-white/70 hover:text-white border-white/10'
              }`}
              title="Open 2D grid view"
            >
              <span>Simple view</span>
            </button>

            <button
              onClick={() => {
                if (onOpenProduct) onOpenProduct(currentProduct);
                else if (currentProduct.productUrl) window.open(getProductClickUrl(currentProduct), '_blank');
              }}
              onMouseEnter={() => setCursorHovered(true)}
              onMouseLeave={() => setCursorHovered(false)}
              className="flex items-center gap-2 bg-[#111111] text-white px-5 py-2.5 rounded-full shadow-md hover:bg-[#2F6BFF] transition text-xs font-bold"
            >
              <Icon name="bag" size={14} />
              <span>Cart ({cartCount})</span>
            </button>

            <div className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-xs border ${
              activeView === 'mirror_hall' ? 'bg-white text-[#111111] border-[#C9CED8]/40' : 'bg-[#1E2530] text-white border-white/10'
            }`}>
              👤
            </div>
          </div>
        </header>

        {/* Sub-header status indicators */}
        <div className="absolute top-16 left-6 right-6 z-20 flex items-center justify-between pointer-events-none">
          <div className="flex items-center gap-2">
            <span className={`text-[10px] font-bold tracking-widest px-3 py-1 rounded-full uppercase border ${
              activeView === 'mirror_hall' ? 'bg-white/90 text-[#6B7380] border-[#C9CED8]/40' : 'bg-[#1A222F]/90 text-white/60 border-white/10'
            }`}>
              {activeView === 'mirror_hall' ? 'VIRTUAL STUDIO - 04' : 'Studio rack room / Tray 04'}
            </span>
            <span className="flex items-center gap-1.5 text-[10px] font-bold tracking-widest px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-600 border border-emerald-500/20">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              {activeView === 'mirror_hall' ? 'Spatial Engine Live' : '450 GSM winter drop'}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className={`text-[10px] font-bold tracking-widest px-3 py-1 rounded-full border ${
              activeView === 'mirror_hall' ? 'bg-white/90 text-[#6B7380] border-[#C9CED8]/40' : 'bg-[#1A222F]/90 text-white/60 border-white/10'
            }`}>
              {activeView === 'mirror_hall' ? 'High Specular' : 'Move cursor to drift camera · Click any hoodie to inspect'}
            </span>
          </div>
        </div>

        {/* 3D Viewport Mount */}
        <div ref={mountRef} className="w-full flex-1 cursor-grab active:cursor-grabbing" style={{ minHeight: '440px' }} />

        {/* =========================================================
            SCREEN 1: MIRROR HALL FLOATING CONTROLS
            ========================================================= */}
        {activeView === 'mirror_hall' && (
          <>
            {/* 180° REAR DRAPE Arch Text Header */}
            <div className="absolute top-28 left-1/2 -translate-x-1/2 z-20 pointer-events-none text-center">
              <p className="text-[11px] font-bold uppercase tracking-widest text-[#2F6BFF] drop-shadow-sm">
                180° REAR DRAPE
              </p>
            </div>

            {/* Glowing Oval Pedestal Description Text */}
            <div className="absolute bottom-56 left-1/2 -translate-x-1/2 z-20 pointer-events-none text-center">
              <p className="text-[11px] font-bold text-[#6B7380] uppercase tracking-wider">
                Mirror Specular Reflection
              </p>
              <p className="text-[10px] text-[#6B7380]/80 mt-0.5">
                Drag horizontally to rotate mannequin (reflection syncs in real-time)
              </p>
            </div>

            {/* Floating Product Focus Card (Matching Screenshot 1) */}
            <div className="absolute bottom-16 left-1/2 -translate-x-1/2 z-30 w-[94%] max-w-[480px]">
              <div className="bg-white/95 backdrop-blur-md rounded-[24px] p-5 shadow-2xl border border-[#C9CED8]/40">
                
                {/* Header with < / > navigation */}
                <div className="flex items-center justify-between mb-3">
                  <button
                    onClick={handlePrevProduct}
                    className="w-8 h-8 rounded-full flex items-center justify-center bg-[#F4F6FA] hover:bg-[#E5E7EB] text-[#111111] transition"
                  >
                    ‹
                  </button>
                  <div className="text-center">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#6B7380] block">
                      SELECTED GARMENT
                    </span>
                    <h3 className="font-bold text-base text-[#111111]">{currentProduct.title || currentProduct.name}</h3>
                  </div>
                  <div className="text-right">
                    <span className="text-base font-bold text-[#111111]">{money(currentProduct.price)}</span>
                  </div>
                  <button
                    onClick={handleNextProduct}
                    className="w-8 h-8 rounded-full flex items-center justify-center bg-[#F4F6FA] hover:bg-[#E5E7EB] text-[#111111] transition"
                  >
                    ›
                  </button>
                </div>

                {/* Silhouette Proportion & Palette Nuance Row */}
                <div className="flex items-center justify-between pt-2 pb-3 border-t border-[#C9CED8]/30">
                  {/* Silhouette Proportion */}
                  <div>
                    <span className="text-[10px] font-semibold text-[#6B7380] block mb-1.5">Silhouette proportion</span>
                    <div className="flex items-center gap-1.5 bg-[#F4F6FA] p-1 rounded-full">
                      {['slim', 'regular', 'broad'].map((shape) => (
                        <button
                          key={shape}
                          onClick={() => setBodyShape(shape)}
                          className={`px-3 py-1 rounded-full text-[11px] font-bold capitalize transition ${
                            bodyShape === shape ? 'bg-[#111111] text-white shadow-sm' : 'text-[#6B7380] hover:text-[#111111]'
                          }`}
                        >
                          {shape}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Palette Nuance Swatches */}
                  <div>
                    <span className="text-[10px] font-semibold text-[#6B7380] block mb-1.5 text-right">Palette nuance</span>
                    <div className="flex items-center gap-2">
                      {activeColorList.map((col, idx) => (
                        <button
                          key={col.name}
                          onClick={() => setSelectedColorIndex(idx)}
                          className={`w-6 h-6 rounded-full border-2 transition-transform ${
                            selectedColorIndex === idx ? 'border-[#2F6BFF] scale-110' : 'border-transparent hover:scale-105'
                          }`}
                          style={{ backgroundColor: col.hex }}
                          title={col.name}
                        />
                      ))}
                    </div>
                  </div>
                </div>

                {/* Action Buttons: Add to Bag + Racks */}
                <div className="flex items-center gap-2 pt-1">
                  <button
                    onClick={() => {
                      setCartCount((c) => c + 1);
                      if (onOpenProduct) onOpenProduct(currentProduct);
                      else if (currentProduct.productUrl) window.open(getProductClickUrl(currentProduct), '_blank');
                    }}
                    className="flex-1 py-3 bg-[#111111] hover:bg-[#2F6BFF] text-white text-xs font-bold rounded-full shadow-lg transition flex items-center justify-center gap-2"
                  >
                    <Icon name="bag" size={14} />
                    <span>Add to bag — {money(currentProduct.price)}</span>
                  </button>

                  <button
                    onClick={() => setActiveView('rack')}
                    className="px-4 py-3 bg-[#F4F6FA] hover:bg-[#E5E7EB] text-[#111111] text-xs font-bold rounded-full transition flex items-center gap-1.5"
                  >
                    <span>🗄️</span>
                    <span>Racks</span>
                  </button>
                </div>

              </div>
            </div>
          </>
        )}

        {/* =========================================================
            SCREEN 2: STUDIO RACK ROOM & ARCHITECTURAL SPEC SHEET
            ========================================================= */}
        {activeView === 'rack' && (
          <>
            {/* Active Specimen Highlight on Rack */}
            <div className="absolute top-28 left-1/2 -translate-x-1/2 z-20 pointer-events-none text-center">
              <span className="text-[10px] font-bold uppercase tracking-wider px-3 py-1 rounded-full bg-white/10 text-white/80 border border-white/20">
                Active specimen
              </span>
              <p className="text-[10px] text-white/50 mt-1">Drag to spin 360°</p>
            </div>

            {/* Floating Right Detail Card (Matching Screenshot 2) */}
            <div className="absolute top-44 right-8 z-30 w-72 bg-[#1A222F]/90 backdrop-blur-md rounded-2xl p-4 shadow-2xl border border-white/10 text-white">
              <div className="flex items-center justify-between text-[10px] text-white/60 mb-1">
                <span>Heavyweight 450 gsm</span>
                <span className="text-[#6BA4B8] font-semibold">↺ 360° ready</span>
              </div>
              <h3 className="font-bold text-sm tracking-tight text-white mb-0.5">Sky oversized hoodie</h3>
              <p className="text-[11px] text-white/50 mb-3">Brushed loopback cotton fleece</p>

              {/* Price & Size guide */}
              <div className="flex items-baseline justify-between mb-2">
                <span className="text-base font-bold text-white">₹2,499</span>
                <span className="text-[10px] text-white/50 underline cursor-pointer">Size guide</span>
              </div>

              {/* Size Selector */}
              <div className="mb-4">
                <div className="flex items-center justify-between text-[10px] text-white/60 mb-1.5">
                  <span>Select size</span>
                  <span className="text-emerald-400">Stock: 4 left</span>
                </div>
                <div className="flex gap-1.5">
                  {['S', 'M', 'L', 'XL'].map((sz) => (
                    <button
                      key={sz}
                      onClick={() => setSelectedSize(sz)}
                      className={`flex-1 py-1 text-xs font-bold rounded-lg transition ${
                        selectedSize === sz ? 'bg-white text-[#111111] shadow-sm' : 'bg-[#252E3E] text-white/70 hover:bg-[#313C50]'
                      }`}
                    >
                      {sz}
                    </button>
                  ))}
                </div>
              </div>

              {/* Buttons */}
              <div className="space-y-2">
                <button
                  onClick={() => setCartCount((c) => c + 1)}
                  className="w-full py-2.5 bg-white hover:bg-[#2F6BFF] text-[#111111] hover:text-white font-bold text-xs rounded-full transition flex items-center justify-center gap-1.5 shadow-md"
                >
                  <Icon name="bag" size={13} />
                  <span>Add to cart</span>
                </button>

                <button
                  onClick={() => setActiveView('mirror_hall')}
                  className="w-full py-2 border border-white/20 hover:border-[#2F6BFF] text-white text-[11px] font-semibold rounded-full transition flex items-center justify-center gap-1.5"
                >
                  <span>🪞</span>
                  <span>Try in mirror hall</span>
                </button>
              </div>
            </div>

            {/* Bottom Spec Sheet Panel (Matching Screenshot 2) */}
            <div className="absolute bottom-16 left-6 right-6 z-20 bg-[#161D27]/90 backdrop-blur-md rounded-2xl p-4 border border-white/10 text-white">
              <div className="flex items-start justify-between mb-3 pb-2 border-b border-white/10">
                <div>
                  <span className="text-[9px] font-bold uppercase tracking-widest text-[#6BA4B8] block">
                    ARCHITECTURAL SPEC SHEET
                  </span>
                  <h4 className="font-bold text-xs text-white">Loopback construction & spatial drape</h4>
                </div>
                <p className="text-[10px] text-white/50 max-w-md text-right hidden md:block">
                  Engineered with a tailored Japanese double-needle rib, custom cowl hood geometry, and dropped shoulder seam contours to retain structural volume in physical space.
                </p>
              </div>

              {/* Three Specimen Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {/* Specimen 01 */}
                <div className="bg-[#1C2533] rounded-xl p-2.5 border border-white/5">
                  <div className="flex justify-between text-[9px] text-white/50 mb-1">
                    <span>Specimen textile 01</span>
                    <span className="text-emerald-400">100% Organic</span>
                  </div>
                  <div className="h-14 rounded-lg bg-gradient-to-r from-blue-900 to-indigo-950 flex items-center justify-center text-[10px] text-white/60 mb-1.5">
                    Double-needle surface
                  </div>
                  <p className="text-[10px] font-bold text-white">Pre-shrunk 450 gsm heavy jersey</p>
                  <p className="text-[9px] text-white/40">Dense tight knit prevents sagging while maintaining cloud-like softness.</p>
                </div>

                {/* Specimen 02 */}
                <div className="bg-[#1C2533] rounded-xl p-2.5 border border-white/5">
                  <div className="flex justify-between text-[9px] text-white/50 mb-1">
                    <span>Specimen textile 02</span>
                    <span className="text-[#6BA4B8]">Structured Hood</span>
                  </div>
                  <div className="h-14 rounded-lg bg-gradient-to-r from-slate-800 to-zinc-900 flex items-center justify-center text-[10px] text-white/60 mb-1.5">
                    Self-standing cowl structure
                  </div>
                  <p className="text-[10px] font-bold text-white">Self-standing 3-piece cowl hood</p>
                  <p className="text-[9px] text-white/40">Designed without drawstrings for an uninterrupted sculptural silhouette.</p>
                </div>

                {/* Room Palette List */}
                <div className="bg-[#1C2533] rounded-xl p-2.5 border border-white/5 text-[10px]">
                  <div className="flex justify-between text-[9px] text-white/50 mb-1.5">
                    <span>Room palette</span>
                    <span>4 Shades</span>
                  </div>
                  <div className="space-y-1">
                    <div className="flex justify-between text-white/70">
                      <span className="flex items-center gap-1.5">● Core black</span>
                      <span>₹2,499</span>
                    </div>
                    <div className="flex justify-between text-white/70">
                      <span className="flex items-center gap-1.5">● Graphite heavyweight</span>
                      <span>₹2,499</span>
                    </div>
                    <div className="flex justify-between text-[#6BA4B8] font-bold">
                      <span className="flex items-center gap-1.5">● Sky oversized (selected)</span>
                      <span>₹2,499</span>
                    </div>
                    <div className="flex justify-between text-white/70">
                      <span className="flex items-center gap-1.5">● Midnight nylon</span>
                      <span>₹2,499</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}

        {/* =========================================================
            BOTTOM CATEGORY PILLS (Matching Stitch Footer Bar)
            ========================================================= */}
        <div className="absolute bottom-3 left-0 right-0 z-30 flex items-center justify-between px-6 pointer-events-none">
          <div className="text-[10px] text-[#6B7380] font-semibold hidden md:block">
            Drape Studio · <span className="font-normal">Architectural Virtual Showroom</span>
          </div>

          <div className="drape-category-container pointer-events-auto">
            {[
              { id: 'streetwear', label: 'Streetwear' },
              { id: 'jackets', label: 'Jackets' },
              { id: 'hoodies', label: 'Hoodies' },
              { id: 'denims', label: 'Denims' },
              { id: 'mirror_hall', label: 'Mirror hall' }
            ].map((cat) => {
              const isActive = (cat.id === 'mirror_hall' && activeView === 'mirror_hall') ||
                               (cat.id !== 'mirror_hall' && activeView === 'rack');
              return (
                <button
                  key={cat.id}
                  onClick={() => {
                    if (cat.id === 'mirror_hall') setActiveView('mirror_hall');
                    else setActiveView('rack');
                  }}
                  className={`drape-category-pill ${isActive ? 'is-active' : ''}`}
                >
                  {cat.label}
                </button>
              );
            })}
          </div>

          <div className="text-[10px] text-[#6B7380] font-normal hidden md:block">
            Spatial Experience Engine © 2025 Drape. All rights reserved.
          </div>
        </div>

      </div>
    </div>
  );
}
