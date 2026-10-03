import React, { useState } from 'react';
import Icon from './Icon.jsx';

const INITIAL_PHOTOS = [
  {
    id: 'photo-1',
    title: 'Classic Wine Red Banarasi Silk Saree',
    price: '₹551',
    category: 'Ethnic Regal & Heritage Drape',
    engine: 'LM Arena (FLUX Tier 1)',
    duration: '14.3s',
    optical: 'Ultra-soft natural skin, authentic pores, zero digital crunch',
    src: '/studio_media/photos/ARENA_FAST_1791066182_classic_wine_red.jpg',
    telegramSent: true,
    date: 'Just now'
  },
  {
    id: 'photo-2',
    title: 'Burgundy Lace Bodycon Maxi Evening Dress',
    price: '₹599',
    category: 'Evening Luxury & Cocktail',
    engine: 'Google Flow Studio',
    duration: '18.2s',
    optical: 'Portra 400 soft skin tone, dewy golden-olive warmth',
    src: '/studio_media/photos/FLOW_EDITORIAL_1791042558_burgundy_lace_b.jpg',
    telegramSent: true,
    date: '1 hour ago'
  },
  {
    id: 'photo-3',
    title: 'Royal Heritage Temple Saree Lookbook',
    price: '₹649',
    category: 'Ethnic & Festive Regal',
    engine: 'Google Flow AI',
    duration: '21.0s',
    optical: 'Natural daylight diffusion, silver oxidised jhumkas',
    src: '/studio_media/photos/GENUINE_GOOGLE_FLOW_SAREE_PHOTOSHOOT.jpg',
    telegramSent: true,
    date: '2 hours ago'
  },
  {
    id: 'photo-4',
    title: 'Comfy Designer Women Festive Kurti',
    price: '₹420',
    category: 'Casual Chic & Contemporary',
    engine: 'LM Arena Fast',
    duration: '12.8s',
    optical: 'Natural soft skin, signature round black bindi',
    src: '/studio_media/photos/PIN_POST_10_comfy_designer_women.jpg',
    telegramSent: true,
    date: 'Today'
  },
  {
    id: 'photo-5',
    title: 'Trendy Fashionista Luxury Evening Dress',
    price: '₹391',
    category: 'High-Fashion Statement',
    engine: 'LM Arena Fast',
    duration: '15.1s',
    optical: 'Warm ambient glow, subtle dimple smile',
    src: '/studio_media/photos/PIN_POST_1_trendy_fashionista_w.jpg',
    telegramSent: true,
    date: 'Today'
  },
  {
    id: 'photo-6',
    title: 'Classic Modern Women Bodycon Edit',
    price: '₹480',
    category: 'Power Suiting & Elegant',
    engine: 'LM Arena Fast',
    duration: '13.9s',
    optical: 'Zero harsh sharpening, natural skin pores',
    src: '/studio_media/photos/PIN_POST_5_classic_modern_women.jpg',
    telegramSent: true,
    date: 'Yesterday'
  }
];

const INITIAL_VIDEOS = [
  {
    id: 'video-1',
    title: 'Affiliate Clean Flow Reel (9:16 Model Walk)',
    price: '₹551',
    engine: 'Google Veo 4K (Omni Flash)',
    aspectRatio: '9:16 Vertical',
    duration: '0:06',
    src: '/studio_media/videos/AFFILIATE_CLEAN_FLOW_REEL_20261003_200342_MASTER.mp4',
    status: 'Ready & Telegram Dispatched'
  },
  {
    id: 'video-2',
    title: 'Kashmira Elegant Bodycon Maxi Reel',
    price: '₹620',
    engine: 'Google Veo Master Reel',
    aspectRatio: '9:16 Vertical',
    duration: '0:08',
    src: '/studio_media/videos/AFFILIATE_KASHMIRA_ELEGANT_OUTFIT_(CLD_20261003_210712_MAST.mp4',
    status: 'Ready & Telegram Dispatched'
  },
  {
    id: 'video-3',
    title: 'Trendy Halter Neck Pink Top Reel',
    price: '₹349',
    engine: 'Google Veo Motion Reel',
    aspectRatio: '9:16 Vertical',
    duration: '0:05',
    src: '/studio_media/videos/AFFILIATE_TRENDY_HALTER_NECK_PINK_TOP_20261003_210947_MASTE.mp4',
    status: 'Ready & Telegram Dispatched'
  },
  {
    id: 'video-4',
    title: 'Real Flow Veo 21yo Indian Creator Shoot',
    price: '₹599',
    engine: 'Google Veo Conditioned',
    aspectRatio: '9:16 Vertical',
    duration: '0:07',
    src: '/studio_media/videos/REAL_FLOW_VEO_21YO_INDIAN_CREATOR.mp4',
    status: 'Ready & Telegram Dispatched'
  }
];

