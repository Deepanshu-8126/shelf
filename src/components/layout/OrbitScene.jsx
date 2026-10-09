import React, { useEffect, useRef } from 'react';

export default function OrbitScene() {
  const mountRef = useRef(null);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return undefined;

    let disposed = false;
    let renderer;
    let observer;
    let scene;
    let animationId = 0;

    const createScene = async () => {
      const THREE = await import('three').catch(() => null);
      if (!THREE || disposed) return;

      try {
        renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
      } catch {
        return;
      }

      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.8));
      renderer.setClearColor(0x000000, 0);
      renderer.outputColorSpace = THREE.SRGBColorSpace;
      mount.appendChild(renderer.domElement);

      scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 60);
      camera.position.set(0, 0, 5.4);

      scene.add(new THREE.AmbientLight(0xe8f4d5, 1.5));
      const key = new THREE.PointLight(0xe8ffb2, 3.2, 18);
      key.position.set(2.4, 2.8, 3.8);
      scene.add(key);
      const fill = new THREE.PointLight(0x96bce0, 2.1, 18);
      fill.position.set(-3, -1.3, 2);
      scene.add(fill);

      const sculpture = new THREE.Group();
      scene.add(sculpture);

      const coreGeometry = new THREE.IcosahedronGeometry(0.93, 2);
      const coreMaterial = new THREE.MeshPhysicalMaterial({
        color: 0xc9ed78,
        roughness: 0.26,
        metalness: 0.17,
        clearcoat: 0.9,
        clearcoatRoughness: 0.19,
        flatShading: true,
      });
      const core = new THREE.Mesh(coreGeometry, coreMaterial);
      sculpture.add(core);

      const innerGeometry = new THREE.IcosahedronGeometry(0.72, 1);
      const innerMaterial = new THREE.MeshBasicMaterial({
        color: 0xf0ffd3,
        wireframe: true,
        transparent: true,
        opacity: 0.25,
      });
      const innerWire = new THREE.Mesh(innerGeometry, innerMaterial);
      sculpture.add(innerWire);

      const ringMaterial = new THREE.MeshStandardMaterial({
        color: 0xe7f7c1,
        metalness: 0.74,
        roughness: 0.22,
        transparent: true,
        opacity: 0.78,
      });
      const ring = new THREE.Mesh(new THREE.TorusGeometry(1.42, 0.018, 12, 140), ringMaterial);
      ring.rotation.set(1.03, 0.22, 0.2);
      sculpture.add(ring);

      const secondRing = new THREE.Mesh(
        new THREE.TorusGeometry(1.64, 0.012, 10, 140),
        new THREE.MeshStandardMaterial({ color: 0xaed46e, metalness: 0.5, roughness: 0.4, transparent: true, opacity: 0.42 }),
      );
      secondRing.rotation.set(0.36, 1.08, -0.38);
      sculpture.add(secondRing);

      const beadMaterial = new THREE.MeshStandardMaterial({ color: 0xffd59d, metalness: 0.4, roughness: 0.28 });
      const beadPositions = [
        [1.48, 0.38, 0.2, 0.09],
        [-1.31, -0.53, 0.34, 0.065],
        [0.32, 1.45, -0.12, 0.055],
      ];
      const beads = beadPositions.map(([x, y, z, radius]) => {
        const bead = new THREE.Mesh(new THREE.SphereGeometry(radius, 16, 16), beadMaterial);
        bead.position.set(x, y, z);
        sculpture.add(bead);
        return bead;
      });

      const resize = () => {
        const width = Math.max(1, mount.clientWidth);
        const height = Math.max(1, mount.clientHeight);
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        renderer.setSize(width, height, false);
      };
      observer = new ResizeObserver(resize);
      observer.observe(mount);
      resize();

      let frame = 0;
      const animate = () => {
        if (disposed) return;
        animationId = window.requestAnimationFrame(animate);
        frame += 0.006;
        sculpture.rotation.y = Math.sin(frame * 0.6) * 0.3;
        sculpture.rotation.x = Math.sin(frame * 0.42) * 0.07;
        core.rotation.y += 0.0032;
        core.rotation.x += 0.0011;
        innerWire.rotation.y -= 0.0042;
        ring.rotation.z += 0.0018;
        secondRing.rotation.y += 0.0015;
        beads.forEach((bead, index) => {
          bead.position.y += Math.sin(frame * 1.2 + index) * 0.0009;
        });
        renderer.render(scene, camera);
      };
      animate();
    };

    createScene();

    return () => {
      disposed = true;
      window.cancelAnimationFrame(animationId);
      observer?.disconnect();
      scene?.traverse((item) => {
        if (item.geometry) item.geometry.dispose();
        if (item.material) {
          if (Array.isArray(item.material)) item.material.forEach((material) => material.dispose());
          else item.material.dispose();
        }
      });
      renderer?.dispose();
      if (renderer?.domElement.parentNode === mount) mount.removeChild(renderer.domElement);
    };
  }, []);

  return <div className="orbit-scene" ref={mountRef} aria-hidden="true" />;
}
