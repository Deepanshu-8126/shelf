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
  const [roomArchetype, setRoomArchetype] = useState('peach'); // 'peach', 'petal_vortex', 'cyber_garage', 'minimalist_rail', 'mirror_hall'
  const [bodyShape, setBodyShape] = useState('regular'); // 'slim' (0.88), 'regular' (1.0), 'broad' (1.15)
  const [selectedColorHex, setSelectedColorHex] = useState('#ffffff');
  const [cursorPos, setCursorPos] = useState({ x: -100, y: -100 });
  const [isCursorHovered, setIsCursorHovered] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    if (initialProduct) {
      setSelectedProduct(initialProduct);
    }
  }, [initialProduct]);

  // Sync color hex from selected product
  useEffect(() => {
    if (selectedProduct) {
      const colors = selectedProduct.colors || selectedProduct.colours || [];
      if (colors.length > 0 && colors[0].hex) {
        setSelectedColorHex(colors[0].hex);
      } else {
        setSelectedColorHex('#ffffff');
      }
    }
  }, [selectedProduct]);

  // Cursor movement tracking (Desktop only)
  useEffect(() => {
    const handleMouseMove = (e) => {
      setCursorPos({ x: e.clientX, y: e.clientY });
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  // Filter products for showroom
  const showroomItems = useMemo(() => {
    return products.slice(0, 12);
  }, [products]);

  // -------------------------------------------------------------
  // THREE.JS 3D SCENE & ARCHETYPE CONTROLLER
  // -------------------------------------------------------------
  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    let animId;
    const width = container.clientWidth || window.innerWidth;
    const height = container.clientHeight || window.innerHeight;

    // 1. Scene
    const scene = new THREE.Scene();

    // 2. Camera
    const camera = new THREE.PerspectiveCamera(44, width / height, 0.1, 100);
    camera.position.set(0, 0.6, 3.8);

    // 3. Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'high-performance' });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.8));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    // Dynamic Elements container
    const stageGroup = new THREE.Group();
    scene.add(stageGroup);

    // Materials / Color References
    const garmentColor = new THREE.Color(selectedColorHex);
    const bodyScaleFactor = bodyShape === 'slim' ? 0.88 : bodyShape === 'broad' ? 1.15 : 1.0;

    // =========================================================
    // ARCHETYPE 1: WARM PEACH STUDIO (#FCEFED)
    // =========================================================
    if (roomArchetype === 'peach') {
      scene.background = new THREE.Color(0xFCEFED);
      scene.fog = new THREE.Fog(0xFCEFED, 6, 20);

      // Ambient Peach Light
      const ambientLight = new THREE.AmbientLight(0xFFE6E2, 0.85);
      scene.add(ambientLight);

      // Key Directional Light
      const dirLight = new THREE.DirectionalLight(0xFFF9F7, 1.4);
      dirLight.position.set(5, 10, 5);
      dirLight.castShadow = true;
      dirLight.shadow.mapSize.set(1024, 1024);
      dirLight.shadow.bias = -0.0005;
      scene.add(dirLight);

      // Floor
      const floorGeo = new THREE.PlaneGeometry(50, 50);
      const floorMat = new THREE.MeshStandardMaterial({ color: 0xF4EAE7, roughness: 0.22, metalness: 0.06 });
      const floor = new THREE.Mesh(floorGeo, floorMat);
      floor.rotation.x = -Math.PI / 2;
      floor.position.y = -1.5;
      floor.receiveShadow = true;
      scene.add(floor);

      // Glowing Acrylic Lightbox Pedestal
      const pedestalGeo = new THREE.BoxGeometry(1.6, 0.2, 0.9);
      const pedestalMat = new THREE.MeshPhysicalMaterial({
        color: 0xFFA07A,
        emissive: 0xFF7043,
        emissiveIntensity: 2.6,
        roughness: 0.18,
        transmission: 0.4
      });
      const pedestal = new THREE.Mesh(pedestalGeo, pedestalMat);
      pedestal.position.set(0, -1.4, 0);
      pedestal.castShadow = true;
      pedestal.receiveShadow = true;
      stageGroup.add(pedestal);

      // Peach Underglow Point Light
      const underglow = new THREE.PointLight(0xFF8A65, 3.2, 3.5);
      underglow.position.set(0, -1.2, 0);
      stageGroup.add(underglow);

      // Ceiling Hanging Wire & Bar
      const wireGeo = new THREE.CylinderGeometry(0.006, 0.006, 3.5, 8);
      const wireMat = new THREE.MeshStandardMaterial({ color: 0x1E232A, metalness: 0.8, roughness: 0.2 });
      const wireL = new THREE.Mesh(wireGeo, wireMat);
      wireL.position.set(-0.35, 1.8, 0);
      const wireR = new THREE.Mesh(wireGeo, wireMat);
      wireR.position.set(0.35, 1.8, 0);
      stageGroup.add(wireL, wireR);
    }

    // =========================================================
    // ARCHETYPE 2: FLOATING ROSE PETAL VORTEX (IMAGE 1)
    // =========================================================
    let petalParticles = [];
    if (roomArchetype === 'petal_vortex') {
      scene.background = new THREE.Color(0x0E1015);
      scene.fog = new THREE.Fog(0x0E1015, 4, 18);

      // Dim ambient
      const ambientLight = new THREE.AmbientLight(0x2A2E3D, 0.4);
      scene.add(ambientLight);

      // Dramatic Overhead Cone Spotlight
      const spotLight = new THREE.SpotLight(0xFFFFFF, 3.8);
      spotLight.position.set(0, 7, 0);
      spotLight.angle = Math.PI / 6;
      spotLight.penumbra = 0.45;
      spotLight.castShadow = true;
      spotLight.shadow.mapSize.set(1024, 1024);
      scene.add(spotLight);

      // Polished dark concrete floor with specular contact reflection
      const floorGeo = new THREE.PlaneGeometry(50, 50);
      const floorMat = new THREE.MeshStandardMaterial({ color: 0x181A20, roughness: 0.16, metalness: 0.4 });
      const floor = new THREE.Mesh(floorGeo, floorMat);
      floor.rotation.x = -Math.PI / 2;
      floor.position.y = -1.5;
      floor.receiveShadow = true;
      scene.add(floor);

      // Create 80 Orbiting Rose Petals
      const petalGeo = new THREE.SphereGeometry(0.04, 8, 8);
      petalGeo.scale(1.2, 0.2, 1.6);
      const petalMat = new THREE.MeshStandardMaterial({ color: 0xE11D48, roughness: 0.6 });

      for (let i = 0; i < 80; i++) {
        const petal = new THREE.Mesh(petalGeo, petalMat);
        const theta = (i / 80) * Math.PI * 4;
        const radius = 0.5 + (i / 80) * 1.3;
        const y = -1.2 + (i / 80) * 2.4;
        petal.position.set(Math.cos(theta) * radius, y, Math.sin(theta) * radius);
        petal.rotation.set(Math.random() * Math.PI, Math.random() * Math.PI, Math.random() * Math.PI);
        petal.userData = { theta, radius, y, speed: 0.015 + Math.random() * 0.01 };
        stageGroup.add(petal);
        petalParticles.push(petal);
      }
    }

    // =========================================================
    // ARCHETYPE 3: CYBERPUNK GARAGE SHOWROOM (IMAGE 2)
    // =========================================================
    if (roomArchetype === 'cyber_garage') {
      scene.background = new THREE.Color(0x08090D);
      scene.fog = new THREE.Fog(0x08090D, 5, 20);

      const ambientLight = new THREE.AmbientLight(0x1E2230, 0.6);
      scene.add(ambientLight);

      // Neon Cyan Strip
      const neonCyan = new THREE.PointLight(0x00E5FF, 3.0, 8);
      neonCyan.position.set(-2.5, 3.0, 1.0);
      scene.add(neonCyan);

      // Neon Magenta Strip
      const neonMagenta = new THREE.PointLight(0xFF007F, 3.0, 8);
      neonMagenta.position.set(2.5, 3.0, 1.0);
      scene.add(neonMagenta);

      // Wet Asphalt Floor
      const floorGeo = new THREE.PlaneGeometry(50, 50);
      const floorMat = new THREE.MeshStandardMaterial({ color: 0x0F1116, roughness: 0.12, metalness: 0.75 });
      const floor = new THREE.Mesh(floorGeo, floorMat);
      floor.rotation.x = -Math.PI / 2;
      floor.position.y = -1.5;
      floor.receiveShadow = true;
      scene.add(floor);

      // Industrial Rolling Pipe Rack with 4 Caster Wheels
      const rackGroup = new THREE.Group();
      const pipeMat = new THREE.MeshStandardMaterial({ color: 0x22242B, metalness: 0.85, roughness: 0.25 });
      const casterMat = new THREE.MeshStandardMaterial({ color: 0x111215, roughness: 0.4 });

      // Horizontal Bar
      const topBar = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 2.2, 16), pipeMat);
      topBar.rotation.z = Math.PI / 2;
      topBar.position.y = 1.2;
      rackGroup.add(topBar);

      // Vertical Uprights
      const postL = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 2.6, 16), pipeMat);
      postL.position.set(-1.05, -0.1, 0);
      const postR = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 2.6, 16), pipeMat);
      postR.position.set(1.05, -0.1, 0);
      rackGroup.add(postL, postR);

      // Base Feet & Casters
      [-1.05, 1.05].forEach((x) => {
        const foot = new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.04, 0.7), pipeMat);
        foot.position.set(x, -1.4, 0);
        const wheelF = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.03, 16), casterMat);
        wheelF.rotation.z = Math.PI / 2;
        wheelF.position.set(x, -1.45, 0.3);
        const wheelB = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.03, 16), casterMat);
        wheelB.rotation.z = Math.PI / 2;
        wheelB.position.set(x, -1.45, -0.3);
        rackGroup.add(foot, wheelF, wheelB);
      });
      stageGroup.add(rackGroup);
    }

    // =========================================================
    // ARCHETYPE 4: MINIMALIST RAIL & CYCLORAMA (IMAGES 3 & 4)
    // =========================================================
    if (roomArchetype === 'minimalist_rail') {
      scene.background = new THREE.Color(0xF0F2F5);
      scene.fog = new THREE.Fog(0xF0F2F5, 6, 22);

      const ambientLight = new THREE.AmbientLight(0xFFFFFF, 0.9);
      scene.add(ambientLight);

      const keyLight = new THREE.DirectionalLight(0xFFFFFF, 1.2);
      keyLight.position.set(4, 8, 4);
      keyLight.castShadow = true;
      scene.add(keyLight);

      // Soft Cyclorama Floor
      const floorGeo = new THREE.PlaneGeometry(50, 50);
      const floorMat = new THREE.MeshStandardMaterial({ color: 0xE8EBF0, roughness: 0.35 });
      const floor = new THREE.Mesh(floorGeo, floorMat);
      floor.rotation.x = -Math.PI / 2;
      floor.position.y = -1.5;
      floor.receiveShadow = true;
      scene.add(floor);

      // Clean Minimalist Black Bar
      const railMat = new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.3 });
      const rail = new THREE.Mesh(new THREE.CylinderGeometry(0.015, 0.015, 2.8, 16), railMat);
      rail.rotation.z = Math.PI / 2;
      rail.position.set(0, 1.1, 0);
      stageGroup.add(rail);

      // Dual ceiling drop wires
      const wireMat = new THREE.MeshStandardMaterial({ color: 0x888888, metalness: 0.8 });
      const dropL = new THREE.Mesh(new THREE.CylinderGeometry(0.004, 0.004, 4, 8), wireMat);
      dropL.position.set(-1.2, 3.1, 0);
      const dropR = new THREE.Mesh(new THREE.CylinderGeometry(0.004, 0.004, 4, 8), wireMat);
      dropR.position.set(1.2, 3.1, 0);
      stageGroup.add(dropL, dropR);
    }

    // =========================================================
    // ARCHETYPE 5: DUAL MIRROR HALL (TRY-ON REFLECTION)
    // =========================================================
    let backMannequinGroup = null;
    if (roomArchetype === 'mirror_hall') {
      scene.background = new THREE.Color(0xF5F7FA);
      scene.fog = new THREE.Fog(0xF5F7FA, 6, 20);

      const ambientLight = new THREE.AmbientLight(0xFFFFFF, 0.85);
      scene.add(ambientLight);

      const keyLight = new THREE.DirectionalLight(0xFFFFFF, 1.3);
      keyLight.position.set(3, 9, 5);
      scene.add(keyLight);

      // Floor
      const floorGeo = new THREE.PlaneGeometry(50, 50);
      const floorMat = new THREE.MeshStandardMaterial({ color: 0xEDEFF2, roughness: 0.28 });
      const floor = new THREE.Mesh(floorGeo, floorMat);
      floor.rotation.x = -Math.PI / 2;
      floor.position.y = -1.5;
      floor.receiveShadow = true;
      scene.add(floor);

      // Tall Electric Blue Mirror Frame
      const frameMat = new THREE.MeshStandardMaterial({ color: 0x2F6BFF, metalness: 0.5, roughness: 0.2 });
      const mirrorFrame = new THREE.Mesh(new THREE.BoxGeometry(2.4, 3.2, 0.06), frameMat);
      mirrorFrame.position.set(0, 0.2, -0.2);

      // Mirror Glass Surface
      const glassMat = new THREE.MeshPhysicalMaterial({
        color: 0xE8F0FE,
        roughness: 0.04,
        metalness: 0.9,
        transmission: 0.65,
        transparent: true,
        opacity: 0.85
      });
      const glass = new THREE.Mesh(new THREE.PlaneGeometry(2.2, 3.0), glassMat);
      glass.position.set(0, 0.2, -0.16);
      scene.add(mirrorFrame, glass);

      // Reflected Duplicate behind the mirror glass (turned 180 deg)
      backMannequinGroup = new THREE.Group();
      backMannequinGroup.position.set(0, -0.2, -0.85);
      scene.add(backMannequinGroup);
    }

    // =========================================================
    // PROCEDURAL 3D APPAREL MESH BUILDER
    // =========================================================
    function createGarment(scaleX = 1.0) {
      const g = new THREE.Group();
      g.scale.set(scaleX, 1, 1);

      const mat = new THREE.MeshStandardMaterial({
        color: garmentColor,
        roughness: 0.65,
        metalness: 0.05
      });

      // Collar
      const collar = new THREE.Mesh(new THREE.TorusGeometry(0.18, 0.04, 16, 32), mat);
      collar.rotation.x = Math.PI / 2;
      collar.position.set(0, 0.6, 0);

      // Main Torso
      const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.42, 0.46, 0.95, 32), mat);
      torso.position.set(0, 0.08, 0);
      torso.castShadow = true;

      // Left Sleeve
      const sleeveL = new THREE.Mesh(new THREE.CylinderGeometry(0.17, 0.19, 0.44, 24), mat);
      sleeveL.rotation.z = 0.45;
      sleeveL.position.set(-0.52, 0.38, 0);
      sleeveL.castShadow = true;

      // Right Sleeve
      const sleeveR = new THREE.Mesh(new THREE.CylinderGeometry(0.17, 0.19, 0.44, 24), mat);
      sleeveR.rotation.z = -0.45;
      sleeveR.position.set(0.52, 0.38, 0);
      sleeveR.castShadow = true;

      // Hood / Cowl
      const hood = new THREE.Mesh(
        new THREE.SphereGeometry(0.28, 24, 24, 0, Math.PI * 2, 0, Math.PI * 0.7),
        mat
      );
      hood.position.set(0, 0.65, -0.08);

      g.add(collar, torso, sleeveL, sleeveR, hood);
      return g;
    }

    const frontGarment = createGarment(bodyScaleFactor);
    frontGarment.position.set(0, -0.2, 0);
    stageGroup.add(frontGarment);

    if (backMannequinGroup) {
      const backGarment = createGarment(bodyScaleFactor);
      backMannequinGroup.add(backGarment);
    }

    // =========================================================
    // INTERACTIVE ROTATION & ANIMATION LOOP
    // =========================================================
    let currentRotation = 0;
    let targetRotation = 0;
    let prevMouseX = 0;

    const onPointerDown = (e) => {
      setIsDragging(true);
      prevMouseX = e.clientX;
    };

    const onPointerMove = (e) => {
      if (prevMouseX !== 0 && (e.buttons === 1 || e.type === 'touchmove')) {
        const clientX = e.clientX || (e.touches && e.touches[0].clientX) || 0;
        const delta = clientX - prevMouseX;
        targetRotation += delta * 0.012;
        prevMouseX = clientX;
      }
    };

    const onPointerUp = () => {
      setIsDragging(false);
      prevMouseX = 0;
    };

    const dom = renderer.domElement;
    dom.addEventListener('mousedown', onPointerDown);
    dom.addEventListener('mousemove', onPointerMove);
    window.addEventListener('mouseup', onPointerUp);

    // Render loop
    const clock = new THREE.Clock();
    const animate = () => {
      animId = requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();

      // Smooth Rotation Lerp
      currentRotation = THREE.MathUtils.lerp(currentRotation, targetRotation, 0.08);
      stageGroup.rotation.y = currentRotation;

      // Inverted Back Reflection (θ_ref = π - θ)
      if (backMannequinGroup) {
        backMannequinGroup.rotation.y = Math.PI - currentRotation;
      }

      // Gentle idle sway (unless dragging)
      if (!isDragging && roomArchetype !== 'petal_vortex') {
        targetRotation += 0.003;
      }

      // Petal Vortex Particle Animation
      if (petalParticles.length > 0) {
        petalParticles.forEach((petal) => {
          petal.userData.theta += petal.userData.speed;
          petal.position.x = Math.cos(petal.userData.theta) * petal.userData.radius;
          petal.position.z = Math.sin(petal.userData.theta) * petal.userData.radius;
          petal.position.y += Math.sin(elapsed * 2 + petal.userData.radius) * 0.002;
          petal.rotation.x += 0.01;
          petal.rotation.y += 0.015;
        });
      }

      renderer.render(scene, camera);
    };
    animate();

    // Resize Handler
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
  }, [roomArchetype, bodyShape, selectedColorHex]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-md animate-fade-in select-none">
      {/* Custom Cursor (8px dot + 30px ring expanding to 54px with #2F6BFF hover) */}
      <div
        className="drape-cursor-dot hidden md:block"
        style={{ left: cursorPos.x, top: cursorPos.y }}
      />
      <div
        className={`drape-cursor-ring hidden md:block ${isCursorHovered ? 'is-hovered' : ''}`}
        style={{ left: cursorPos.x, top: cursorPos.y }}
      />

      <div className="relative w-full h-full max-w-7xl max-h-[96vh] rounded-3xl overflow-hidden shadow-2xl flex flex-col bg-[#FCEFED] border border-white/20">
        
        {/* Minimalist Topbar */}
        <header className="absolute top-0 left-0 right-0 z-30 flex items-center justify-between px-6 py-4 pointer-events-none">
          <div className="flex items-center gap-3 pointer-events-auto">
            <button
              onClick={onClose}
              onMouseEnter={() => setIsCursorHovered(true)}
              onMouseLeave={() => setIsCursorHovered(false)}
              className="flex items-center justify-center w-10 h-10 rounded-full bg-white shadow-md text-[#111111] hover:text-[#2F6BFF] transition border border-[#C9CED8]/40"
              aria-label="Back to store"
            >
              <Icon name="arrow-left" size={18} />
            </button>
            <div className="flex items-center gap-2">
              <span className="text-xl font-bold tracking-tight text-[#111111]">drape<span className="text-[#2F6BFF]">.</span></span>
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-[#111111] text-white">3D Spatial Showroom</span>
            </div>
          </div>

          {/* Breadcrumb info pill */}
          <div className="hidden sm:flex items-center gap-2 text-xs text-[#6B7380] font-semibold bg-white/80 backdrop-blur-md px-4 py-2 rounded-full shadow-sm border border-[#C9CED8]/40 pointer-events-auto">
            <span>Showroom</span>
            <span>/</span>
            <span className="capitalize text-[#111111]">
              {roomArchetype === 'peach' ? 'Warm Peach Studio' :
               roomArchetype === 'petal_vortex' ? 'Petal Vortex Gallery' :
               roomArchetype === 'cyber_garage' ? 'Cyber Garage Rack' :
               roomArchetype === 'minimalist_rail' ? 'Minimalist Rail' : 'Dual Mirror Hall'}
            </span>
          </div>

          {/* Quick Action Button */}
          <div className="flex items-center gap-3 pointer-events-auto">
            {selectedProduct && (
              <button
                onClick={() => {
                  if (onOpenProduct) onOpenProduct(selectedProduct);
                  else if (selectedProduct.productUrl) window.open(getProductClickUrl(selectedProduct), '_blank');
                }}
                onMouseEnter={() => setIsCursorHovered(true)}
                onMouseLeave={() => setIsCursorHovered(false)}
                className="flex items-center gap-2 bg-[#111111] text-white px-5 py-2.5 rounded-full shadow-md hover:bg-[#2F6BFF] transition text-xs font-bold"
              >
                <span>Instant Order</span>
                <Icon name="bag" size={14} />
              </button>
            )}
            <button
              onClick={onClose}
              onMouseEnter={() => setIsCursorHovered(true)}
              onMouseLeave={() => setIsCursorHovered(false)}
              className="flex items-center justify-center w-10 h-10 rounded-full bg-white shadow-md text-[#111111] hover:text-[#E11D48] transition border border-[#C9CED8]/40"
              aria-label="Close"
            >
              <Icon name="close" size={18} />
            </button>
          </div>
        </header>

        {/* 3D Viewport Canvas Container */}
        <div ref={mountRef} className="w-full h-full cursor-grab active:cursor-grabbing" />

        {/* Top Archetype Badge (Centered) */}
        <div className="absolute top-16 left-1/2 -translate-x-1/2 z-20 pointer-events-none text-center">
          <p className="text-[11px] font-bold uppercase tracking-widest text-[#6B7380] drop-shadow-sm">
            {roomArchetype === 'petal_vortex' ? 'ENGINEERED FOR PRESENCE · DESIGNED FOR PEACE' :
             roomArchetype === 'cyber_garage' ? 'DESIGN FOR SALE · INDUSTRIAL CARGO SHOWROOM' :
             roomArchetype === 'peach' ? 'WARM PEACH AMBIENT · GLOWING LIGHTBOX PEDESTAL' :
             roomArchetype === 'minimalist_rail' ? 'NABR STUDIOS · MINIMALIST CEILING SUSPENSION' :
             'DUAL MANNEQUIN STAGE · 180° BACK REFLECTION'}
          </p>
        </div>

        {/* Floating Bottom Card Carousel (Min-width 185px, 20px radius) */}
        <div className="drape-carousel-tray">
          <div className="drape-carousel-inner">
            {showroomItems.map((item) => {
              const isSelected = selectedProduct?.id === item.id;
              const colorHex = item.colors?.[0]?.hex || item.colours?.[0]?.hex || '#111111';
              const colorName = item.colors?.[0]?.name || item.colours?.[0]?.name || 'Classic';

              return (
                <div
                  key={item.id}
                  onClick={() => setSelectedProduct(item)}
                  onMouseEnter={() => setIsCursorHovered(true)}
                  onMouseLeave={() => setIsCursorHovered(false)}
                  className={`drape-product-card ${isSelected ? 'is-active' : ''}`}
                >
                  <div className="flex items-center gap-2 mb-1.5">
                    <span
                      className="w-3.5 h-3.5 rounded-full border border-black/10 shrink-0"
                      style={{ backgroundColor: colorHex }}
                    />
                    <span className="text-[11px] text-[#6B7380] font-medium truncate">{colorName}</span>
                  </div>
                  <h4 className="font-bold text-[#111111] text-xs tracking-tight line-clamp-1">
                    {item.title || item.name}
                  </h4>
                  <div className="flex items-center justify-between mt-2 pt-1 border-t border-[#C9CED8]/30">
                    <span className="text-xs font-bold text-[#111111]">{money(item.price)}</span>
                    <span className="text-[10px] font-semibold text-[#2F6BFF]">Inspect 3D</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Bottom Horizontal Category Switcher Pills */}
        <div className="drape-category-bar">
          <div className="drape-category-container">
            {[
              { id: 'peach', label: '🌸 Peach Studio' },
              { id: 'petal_vortex', label: '🌹 Petal Vortex' },
              { id: 'cyber_garage', label: '⚡ Cyber Garage' },
              { id: 'minimalist_rail', label: '📐 Minimalist Rail' },
              { id: 'mirror_hall', label: '🪞 Mirror Hall' }
            ].map((arch) => (
              <button
                key={arch.id}
                onClick={() => setRoomArchetype(arch.id)}
                onMouseEnter={() => setIsCursorHovered(true)}
                onMouseLeave={() => setIsCursorHovered(false)}
                className={`drape-category-pill ${roomArchetype === arch.id ? 'is-active' : ''}`}
              >
                {arch.label}
              </button>
            ))}

            {/* Body shape scaler (Only in Mirror Hall) */}
            {roomArchetype === 'mirror_hall' && (
              <div className="flex items-center gap-1 pl-2 border-l border-[#C9CED8]/60">
                {['slim', 'regular', 'broad'].map((shape) => (
                  <button
                    key={shape}
                    onClick={() => setBodyShape(shape)}
                    onMouseEnter={() => setIsCursorHovered(true)}
                    onMouseLeave={() => setIsCursorHovered(false)}
                    className={`px-3 py-1 rounded-full text-[11px] font-bold capitalize transition ${
                      bodyShape === shape ? 'bg-[#2F6BFF] text-white shadow-sm' : 'bg-transparent text-[#6B7380] hover:text-[#111111]'
                    }`}
                  >
                    {shape}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