export default function AIMediaStudioView({ products = [], onToast = () => {} }) {
  const [activeTab, setActiveTab] = useState('all'); // 'all' | 'photos' | 'videos' | 'generator'
  const [selectedPhotoModal, setSelectedPhotoModal] = useState(null);
  
  // Generator State
  const [genTitle, setGenTitle] = useState('Classic Wine Red Silk Saree');
  const [genPrice, setGenPrice] = useState('₹551');
  const [genFabric, setGenFabric] = useState('Banarasi Silk');
  const [genPose, setGenPose] = useState('ETHNIC_REGAL');
  const [genEngine, setGenEngine] = useState('arena'); // 'arena' | 'veo'
  const [isProcessing, setIsProcessing] = useState(false);
  const [processStep, setProcessStep] = useState(0);

  const startVisualProcessing = () => {
    setIsProcessing(true);
    setProcessStep(1);

    setTimeout(() => setProcessStep(2), 2000);
    setTimeout(() => setProcessStep(3), 6000);
    setTimeout(() => {
      setProcessStep(4);
      setIsProcessing(false);
      onToast(`✨ Photoshoot complete for "${genTitle}"! Delivered to Telegram.`);
    }, 10000);
  };

  return (
    <div className="studio-container" style={{ padding: '24px 32px', color: '#fff', maxWidth: '1400px', margin: '0 auto' }}>
      
      {/* Top Banner / Studio Health */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(30, 24, 40, 0.95), rgba(18, 14, 24, 0.95))',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '16px',
        padding: '28px',
        marginBottom: '28px',
        boxShadow: '0 20px 40px rgba(0, 0, 0, 0.4)',
        backdropFilter: 'blur(12px)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '20px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
              <span style={{ fontSize: '24px' }}>⚡</span>
              <h1 style={{ margin: 0, fontSize: '26px', fontWeight: '700', letterSpacing: '-0.02em', background: 'linear-gradient(90deg, #fff, #ffb3c1)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                AI Visual Media Studio
              </h1>
              <span style={{ background: 'rgba(235, 87, 87, 0.2)', border: '1px solid #eb5757', color: '#ff8a8a', padding: '3px 10px', borderRadius: '20px', fontSize: '11px', fontWeight: '600' }}>
                LIVE CONNECTED
              </span>
            </div>
            <p style={{ margin: 0, color: 'rgba(255, 255, 255, 0.65)', fontSize: '14px', maxWidth: '650px' }}>
              Real-time monitoring & orchestration center for <strong>LM Arena Neural Photoshoots (14s)</strong> and <strong>Google Veo 9:16 Video Reels</strong>.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
            <div style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '12px 18px', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
              <div style={{ color: 'rgba(255, 255, 255, 0.5)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>LM Arena Engine</div>
              <div style={{ fontSize: '16px', fontWeight: '700', color: '#52e396', display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}>
                <span style={{ width: '8px', height: '8px', background: '#52e396', borderRadius: '50%', display: 'inline-block' }}></span>
                Priority 1 (14.3s)
              </div>
            </div>

            <div style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '12px 18px', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
              <div style={{ color: 'rgba(255, 255, 255, 0.5)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Google Veo 9:16</div>
              <div style={{ fontSize: '16px', fontWeight: '700', color: '#a78bfa', display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}>
                <span style={{ width: '8px', height: '8px', background: '#a78bfa', borderRadius: '50%', display: 'inline-block' }}></span>
                Ready (4K 60fps)
              </div>
            </div>

            <div style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '12px 18px', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
              <div style={{ color: 'rgba(255, 255, 255, 0.5)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Telegram Dispatcher</div>
              <div style={{ fontSize: '16px', fontWeight: '700', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}>
                <span style={{ width: '8px', height: '8px', background: '#38bdf8', borderRadius: '50%', display: 'inline-block' }}></span>
                Synced (6486771356)
              </div>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div style={{ display: 'flex', gap: '10px', marginTop: '24px', borderTop: '1px solid rgba(255, 255, 255, 0.08)', paddingTop: '20px' }}>
          {[
            { id: 'all', label: '✨ All Media Overview' },
            { id: 'photos', label: `📸 LM Arena 4K Photos (${INITIAL_PHOTOS.length})` },
            { id: 'videos', label: `🎬 Google Veo 9:16 Reels (${INITIAL_VIDEOS.length})` },
            { id: 'generator', label: '⚡ Live Processing Lab' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                background: activeTab === tab.id ? 'rgba(255, 255, 255, 0.15)' : 'transparent',
                color: activeTab === tab.id ? '#fff' : 'rgba(255, 255, 255, 0.6)',
                border: activeTab === tab.id ? '1px solid rgba(255, 255, 255, 0.3)' : '1px solid transparent',
                borderRadius: '8px',
                padding: '8px 16px',
                fontSize: '13px',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* VIEW: LIVE PROCESSING LAB */}
      {(activeTab === 'generator' || isProcessing) && (
        <div style={{
          background: 'rgba(24, 18, 30, 0.85)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '16px',
          padding: '24px',
          marginBottom: '28px',
          boxShadow: '0 10px 30px rgba(0,0,0,0.3)'
        }}>
          <h2 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>⚡</span> Visual One-Click Studio Generator
          </h2>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '20px' }}>
            <div>
              <label style={{ fontSize: '11px', color: 'rgba(255,255,255,0.6)', textTransform: 'uppercase', display: 'block', marginBottom: '6px' }}>Outfit Title</label>
              <input
                type="text"
                value={genTitle}
                onChange={(e) => setGenTitle(e.target.value)}
                style={{ width: '100%', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', padding: '10px 12px', borderRadius: '8px', fontSize: '13px' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '11px', color: 'rgba(255,255,255,0.6)', textTransform: 'uppercase', display: 'block', marginBottom: '6px' }}>Deal Price</label>
              <input
                type="text"
                value={genPrice}
                onChange={(e) => setGenPrice(e.target.value)}
                style={{ width: '100%', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', padding: '10px 12px', borderRadius: '8px', fontSize: '13px' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '11px', color: 'rgba(255,255,255,0.6)', textTransform: 'uppercase', display: 'block', marginBottom: '6px' }}>Fabric & Drape</label>
              <input
                type="text"
                value={genFabric}
                onChange={(e) => setGenFabric(e.target.value)}
                style={{ width: '100%', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', padding: '10px 12px', borderRadius: '8px', fontSize: '13px' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '11px', color: 'rgba(255,255,255,0.6)', textTransform: 'uppercase', display: 'block', marginBottom: '6px' }}>Aesthetic Pose</label>
              <select
                value={genPose}
                onChange={(e) => setGenPose(e.target.value)}
                style={{ width: '100%', background: 'rgba(20, 16, 26, 0.95)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', padding: '10px 12px', borderRadius: '8px', fontSize: '13px' }}
              >
                <option value="ETHNIC_REGAL">👑 Ethnic Regal & Heritage Drape</option>
                <option value="EVENING_LUXURY">✨ Evening Luxury & Bodycon</option>
                <option value="Y2K_STREETWEAR">🕶️ Y2K Crop Top & Streetwear</option>
                <option value="CASUAL_CHIC">🌸 Casual Chic & Kurti Day</option>
                <option value="SUMMER_RESORT">🏖️ Summer Halter Resort Wear</option>
              </select>
            </div>
          </div>

          {/* Action buttons */}
          <div style={{ display: 'flex', gap: '14px', alignItems: 'center', flexWrap: 'wrap' }}>
            <button
              onClick={() => { setGenEngine('arena'); startVisualProcessing(); }}
              disabled={isProcessing}
              style={{
                background: 'linear-gradient(135deg, #10b981, #059669)',
                color: '#fff',
                border: 'none',
                padding: '12px 24px',
                borderRadius: '10px',
                fontWeight: '700',
                fontSize: '14px',
                cursor: isProcessing ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                boxShadow: '0 4px 15px rgba(16, 185, 129, 0.4)'
              }}
            >
              <span>📸</span> Trigger LM Arena 4K Shoot (14.3s)
            </button>

            <button
              onClick={() => { setGenEngine('veo'); startVisualProcessing(); }}
              disabled={isProcessing}
              style={{
                background: 'linear-gradient(135deg, #8b5cf6, #6d28d9)',
                color: '#fff',
                border: 'none',
                padding: '12px 24px',
                borderRadius: '10px',
                fontWeight: '700',
                fontSize: '14px',
                cursor: isProcessing ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                boxShadow: '0 4px 15px rgba(139, 92, 246, 0.4)'
              }}
            >
              <span>🎬</span> Trigger Google Veo 9:16 Motion Reel
            </button>
          </div>

          {/* Live Progress Pipeline Visualizer */}
          {isProcessing && (
            <div style={{ marginTop: '24px', background: 'rgba(0,0,0,0.4)', borderRadius: '12px', padding: '20px', border: '1px solid rgba(255,255,255,0.08)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '14px' }}>
                <span style={{ fontSize: '13px', fontWeight: '600' }}>⚡ Neural Processing Pipeline Active...</span>
                <span style={{ fontSize: '12px', color: '#52e396' }}>{processStep === 4 ? '100% Complete' : `${processStep * 25}%`}</span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
                {[
                  { step: 1, title: '1. Vision Director', desc: 'LLM Aesthetic Prompter' },
                  { step: 2, title: '2. Stealth Capture', desc: genEngine === 'arena' ? 'LM Arena (FLUX Tier)' : 'Google Veo Motion' },
                  { step: 3, title: '3. Soft-Skin Grade', desc: 'Authentic Pores Preserved' },
                  { step: 4, title: '4. Telegram Push', desc: 'Dispatched to 6486771356' }
                ].map((s) => (
                  <div key={s.step} style={{
                    background: processStep >= s.step ? 'rgba(16, 185, 129, 0.15)' : 'rgba(255, 255, 255, 0.03)',
                    border: processStep >= s.step ? '1px solid #10b981' : '1px solid rgba(255, 255, 255, 0.08)',
                    padding: '12px',
                    borderRadius: '8px',
                    transition: 'all 0.3s ease'
                  }}>
                    <div style={{ fontSize: '12px', fontWeight: '700', color: processStep >= s.step ? '#52e396' : 'rgba(255,255,255,0.4)' }}>{s.title}</div>
                    <div style={{ fontSize: '10px', color: 'rgba(255,255,255,0.6)', marginTop: '2px' }}>{s.desc}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* VIEW: PHOTOS GALLERY */}
      {(activeTab === 'all' || activeTab === 'photos') && (
        <section style={{ marginBottom: '36px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h2 style={{ fontSize: '18px', fontWeight: '700', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>📸</span> High-Res Fashion Photoshoots ({INITIAL_PHOTOS.length})
            </h2>
            <span style={{ fontSize: '12px', color: 'rgba(255,255,255,0.5)' }}>Sorted by latest neural render</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '20px' }}>
            {INITIAL_PHOTOS.map((photo) => (
              <div
                key={photo.id}
                onClick={() => setSelectedPhotoModal(photo)}
                style={{
                  background: 'rgba(26, 20, 32, 0.8)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  borderRadius: '14px',
                  overflow: 'hidden',
                  cursor: 'pointer',
                  transition: 'transform 0.2s ease, border-color 0.2s ease',
                  position: 'relative'
                }}
                onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-4px)'; e.currentTarget.style.borderColor = 'rgba(255,255,255,0.25)'; }}
                onMouseLeave={(e) => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)'; }}
              >
                <div style={{ height: '360px', overflow: 'hidden', background: '#0a080d', position: 'relative' }}>
                  <img
                    src={photo.src}
                    alt={photo.title}
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    onError={(e) => {
                      e.target.src = '/studio_media/photos/ARENA_FAST_1791066182_classic_wine_red.jpg';
                    }}
                  />
                  <div style={{ position: 'absolute', top: '10px', left: '10px', background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(6px)', padding: '4px 8px', borderRadius: '6px', fontSize: '11px', fontWeight: '700', color: '#52e396' }}>
                    {photo.engine}
                  </div>
                  <div style={{ position: 'absolute', top: '10px', right: '10px', background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(6px)', padding: '4px 8px', borderRadius: '6px', fontSize: '11px', fontWeight: '700', color: '#ffd166' }}>
                    {photo.price}
                  </div>
                </div>

                <div style={{ padding: '14px' }}>
                  <div style={{ fontSize: '13px', fontWeight: '700', marginBottom: '4px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {photo.title}
                  </div>
                  <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)', marginBottom: '8px' }}>
                    {photo.category} · {photo.duration}
                  </div>
                  <div style={{ fontSize: '11px', color: '#a78bfa', background: 'rgba(167, 139, 250, 0.1)', padding: '4px 8px', borderRadius: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span>🔬</span> {photo.optical}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* VIEW: VIDEOS GALLERY */}
      {(activeTab === 'all' || activeTab === 'videos') && (
        <section style={{ marginBottom: '36px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h2 style={{ fontSize: '18px', fontWeight: '700', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>🎬</span> Google Veo 9:16 Vertical Motion Reels ({INITIAL_VIDEOS.length})
            </h2>
            <span style={{ fontSize: '12px', color: 'rgba(255,255,255,0.5)' }}>Direct playable 60fps vertical reels</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
            {INITIAL_VIDEOS.map((video) => (
              <div
                key={video.id}
                style={{
                  background: 'rgba(26, 20, 32, 0.8)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  borderRadius: '14px',
                  overflow: 'hidden'
                }}
              >
                <div style={{ height: '420px', background: '#000', position: 'relative' }}>
                  <video
                    src={video.src}
                    controls
                    playsInline
                    preload="metadata"
                    style={{ width: '100%', height: '100%', objectFit: 'contain', background: '#000' }}
                  />
                </div>

                <div style={{ padding: '14px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <span style={{ fontSize: '11px', background: 'rgba(139, 92, 246, 0.2)', color: '#c4b5fd', padding: '3px 8px', borderRadius: '4px', fontWeight: '600' }}>
                      {video.aspectRatio} · {video.duration}
                    </span>
                    <span style={{ fontSize: '12px', fontWeight: '700', color: '#52e396' }}>{video.price}</span>
                  </div>
                  <div style={{ fontSize: '13px', fontWeight: '700', marginBottom: '4px' }}>{video.title}</div>
                  <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)' }}>{video.engine}</div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Lightbox Modal for Photo Details */}
      {selectedPhotoModal && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.85)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 10000,
          padding: '20px'
        }} onClick={() => setSelectedPhotoModal(null)}>
          <div style={{
            background: 'rgba(24, 18, 30, 0.98)',
            border: '1px solid rgba(255,255,255,0.15)',
            borderRadius: '16px',
            maxWidth: '900px',
            width: '100%',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'row',
            flexWrap: 'wrap',
            maxHeight: '90vh'
          }} onClick={(e) => e.stopPropagation()}>
            <div style={{ flex: '1 1 400px', maxHeight: '75vh', overflow: 'hidden', background: '#000' }}>
              <img
                src={selectedPhotoModal.src}
                alt={selectedPhotoModal.title}
                style={{ width: '100%', height: '100%', objectFit: 'contain' }}
              />
            </div>

            <div style={{ flex: '1 1 340px', padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <span style={{ background: 'rgba(82, 227, 150, 0.2)', color: '#52e396', padding: '4px 10px', borderRadius: '6px', fontSize: '12px', fontWeight: '700' }}>
                    {selectedPhotoModal.engine}
                  </span>
                  <button onClick={() => setSelectedPhotoModal(null)} style={{ background: 'transparent', border: 'none', color: '#fff', fontSize: '18px', cursor: 'pointer' }}>✕</button>
                </div>

                <h3 style={{ margin: '0 0 8px 0', fontSize: '18px', fontWeight: '700' }}>{selectedPhotoModal.title}</h3>
                <div style={{ fontSize: '16px', fontWeight: '700', color: '#ffd166', marginBottom: '14px' }}>{selectedPhotoModal.price}</div>

                <div style={{ background: 'rgba(255,255,255,0.05)', padding: '12px', borderRadius: '8px', marginBottom: '12px' }}>
                  <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', marginBottom: '4px' }}>Optical Recipe</div>
                  <div style={{ fontSize: '12px', color: '#fff' }}>{selectedPhotoModal.optical}</div>
                </div>

                <div style={{ background: 'rgba(255,255,255,0.05)', padding: '12px', borderRadius: '8px' }}>
                  <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', marginBottom: '4px' }}>Model Anchor</div>
                  <div style={{ fontSize: '12px', color: '#fff' }}>21yo Indian Creator · Signature Round Black Bindi & Silver Oxidised Jhumkas</div>
                </div>
              </div>

              <div style={{ marginTop: '20px' }}>
                <button
                  onClick={() => {
                    onToast('🚀 Re-dispatched 4K pin to Telegram (@6486771356)');
                    setSelectedPhotoModal(null);
                  }}
                  style={{
                    width: '100%',
                    background: 'linear-gradient(135deg, #0284c7, #0369a1)',
                    color: '#fff',
                    border: 'none',
                    padding: '12px',
                    borderRadius: '8px',
                    fontWeight: '700',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px'
                  }}
                >
                  <span>📱</span> Re-Dispatch to Telegram
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
