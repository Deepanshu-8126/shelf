import React, { useState, useEffect, useRef, useMemo } from 'react';
import Icon from './Icon.jsx';
import { cleanDisplayTitle } from './ProductCard.jsx';
import './AIMediaStudioView.css';

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
     <div className="aim-studio-view">
       {/* ── Header ── */}
       <div className="studio-header">
         <div>
           <div className="header-left">
             <h1 className="studio-title">
               🎨 AI Media Studio &amp; Photoshoot Lab
             </h1>
             <span className="studio-badge">
               🟢 FLUX / Gemini Active
             </span>
           </div>
           <p className="studio-description">
             Transform product photos into high-fashion editorials. Preserves exact garment silhouette and colors with zero anime/CGI drift.
           </p>
         </div>

         <div className="header-right">
           <span className="active-products-badge">
             ⚡ Quota: <strong>500 / 500</strong> Free Daily Images
           </span>
         </div>
       </div>

       {/* ── Sub Navigation Tabs ── */}
       <div className="tab-container">
         <button
           type="button"
           className={`${activeTab === 'studio' ? 'tab-button active' : 'tab-button'}`}
           onClick={() => setActiveTab('studio')}
         >
           📷 Photoshoot Studio
         </button>

         <button
           type="button"
           className={`${activeTab === 'gallery' ? 'tab-button active' : 'tab-button'}`}
           onClick={() => setActiveTab('gallery')}
         >
           🖼️ Image Gallery ({photosList.length})
         </button>

         <button
           type="button"
           className={`${activeTab === 'videos' ? 'tab-button active' : 'tab-button'}`}
           onClick={() => setActiveTab('videos')}
         >
           🎬 Video Reels Hub ({videosList.length})
         </button>
       </div>

       {/* ── Tab 1: Photoshoot Studio (Clean 2-Column Canvas) ── */}
       {activeTab === 'studio' && (
         <div className="studio-main-content">
           {/* Left Column: 3-Step Guided Controls */}
           <div className="left-panel">
             {/* Engine Selection Bar */}
             <div className="preview-card">
               <div className="preview-header">
                 <span className="preview-label">
                   ⚡ AI Photoshoot Engine
                 </span>
                 <span className="preview-badge">
                   {selectedEngine === 'arena' ? 'LM Arena (FLUX) Active' : selectedEngine === 'gemini' ? 'Google AI Studio Active' : selectedEngine.toUpperCase()}
                 </span>
              </div>
               <div className="preview-grid">
                {[
                  { id: 'arena', label: 'LM Arena', tag: 'FLUX Tier 1' },
                  { id: 'gemini', label: 'Google AI', tag: 'Gemini 3.8' },
                  { id: 'cloudflare', label: 'Cloudflare', tag: 'FLUX Schnell' },
                  { id: 'pexels', label: 'Pexels Stock', tag: 'Editorial' }
             ].map((eng) => (
                   <button
                     key={eng.id}
                     type="button"
                     className={`${selectedEngine === eng.id ? 'engine-button active' : 'engine-button'}`}
                     onClick={() => setSelectedEngine(eng.id)}
                   >
                     <strong className="engine-label">{eng.label}</strong>
                     <span className="engine-tag">{eng.tag}</span>
                   </button>
                 ))}
              </div>
            </div>

             {/* Step 1: Select Outfit or Upload Custom Photo */}
             <div className="product-card">
               <div className="step-header">
                 <span className="step-number">
                   1
                 </span>
                 <h3 className="step-title">
                   Reference Garment Photo
                 </h3>
              </div>

               {/* Source Switcher Tabs */}
               <div className="source-tabs">
                 <button
                   type="button"
                   className={`${garmentSource === 'catalog' ? 'source-tab active' : 'source-tab'}`}
                   onClick={() => setGarmentSource('catalog')}
                 >
                   🛍️ From Catalog
                 </button>
                 <button
                   type="button"
                   className={`${garmentSource === 'custom' ? 'source-tab active' : 'source-tab'}`}
                   onClick={() => setGarmentSource('custom')}
                 >
                   📤 Upload / Custom Photo
                 </button>
               </div>

              {garmentSource === 'catalog' ? (
                <>
                   <select
                     value={selectedProductId}
                     onChange={(e) => handleProductChange(e.target.value)}
                     className="product-select"
                   >
                    {products.map((p) => (
                      <option key={p.id} value={p.id}>
                        {cleanDisplayTitle(p.title)} ({money(p.price)})
                      </option>
                    ))}
                  </select>

                  {activeProduct && (
                     <div className="product-preview-wrapper">
                       <img
                         src={activeProduct.image}
                         alt=""
                         className="product-thumbnail-img"
                         onError={(e) => { e.currentTarget.src = '/images/meesho-peach-short-kurti.webp'; }}
                       />
                       <div className="product-info">
                         <strong className="product-title">{cleanDisplayTitle(activeProduct.title)}</strong>
                         <div className="product-meta">
                           <span className="product-price">{money(activeProduct.price)}</span>
                           <span className="product-divider">·</span>
                           <span className="product-category">{activeProduct.category || 'Fashion'}</span>
                         </div>
                       </div>
                    </div>
                  )}
                </>
               ) : (
                 <div className="custom-input-section">
                    <label className="image-upload-label">
                      <span className="upload-icon">📷</span>
                      <strong className="upload-title">Choose Image File</strong>
                      <span className="upload-hint">PNG, JPG or WEBP from your device</span>
                      <input type="file" accept="image/*" onChange={handleFileUpload} className="file-input" />
                    </label>

                   <div className="url-section">
                     <span className="url-label">OR URL:</span>
                     <input
                       type="text"
                       placeholder="Paste Meesho / Pinterest Image URL..."
                       value={customImage.startsWith('data:') ? '' : customImage}
                       onChange={(e) => {
                         setCustomImage(e.target.value);
                         setActiveEditorialResult(null);
                       }}
                       className="url-input"
                     />
                   </div>

                   <input
                     type="text"
                     placeholder="Garment name (e.g. Burgundy Velvet Zari Saree)..."
                     value={customTitle}
                     onChange={(e) => setCustomTitle(e.target.value)}
                     className="custom-title-input"
                   />

                   {customImage && (
                     <div className="custom-preview">
                       <img src={customImage} alt="Custom Preview" className="custom-preview-img" />
                       <div className="custom-preview-info">
                         <span className="custom-title">{customTitle || 'Custom Outfit'}</span>
                         <span className="custom-status">
                           ✓ Garment Anchor Attached • Gemini Vision Ready
                         </span>
                       </div>
                     </div>
                   )}
                </div>
              )}
            </div>

             {/* Step 2: Editorial Atmosphere & Vibe */}
             <div className="product-card">
               <div className="step-header">
                 <span className="step-number">2</span>
                 <h3 className="step-title">Choose Editorial Style &amp; Atmosphere</h3>
               </div>

               <div className="style-grid">
                {EDITORIAL_STYLES.map((style) => {
                  const isSelected = selectedStyleId === style.id;
                  return (
                     <button
                       key={style.id}
                       className={`${isSelected ? 'style-button active' : 'style-button'}`}
                       onClick={() => {
                         setSelectedStyleId(style.id);
                         setIsPromptCustomized(false);
                       }}
                     >
                       <div className="style-icon-large">{style.icon}</div>
                       <strong className="style-name">{style.name}</strong>
                       <span className="style-desc">{style.desc}</span>
                    </button>
                  );
                })}
              </div>

               {/* Aspect Ratio */}
               <div className="aspect-ratio-section">
                 <span className="aspect-ratio-label">Aspect Ratio:</span>
                 <div className="aspect-ratio-options">
                   {['4:5', '9:16', '1:1'].map((r) => (
                     <button
                       key={r}
                       className={`${aspectRatio === r ? 'aspect-ratio-button active' : 'aspect-ratio-button'}`}
                       onClick={() => setAspectRatio(r)}
                     >
                       {r}
                     </button>
                   ))}
                 </div>
               </div>
            </div>

             {/* Step 3: Vision Direction & Generate */}
             <div className="product-card">
               <div className="step-header">
                  <div className="prompt-editor-header">
                   <span className="step-number">
                     3
                   </span>
                   <h3 className="step-title">
                     Prompt &amp; Generation
                   </h3>
                 </div>
                {isPromptCustomized && (
                   <button
                     type="button"
                     className="reset-prompt-button"
                     onClick={() => setIsPromptCustomized(false)}
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
                />

                <button
                 type="button"
                 className={`${isGenerating || !activeProduct ? 'generate-button disabled' : 'generate-button'}`}
                 disabled={isGenerating || !activeProduct}
                 onClick={handleGenerate}
               >
                 {isGenerating ? (
                   <span>⚙️ Rendering Step {generationStep}/4...</span>
                 ) : (
                   <>
                     <span className="generate-icon">🚀</span> Generate Fashion Editorial
                   </>
                 )}
               </button>
            </div>
          </div>

           {/* Right Column: Visual Canvas & Real Output */}
           <div className="visual-output-card">
             <div className="visual-output-header">
               <div>
                 <h3 className="visual-output-title">
                   Visual Output Comparison
                 </h3>
                 <p className="visual-output-description">
                   Side-by-side verification: Original product vs AI photoshoot.
                 </p>
               </div>

               <label className="watermark-label">
                 <input
                   type="checkbox"
                   checked={showWatermark}
                   onChange={(e) => setShowWatermark(e.target.checked)}
                 />
                 <span>Brand watermark</span>
               </label>
             </div>

             {/* Side-by-Side Canvas */}
             <div className="canvas-grid">
               {/* Original Listing Image */}
               <div className="canvas-panel original-panel">
                 <div className="panel-header">
                   <span className="panel-title">Input Reference Garment</span>
                   <span className="panel-badge">RAW ANCHOR</span>
                 </div>
                 <div className="canvas-image-wrapper">
                   <img
                     src={activeEditorialResult?.reference_image || (garmentSource === 'custom' ? customImage : activeProduct?.image) || '/images/meesho-peach-short-kurti.webp'}
                     alt="Original Reference"
                     className="canvas-image"
                     onError={(e) => { e.currentTarget.src = '/images/meesho-peach-short-kurti.webp'; }}
                   />
                 </div>
                 <div className="panel-footer">
                   {garmentSource === 'custom' ? (customTitle || 'Custom Outfit') : cleanDisplayTitle(activeProduct?.title)}
                 </div>
               </div>

               {/* Generated Fashion Editorial */}
               <div className={`canvas-panel editorial-panel ${activeEditorialResult ? 'has-result' : ''}`}>
                 <div className="panel-header">
                   <span className="panel-title">
                     {activeEditorialResult ? '✓ Enhanced Editorial' : 'AI Rendered Result'}
                   </span>
                  {activeEditorialResult?.garment_analyzed && (
                    <span style={{ fontSize: '10px', background: 'rgba(34, 197, 94, 0.12)', color: '#16a34a', padding: '1px 6px', borderRadius: '4px', fontWeight: 700 }}>
                      VISION PRESERVED
                    </span>
                  )}
                </div>

                 <div className="canvas-image-wrapper">
                   {isGenerating ? (
                     <div className="generation-state">
                       <span className="generation-icon">⚙️</span>
                       <strong className="generation-title">Rendering Editorial...</strong>
                       <span className="generation-step">
                         Step {generationStep}/4 · {selectedEngine === 'arena' ? 'LM Arena (FLUX Tier 1)' : 'Google AI Studio'}
                       </span>
                     </div>
                  ) : activeEditorialResult ? (
                    <>
                       <img
                         src={activeEditorialResult.src}
                         alt="Generated Editorial"
                         className="result-image"
                       />
                       {showWatermark && (
                         <div className="watermark">
                           SHELF EDITORIAL
                         </div>
                       )}
                    </>
                   ) : (
                     <div className="empty-state">
                       <span className="empty-icon">✨</span>
                       <strong className="empty-title">No Result Yet</strong>
                       <p className="empty-description">
                         Generate an AI fashion editorial to see the result here.
                       </p>
                     </div>
                  )}
                </div>

                <div style={{ fontSize: '11.5px', color: activeEditorialResult ? '#16a34a' : 'var(--muted)', marginTop: '8px', fontWeight: activeEditorialResult ? 700 : 500 }}>
                  {activeEditorialResult ? `● ${activeEditorialResult.engine} (${activeEditorialResult.duration})` : `○ Engine: ${selectedEngine.toUpperCase()}`}
                 </div>
               </div>
             </div>

             <div className="engine-info">
               {activeEditorialResult ? `● ${activeEditorialResult.engine} (${activeEditorialResult.duration})` : `○ Engine: ${selectedEngine.toUpperCase()}`}
             </div>

             {/* 1-Click Action Bar for Generated Result */}
             {activeEditorialResult && (
               <div className="action-bar">
                 <button
                   type="button"
                   onClick={handleApplyToStorefront}
                   className="button button-dark action-button"
                 >
                   ✨ Storefront Cover
                 </button>

                 <button
                   type="button"
                   onClick={handleApplyToWishlink}
                   className="action-button wishlink-button"
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
