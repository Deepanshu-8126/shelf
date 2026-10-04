import React, { useState, useEffect, useRef, useMemo } from 'react';
import Icon from './Icon.jsx';
import { cleanDisplayTitle } from './ProductCard.jsx';

function money(v) {
  return `₹${Number(v || 0).toLocaleString('en-IN')}`;
}

const EDITORIAL_STYLES = [
  {
    id: 'vogue',
    name: 'Vogue India Studio',
    icon: '🌟',
    desc: 'Softbox studio lighting, neutral greige canvas, high-fashion poise',
    buildPrompt: (title, fabric) =>
      `Photorealistic high-fashion Vogue editorial of an adult Indian female model wearing ${title} (${fabric}). Studio setting with neutral warm-greige seamless backdrop, 50mm f/1.8 portrait lens, soft diffused softbox lighting from camera-left, gentle fill, natural skin micro-pores, authentic fabric texture and exact drape of the outfit. 8K resolution, zero CGI artifacts, photorealism.`
  },
  {
    id: 'streetwear',
    name: 'Urban Streetwear',
    icon: '🏙️',
    desc: 'Natural daylight, cinematic street lookbook, relaxed Gen-Z posture',
    buildPrompt: (title, fabric) =>
      `Cinematic urban streetwear lookbook of an adult model wearing ${title} (${fabric}). Outdoor architectural city setting with natural daylight, 50mm lens perspective, relaxed modern posture, authentic fabric seams, high-fashion street aesthetics, photorealistic, 8K.`
  },
  {
    id: 'royal',
    name: 'Royal Heritage',
    icon: '👑',
    desc: 'Grand architectural courtyard, warm golden hour, regal drape',
    buildPrompt: (title, fabric) =>
      `Regal festive Indian fashion campaign of an adult female model wearing ${title} (${fabric}). Grand royal palace courtyard backdrop, soft golden hour lighting, authentic Indian jewellery and styling, elegant drape, 8K ultra-detailed fashion photography.`
  },
  {
    id: 'minimalist',
    name: 'Minimalist Aesthetic',
    icon: '🌸',
    desc: 'Travertine pedestal, soft ambient light, warm muted tone',
    buildPrompt: (title, fabric) =>
      `Minimalist contemporary fashion campaign of an adult model wearing ${title} (${fabric}). Clean travertine pedestal backdrop, soft directional morning window illumination, natural relaxed poise, authentic fabric texture and silhouette, editorial lookbook.`
  }
];

const INITIAL_PHOTOS = [
  {
    id: 'photo-1',
    title: 'Classic Wine Red Banarasi Silk Saree',
    price: '₹551',
    category: 'Ethnic Regal & Heritage Drape',
    engine: 'LM Arena (FLUX Tier 1)',
    duration: '14.3s',
    src: '/studio_media/photos/ARENA_FAST_1791066182_classic_wine_red.jpg',
    date: 'Recent Render'
  },
  {
    id: 'photo-2',
    title: 'Burgundy Lace Bodycon Maxi Evening Dress',
    price: '₹599',
    category: 'Evening Luxury & Cocktail',
    engine: 'Google Flow Studio',
    duration: '18.2s',
    src: '/studio_media/photos/FLOW_EDITORIAL_1791042558_burgundy_lace_b.jpg',
    date: 'Recent Render'
  },
  {
    id: 'photo-3',
    title: 'Royal Heritage Temple Saree Lookbook',
    price: '₹649',
    category: 'Ethnic & Festive Regal',
    engine: 'Google Flow AI',
    duration: '21.0s',
    src: '/studio_media/photos/GENUINE_GOOGLE_FLOW_SAREE_PHOTOSHOOT.jpg',
    date: 'Recent Render'
  },
  {
    id: 'photo-4',
    title: 'Comfy Designer Women Festive Kurti',
    price: '₹420',
    category: 'Casual Chic & Contemporary',
    engine: 'LM Arena Fast',
    duration: '12.8s',
    src: '/studio_media/photos/PIN_POST_10_comfy_designer_women.jpg',
    date: 'Recent Render'
  }
];

const INITIAL_VIDEOS = [
  {
    id: 'video-1',
    title: 'Affiliate Clean Flow Reel (9:16 Model Walk)',
    price: '₹551',
    duration: '0:06',
    src: '/studio_media/videos/AFFILIATE_CLEAN_FLOW_REEL_20261003_200342_MASTER.mp4'
  },
  {
    id: 'video-2',
    title: 'Kashmira Elegant Bodycon Maxi Reel',
    price: '₹620',
    duration: '0:08',
    src: '/studio_media/videos/AFFILIATE_KASHMIRA_ELEGANT_OUTFIT_(CLD_20261003_210712_MASTER.mp4'
  },
  {
    id: 'video-3',
    title: 'Trendy Halter Neck Pink Top Reel',
    price: '₹399',
    duration: '0:07',
    src: '/studio_media/videos/AFFILIATE_TRENDY_HALTER_NECK_PINK_TOP_20261003_210947_MASTER.mp4'
  }
];

export default function AIMediaStudioView({
  products = [],
  onUpdateProduct,
  onToast = () => {}
}) {
  const [activeTab, setActiveTab] = useState('studio'); // 'studio' | 'gallery' | 'videos' | 'trends'
  const [selectedProductId, setSelectedProductId] = useState(() => products[0]?.id || '');
  const [selectedStyleId, setSelectedStyleId] = useState('vogue');
  const [selectedEngine, setSelectedEngine] = useState('arena'); // 'arena' | 'gemini' | 'cloudflare' | 'pexels'
  const [garmentSource, setGarmentSource] = useState('catalog'); // 'catalog' | 'custom'
  const [customImage, setCustomImage] = useState('');
  const [customTitle, setCustomTitle] = useState('');
  const [aspectRatio, setAspectRatio] = useState('4:5');
  const [customPrompt, setCustomPrompt] = useState('');
  const [isPromptCustomized, setIsPromptCustomized] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationStep, setGenerationStep] = useState(0);
  const [activeEditorialResult, setActiveEditorialResult] = useState(null);
  const [photosList, setPhotosList] = useState(INITIAL_PHOTOS);
  const [videosList] = useState(INITIAL_VIDEOS);
  const [showWatermark, setShowWatermark] = useState(false);
  const [pushingTelegram, setPushingTelegram] = useState(false);
  const timerRef = useRef(null);

  // Active selected product
  const activeProduct = useMemo(() => {
    return products.find((p) => String(p.id) === String(selectedProductId)) || products[0] || null;
  }, [products, selectedProductId]);

  const activeStyle = useMemo(() => {
    return EDITORIAL_STYLES.find((s) => s.id === selectedStyleId) || EDITORIAL_STYLES[0];
  }, [selectedStyleId]);

  // Sync auto prompt when product or style changes (if user hasn't typed custom)
  useEffect(() => {
    if (!isPromptCustomized) {
      const title = garmentSource === 'custom'
        ? (customTitle || 'Designer Festive Outfit')
        : cleanDisplayTitle(activeProduct?.title || 'Festive Indian Outfit');
      const fabric = garmentSource === 'custom'
        ? 'Silk'
        : (activeProduct?.fabric || activeProduct?.category || 'Cotton Silk');
      setCustomPrompt(activeStyle.buildPrompt(title, fabric));
    }
  }, [activeProduct, activeStyle, isPromptCustomized, garmentSource, customTitle]);

  // Reset active editorial when user switches products
  const handleProductChange = (prodId) => {
    setSelectedProductId(prodId);
    setActiveEditorialResult(null);
    setIsPromptCustomized(false);
  };

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      setCustomImage(event.target.result);
      if (!customTitle) {
        const nameClean = file.name.replace(/\.[^/.]+$/, '').replace(/[_-]/g, ' ');
        setCustomTitle(nameClean);
      }
      setActiveEditorialResult(null);
      onToast('📸 Outfit photo loaded! Ready to enhance via AI.');
    };
    reader.readAsDataURL(file);
  };

  const handleGenerate = async () => {
    const isCustom = garmentSource === 'custom';
    const effectiveImage = isCustom ? customImage : activeProduct?.image;
    const effectiveTitle = isCustom ? (customTitle || 'Designer Festive Outfit') : cleanDisplayTitle(activeProduct?.title || 'Festive Outfit');
    const effectivePrice = isCustom ? '₹699' : (activeProduct?.price || '₹699');
    const effectiveFabric = isCustom ? 'Silk' : (activeProduct?.fabric || activeProduct?.category || 'Silk');

    if (!effectiveImage && !activeProduct) {
      onToast('Please select a product or upload an outfit photo first.');
      return;
    }

    setIsGenerating(true);
    setGenerationStep(1);
    setActiveEditorialResult(null);

    let currentStep = 1;
    timerRef.current = setInterval(() => {
      currentStep++;
      if (currentStep <= 4) {
        setGenerationStep(currentStep);
      }
    }, 2800);

    try {
      const res = await fetch('/api/studio/generate-photo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: effectiveTitle,
          price: effectivePrice,
          engine: selectedEngine,
          prompt: customPrompt,
          aspect_ratio: aspectRatio,
          fabric: effectiveFabric,
          image_url: effectiveImage,
          style_preset: selectedStyleId
        })
      });

      const data = await res.json();
      if (timerRef.current) clearInterval(timerRef.current);

      if (data && data.success && data.src) {
        const newPhoto = {
          id: `render-${Date.now()}`,
          title: effectiveTitle,
          price: money(effectivePrice),
          category: activeProduct?.category || 'Editorial Lookbook',
          engine: data.engine || (selectedEngine === 'arena' ? 'LM Arena (FLUX Tier 1)' : 'Google AI Studio'),
          duration: data.duration || '12.4s',
          src: data.src,
          prompt: data.prompt || customPrompt,
          reference_image: effectiveImage,
          garment_analyzed: data.garment_analyzed || false,
          date: 'Just now'
        };

        setActiveEditorialResult(newPhoto);
        setPhotosList((prev) => [newPhoto, ...prev]);
        onToast(data.garment_analyzed
          ? '✨ Garment preserved & editorial rendered via LM Arena + Gemini Vision!'
          : '✨ High-fashion editorial photoshoot rendered successfully!');
      } else {
        onToast('⚠️ Could not complete render. Server returned error.');
      }
    } catch (err) {
      if (timerRef.current) clearInterval(timerRef.current);
      onToast('⚠️ Photoshoot error: ' + err.message);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleApplyToStorefront = async () => {
    if (!activeEditorialResult || !activeProduct) return;
    await onUpdateProduct?.(activeProduct.id, { image: activeEditorialResult.src });
    onToast(`✨ Set as Storefront Cover for "${cleanDisplayTitle(activeProduct.title).slice(0, 25)}"`);
  };

  const handleApplyToWishlink = async () => {
    if (!activeEditorialResult || !activeProduct) return;
    await onUpdateProduct?.(activeProduct.id, { wishlink_image: activeEditorialResult.src });
    onToast(`🌸 Set as Aesthetic Look for Wishlink Bio Haul!`);
  };

  const handlePushTelegram = async () => {
    if (!activeEditorialResult) return;
    setPushingTelegram(true);
    try {
      const res = await fetch('/api/studio/push-telegram', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: activeEditorialResult.title,
          image_url: activeEditorialResult.src,
          price: activeEditorialResult.price,
          category: activeEditorialResult.category
        })
      });
      const data = await res.json();
      if (data.success) {
        onToast('📲 Successfully pushed to Telegram Bot!');
      } else {
        onToast('⚠️ Telegram push: ' + (data.error || 'Check bot credentials'));
      }
    } catch (e) {
      onToast('⚠️ Telegram push failed: ' + e.message);
    } finally {
      setPushingTelegram(false);
    }
  };

  return (
    <div style={{ maxWidth: '1440px', margin: '0 auto', padding: '24px 20px' }}>
      {/* ── Header ── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '14px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 style={{ fontSize: '24px', fontWeight: 800, color: 'var(--ink)' }}>
              🎨 AI Media Studio &amp; Photoshoot Lab
            </h1>
            <span style={{ fontSize: '11.5px', background: 'rgba(34, 197, 94, 0.12)', color: '#16a34a', border: '1px solid rgba(34, 197, 94, 0.25)', padding: '3px 10px', borderRadius: '999px', fontWeight: 700 }}>
              🟢 FLUX / Gemini Active
            </span>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--muted)', marginTop: '4px' }}>
            Transform product photos into high-fashion editorials. Preserves exact garment silhouette and colors with zero anime/CGI drift.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span style={{ fontSize: '12px', background: 'var(--paper)', border: '1px solid var(--line)', padding: '6px 12px', borderRadius: '8px', fontWeight: 600, color: 'var(--ink)' }}>
            ⚡ Quota: <strong>500 / 500</strong> Free Daily Images
          </span>
        </div>
      </div>

      {/* ── Sub Navigation Tabs ── */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--line)', marginBottom: '24px' }}>
        <button
          type="button"
          onClick={() => setActiveTab('studio')}
          style={{
            padding: '12px 18px',
            fontSize: '13.5px',
            fontWeight: activeTab === 'studio' ? 800 : 600,
            color: activeTab === 'studio' ? 'var(--ink)' : 'var(--muted)',
            borderBottom: activeTab === 'studio' ? '2px solid var(--ink)' : '2px solid transparent',
            background: 'none',
            border: 'none',
            cursor: 'pointer'
          }}
        >
          📷 Photoshoot Studio
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('gallery')}
          style={{
            padding: '12px 18px',
            fontSize: '13.5px',
            fontWeight: activeTab === 'gallery' ? 800 : 600,
            color: activeTab === 'gallery' ? 'var(--ink)' : 'var(--muted)',
            borderBottom: activeTab === 'gallery' ? '2px solid var(--ink)' : '2px solid transparent',
            background: 'none',
            border: 'none',
            cursor: 'pointer'
          }}
        >
          🖼️ Generated Gallery ({photosList.length})
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('videos')}
          style={{
            padding: '12px 18px',
            fontSize: '13.5px',
            fontWeight: activeTab === 'videos' ? 800 : 600,
            color: activeTab === 'videos' ? 'var(--ink)' : 'var(--muted)',
            borderBottom: activeTab === 'videos' ? '2px solid var(--ink)' : '2px solid transparent',
            background: 'none',
            border: 'none',
            cursor: 'pointer'
          }}
        >
          🎬 Video Reels Hub ({videosList.length})
        </button>
      </div>

      {/* ── Tab 1: Photoshoot Studio (Clean 2-Column Canvas) ── */}
      {activeTab === 'studio' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(340px, 1fr) minmax(420px, 1.3fr)', gap: '24px', alignItems: 'start' }}>
          {/* Left Column: 3-Step Guided Controls */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Engine Selection Bar */}
            <div style={{ background: 'var(--paper)', border: '1px solid var(--line)', borderRadius: '16px', padding: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <span style={{ fontSize: '12px', fontWeight: 800, color: 'var(--ink)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  ⚡ AI Photoshoot Engine
                </span>
                <span style={{ fontSize: '11px', background: 'rgba(99, 102, 241, 0.1)', color: 'var(--primary)', padding: '2px 8px', borderRadius: '999px', fontWeight: 700 }}>
                  {selectedEngine === 'arena' ? 'LM Arena (FLUX) Active' : selectedEngine === 'gemini' ? 'Google AI Studio Active' : selectedEngine.toUpperCase()}
                </span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '6px' }}>
                {[
                  { id: 'arena', label: 'LM Arena', tag: 'FLUX Tier 1' },
                  { id: 'gemini', label: 'Google AI', tag: 'Gemini 3.8' },
                  { id: 'cloudflare', label: 'Cloudflare', tag: 'FLUX Schnell' },
                  { id: 'pexels', label: 'Pexels Stock', tag: 'Editorial' }
                ].map((eng) => (
                  <button
                    key={eng.id}
                    type="button"
                    onClick={() => setSelectedEngine(eng.id)}
                    style={{
                      padding: '8px 4px',
                      borderRadius: '10px',
                      border: selectedEngine === eng.id ? '2px solid var(--primary, #6366f1)' : '1px solid var(--line)',
                      background: selectedEngine === eng.id ? 'rgba(99, 102, 241, 0.08)' : 'var(--canvas)',
                      cursor: 'pointer',
                      textAlign: 'center'
                    }}
                  >
                    <strong style={{ fontSize: '11.5px', color: 'var(--ink)', display: 'block' }}>{eng.label}</strong>
                    <span style={{ fontSize: '9.5px', color: 'var(--muted)', display: 'block' }}>{eng.tag}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Step 1: Select Outfit or Upload Custom Photo */}
            <div style={{ background: 'var(--paper)', border: '1px solid var(--line)', borderRadius: '16px', padding: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <span style={{ background: 'var(--ink)', color: '#fff', width: '22px', height: '22px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 800 }}>
                  1
                </span>
                <h3 style={{ fontSize: '15px', fontWeight: 800, color: 'var(--ink)' }}>
                  Reference Garment Photo
                </h3>
              </div>

              {/* Source Switcher Tabs */}
              <div style={{ display: 'flex', gap: '8px', marginBottom: '14px' }}>
                <button
                  type="button"
                  onClick={() => setGarmentSource('catalog')}
                  style={{
                    flex: 1,
                    padding: '7px 10px',
                    borderRadius: '8px',
                    fontSize: '12px',
                    fontWeight: 700,
                    cursor: 'pointer',
                    border: garmentSource === 'catalog' ? '1px solid var(--ink)' : '1px solid var(--line)',
                    background: garmentSource === 'catalog' ? 'var(--ink)' : 'var(--canvas)',
                    color: garmentSource === 'catalog' ? '#fff' : 'var(--ink)'
                  }}
                >
                  🛍️ From Catalog
                </button>
                <button
                  type="button"
                  onClick={() => setGarmentSource('custom')}
                  style={{
                    flex: 1,
                    padding: '7px 10px',
                    borderRadius: '8px',
                    fontSize: '12px',
                    fontWeight: 700,
                    cursor: 'pointer',
                    border: garmentSource === 'custom' ? '1px solid var(--ink)' : '1px solid var(--line)',
                    background: garmentSource === 'custom' ? 'var(--ink)' : 'var(--canvas)',
                    color: garmentSource === 'custom' ? '#fff' : 'var(--ink)'
                  }}
                >
                  📤 Upload / Custom Photo
                </button>
              </div>

              {garmentSource === 'catalog' ? (
                <>
                  <select
                    value={selectedProductId}
                    onChange={(e) => handleProductChange(e.target.value)}
                    style={{ width: '100%', height: '42px', borderRadius: '10px', border: '1px solid var(--line)', padding: '0 12px', fontSize: '13px', background: 'var(--canvas)', color: 'var(--ink)', cursor: 'pointer', marginBottom: '12px' }}
                  >
                    {products.map((p) => (
                      <option key={p.id} value={p.id}>
                        {cleanDisplayTitle(p.title)} ({money(p.price)})
                      </option>
                    ))}
                  </select>

                  {activeProduct && (
                    <div style={{ display: 'flex', gap: '12px', alignItems: 'center', background: 'var(--canvas)', padding: '10px', borderRadius: '12px', border: '1px solid var(--line)' }}>
                      <img
                        src={activeProduct.image}
                        alt=""
                        style={{ width: '50px', height: '62px', objectFit: 'cover', borderRadius: '6px' }}
                        onError={(e) => { e.currentTarget.src = '/images/meesho-peach-short-kurti.webp'; }}
                      />
                      <div>
                        <strong style={{ fontSize: '13px', color: 'var(--ink)', display: 'block' }}>
                          {cleanDisplayTitle(activeProduct.title)}
                        </strong>
                        <div style={{ display: 'flex', gap: '8px', fontSize: '12px', marginTop: '2px' }}>
                          <span style={{ color: '#16a34a', fontWeight: 700 }}>{money(activeProduct.price)}</span>
                          <span style={{ color: 'var(--muted)' }}>·</span>
                          <span style={{ color: 'var(--muted)' }}>{activeProduct.category || 'Fashion'}</span>
                        </div>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <label style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', border: '2px dashed var(--line)', borderRadius: '12px', padding: '16px', background: 'var(--canvas)', cursor: 'pointer' }}>
                    <span style={{ fontSize: '24px', marginBottom: '4px' }}>📷</span>
                    <strong style={{ fontSize: '12.5px', color: 'var(--ink)' }}>Choose Image File</strong>
                    <span style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '2px' }}>PNG, JPG or WEBP from your device</span>
                    <input type="file" accept="image/*" onChange={handleFileUpload} style={{ display: 'none' }} />
                  </label>

                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <span style={{ fontSize: '11px', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>OR URL:</span>
                    <input
                      type="text"
                      placeholder="Paste Meesho / Pinterest Image URL..."
                      value={customImage.startsWith('data:') ? '' : customImage}
                      onChange={(e) => {
                        setCustomImage(e.target.value);
                        setActiveEditorialResult(null);
                      }}
                      style={{ flex: 1, height: '34px', borderRadius: '8px', border: '1px solid var(--line)', padding: '0 10px', fontSize: '12px', background: 'var(--canvas)', color: 'var(--ink)' }}
                    />
                  </div>

                  <input
                    type="text"
                    placeholder="Garment name (e.g. Burgundy Velvet Zari Saree)..."
                    value={customTitle}
                    onChange={(e) => setCustomTitle(e.target.value)}
                    style={{ width: '100%', height: '34px', borderRadius: '8px', border: '1px solid var(--line)', padding: '0 10px', fontSize: '12px', background: 'var(--canvas)', color: 'var(--ink)' }}
                  />

                  {customImage && (
                    <div style={{ display: 'flex', gap: '10px', alignItems: 'center', background: 'rgba(99, 102, 241, 0.06)', padding: '8px 12px', borderRadius: '10px', border: '1px solid rgba(99, 102, 241, 0.2)' }}>
                      <img src={customImage} alt="Custom Preview" style={{ width: '42px', height: '52px', objectFit: 'cover', borderRadius: '6px' }} />
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <span style={{ fontSize: '11.5px', fontWeight: 700, color: 'var(--ink)', display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {customTitle || 'Custom Outfit'}
                        </span>
                        <span style={{ fontSize: '11px', color: '#16a34a', fontWeight: 600 }}>
                          ✓ Garment Anchor Attached • Gemini Vision Ready
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Step 2: Editorial Atmosphere & Vibe */}
            <div style={{ background: 'var(--paper)', border: '1px solid var(--line)', borderRadius: '16px', padding: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <span style={{ background: 'var(--ink)', color: '#fff', width: '22px', height: '22px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 800 }}>
                  2
                </span>
                <h3 style={{ fontSize: '15px', fontWeight: 800, color: 'var(--ink)' }}>
                  Choose Editorial Style &amp; Atmosphere
                </h3>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '16px' }}>
                {EDITORIAL_STYLES.map((style) => {
                  const isSelected = selectedStyleId === style.id;
                  return (
                    <button
                      key={style.id}
                      type="button"
                      onClick={() => {
                        setSelectedStyleId(style.id);
                        setIsPromptCustomized(false);
                      }}
                      style={{
                        padding: '12px',
                        borderRadius: '12px',
                        border: isSelected ? '2px solid var(--primary, #6366f1)' : '1px solid var(--line)',
                        background: isSelected ? 'rgba(99, 102, 241, 0.06)' : 'var(--canvas)',
                        textAlign: 'left',
                        cursor: 'pointer'
                      }}
                    >
                      <div style={{ fontSize: '18px', marginBottom: '4px' }}>{style.icon}</div>
                      <strong style={{ fontSize: '13px', color: 'var(--ink)', display: 'block' }}>{style.name}</strong>
                      <span style={{ fontSize: '11px', color: 'var(--muted)', display: 'block', marginTop: '2px', lineHeight: 1.3 }}>
                        {style.desc}
                      </span>
                    </button>
                  );
                })}
              </div>

              {/* Aspect Ratio */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--ink)' }}>Aspect Ratio:</span>
                <div style={{ display: 'flex', gap: '6px' }}>
                  {['4:5', '9:16', '1:1'].map((r) => (
                    <button
                      key={r}
                      type="button"
                      onClick={() => setAspectRatio(r)}
                      style={{
                        padding: '5px 12px',
                        borderRadius: '8px',
                        fontSize: '12px',
                        fontWeight: 700,
                        cursor: 'pointer',
                        border: aspectRatio === r ? '1px solid var(--ink)' : '1px solid var(--line)',
                        background: aspectRatio === r ? 'var(--ink)' : 'var(--canvas)',
                        color: aspectRatio === r ? '#fff' : 'var(--ink)'
                      }}
                    >
                      {r}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Step 3: Vision Direction & Generate */}
            <div style={{ background: 'var(--paper)', border: '1px solid var(--line)', borderRadius: '16px', padding: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ background: 'var(--ink)', color: '#fff', width: '22px', height: '22px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 800 }}>
                    3
                  </span>
                  <h3 style={{ fontSize: '15px', fontWeight: 800, color: 'var(--ink)' }}>
                    Prompt &amp; Generation
                  </h3>
                </div>
                {isPromptCustomized && (
                  <button
                    type="button"
                    onClick={() => setIsPromptCustomized(false)}
                    style={{ background: 'none', border: 'none', color: 'var(--primary)', fontSize: '11.5px', fontWeight: 700, cursor: 'pointer' }}
                  >
                    Reset Prompt
                  </button>
                )}
              </div>

              <textarea
                rows={4}
                value={customPrompt}
                onChange={(e) => {
                  setCustomPrompt(e.target.value);
                  setIsPromptCustomized(true);
                }}
                placeholder="Editorial direction prompt..."
                style={{ width: '100%', borderRadius: '10px', border: '1px solid var(--line)', padding: '10px', fontSize: '12px', background: 'var(--canvas)', color: 'var(--ink)', resize: 'vertical', lineHeight: 1.4, marginBottom: '14px' }}
              />

              <button
                type="button"
                disabled={isGenerating || !activeProduct}
                onClick={handleGenerate}
                style={{
                  width: '100%',
                  height: '46px',
                  borderRadius: '12px',
                  background: isGenerating ? 'var(--muted)' : 'linear-gradient(135deg, #181b1e 0%, #374151 100%)',
                  color: '#fff',
                  fontSize: '13.5px',
                  fontWeight: 800,
                  border: 'none',
                  cursor: isGenerating ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  boxShadow: '0 4px 14px rgba(0, 0, 0, 0.15)'
                }}
              >
                {isGenerating ? (
                  <span>⚙️ Rendering Step {generationStep}/4...</span>
                ) : (
                  <>
                    <span>🚀</span> Generate Fashion Editorial
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Right Column: Visual Canvas & Real Output */}
          <div style={{ background: 'var(--paper)', border: '1px solid var(--line)', borderRadius: '20px', padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <h3 style={{ fontSize: '16px', fontWeight: 800, color: 'var(--ink)' }}>
                  Visual Output Comparison
                </h3>
                <p style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '2px' }}>
                  Side-by-side verification: Original product vs AI photoshoot.
                </p>
              </div>

              <label style={{ fontSize: '12px', color: 'var(--ink)', display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={showWatermark}
                  onChange={(e) => setShowWatermark(e.target.checked)}
                />
                <span>Brand watermark</span>
              </label>
            </div>

            {/* Side-by-Side Canvas */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
              {/* Original Listing Image */}
              <div style={{ background: 'var(--canvas)', borderRadius: '14px', border: '1px solid var(--line)', padding: '12px', textAlign: 'center' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Input Reference Garment
                  </span>
                  <span style={{ fontSize: '10px', background: 'rgba(99, 102, 241, 0.08)', color: 'var(--primary)', padding: '1px 6px', borderRadius: '4px', fontWeight: 700 }}>
                    RAW ANCHOR
                  </span>
                </div>
                <div style={{ height: '320px', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden', borderRadius: '10px', background: '#fff' }}>
                  <img
                    src={activeEditorialResult?.reference_image || (garmentSource === 'custom' ? customImage : activeProduct?.image) || '/images/meesho-peach-short-kurti.webp'}
                    alt="Original Reference"
                    style={{ maxHeight: '100%', maxWidth: '100%', objectFit: 'contain' }}
                    onError={(e) => { e.currentTarget.src = '/images/meesho-peach-short-kurti.webp'; }}
                  />
                </div>
                <div style={{ fontSize: '11.5px', color: 'var(--muted)', marginTop: '8px' }}>
                  {garmentSource === 'custom' ? (customTitle || 'Custom Outfit') : cleanDisplayTitle(activeProduct?.title)}
                </div>
              </div>

              {/* Generated Fashion Editorial */}
              <div style={{ background: 'var(--canvas)', borderRadius: '14px', border: activeEditorialResult ? '2px solid #16a34a' : '1px solid var(--line)', padding: '12px', textAlign: 'center', position: 'relative' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontSize: '11px', fontWeight: 700, color: activeEditorialResult ? '#16a34a' : 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    {activeEditorialResult ? '✓ Enhanced Editorial' : 'AI Rendered Result'}
                  </span>
                  {activeEditorialResult?.garment_analyzed && (
                    <span style={{ fontSize: '10px', background: 'rgba(34, 197, 94, 0.12)', color: '#16a34a', padding: '1px 6px', borderRadius: '4px', fontWeight: 700 }}>
                      VISION PRESERVED
                    </span>
                  )}
                </div>

                <div style={{ height: '320px', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden', borderRadius: '10px', background: '#fff', position: 'relative' }}>
                  {isGenerating ? (
                    <div style={{ textAlign: 'center', padding: '20px' }}>
                      <span style={{ fontSize: '32px', display: 'block', marginBottom: '10px' }}>⚙️</span>
                      <strong style={{ fontSize: '13.5px', color: 'var(--ink)', display: 'block' }}>
                        Rendering Editorial...
                      </strong>
                      <span style={{ fontSize: '11.5px', color: 'var(--muted)', marginTop: '4px', display: 'block' }}>
                        Step {generationStep}/4 · {selectedEngine === 'arena' ? 'LM Arena (FLUX Tier 1)' : 'Google AI Studio'}
                      </span>
                    </div>
                  ) : activeEditorialResult ? (
                    <>
                      <img
                        src={activeEditorialResult.src}
                        alt="Generated Editorial"
                        style={{ height: '100%', width: '100%', objectFit: 'cover' }}
                      />
                      {showWatermark && (
                        <div style={{ position: 'absolute', bottom: '10px', right: '10px', background: 'rgba(0, 0, 0, 0.65)', color: '#fff', padding: '3px 8px', borderRadius: '4px', fontSize: '10px', fontWeight: 700, letterSpacing: '0.05em' }}>
                          SHELF EDITORIAL
                        </div>
                      )}
                    </>
                  ) : (
                    <div style={{ textAlign: 'center', padding: '30px 20px', color: 'var(--muted)' }}>
                      <span style={{ fontSize: '36px', display: 'block', marginBottom: '8px' }}>✨</span>
                      <strong style={{ fontSize: '13.5px', color: 'var(--ink)', display: 'block' }}>
                        Ready to Enhance
                      </strong>
                      <p style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '4px', lineHeight: 1.4 }}>
                        Select or upload an outfit, then click "Generate Fashion Editorial" to render via LM Arena or Google AI.
                      </p>
                    </div>
                  )}
                </div>

                <div style={{ fontSize: '11.5px', color: activeEditorialResult ? '#16a34a' : 'var(--muted)', marginTop: '8px', fontWeight: activeEditorialResult ? 700 : 500 }}>
                  {activeEditorialResult ? `● ${activeEditorialResult.engine} (${activeEditorialResult.duration})` : `○ Engine: ${selectedEngine.toUpperCase()}`}
                </div>
              </div>
            </div>

            {/* 1-Click Action Bar for Generated Result */}
            {activeEditorialResult && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '10px', background: 'rgba(34, 197, 94, 0.08)', padding: '16px', borderRadius: '14px', border: '1px solid rgba(34, 197, 94, 0.25)' }}>
                <button
                  type="button"
                  onClick={handleApplyToStorefront}
                  className="button button-dark"
                  style={{ fontSize: '12px', padding: '10px 12px', fontWeight: 700 }}
                >
                  ✨ Storefront Cover
                </button>

                <button
                  type="button"
                  onClick={handleApplyToWishlink}
                  style={{ background: '#ec4899', color: '#fff', border: 'none', borderRadius: '10px', fontSize: '12px', padding: '10px 12px', fontWeight: 700, cursor: 'pointer' }}
                >
                  🌸 Wishlink Look
                </button>

                <button
                  type="button"
                  disabled={pushingTelegram}
                  onClick={handlePushTelegram}
                  style={{ background: '#0284c7', color: '#fff', border: 'none', borderRadius: '10px', fontSize: '12px', padding: '10px 12px', fontWeight: 700, cursor: 'pointer' }}
                >
                  {pushingTelegram ? 'Sending...' : '📲 Telegram'}
                </button>

                <a
                  href={activeEditorialResult.src}
                  download="shelf-editorial.jpg"
                  target="_blank"
                  rel="noreferrer"
                  style={{ background: 'var(--paper)', border: '1px solid var(--line)', color: 'var(--ink)', borderRadius: '10px', fontSize: '12px', padding: '10px 12px', fontWeight: 700, textDecoration: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                >
                  ⬇️ Download HD
                </a>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Tab 2: Generated Gallery ── */}
      {activeTab === 'gallery' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '18px' }}>
          {photosList.map((photo) => (
            <div key={photo.id} style={{ background: 'var(--paper)', borderRadius: '16px', border: '1px solid var(--line)', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
              <div style={{ height: '320px', overflow: 'hidden', background: 'var(--canvas)' }}>
                <img
                  src={photo.src}
                  alt={photo.title}
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  onError={(e) => { e.currentTarget.src = '/images/meesho-peach-short-kurti.webp'; }}
                />
              </div>

              <div style={{ padding: '14px', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                  <strong style={{ fontSize: '13.5px', color: 'var(--ink)', display: 'block' }}>
                    {photo.title}
                  </strong>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '6px' }}>
                    <span style={{ fontSize: '12px', color: '#16a34a', fontWeight: 700 }}>{photo.price}</span>
                    <span style={{ fontSize: '11px', color: 'var(--muted)' }}>{photo.date || 'Saved'}</span>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '8px', marginTop: '14px' }}>
                  <a
                    href={photo.src}
                    download
                    target="_blank"
                    rel="noreferrer"
                    style={{ flex: 1, background: 'var(--canvas)', border: '1px solid var(--line)', borderRadius: '8px', padding: '6px', fontSize: '11.5px', fontWeight: 700, textAlign: 'center', textDecoration: 'none', color: 'var(--ink)' }}
                  >
                    View HD ↗
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Tab 3: Video Reels Hub ── */}
      {activeTab === 'videos' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
          {videosList.map((video) => (
            <div key={video.id} style={{ background: 'var(--paper)', borderRadius: '16px', border: '1px solid var(--line)', overflow: 'hidden' }}>
              <div style={{ height: '420px', background: '#000', position: 'relative' }}>
                <video
                  src={video.src}
                  controls
                  playsInline
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
              </div>
              <div style={{ padding: '14px' }}>
                <strong style={{ fontSize: '13.5px', color: 'var(--ink)', display: 'block' }}>
                  {video.title}
                </strong>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '6px', fontSize: '12px', color: 'var(--muted)' }}>
                  <span>Duration: {video.duration}</span>
                  <span style={{ color: '#16a34a', fontWeight: 700 }}>{video.price}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
