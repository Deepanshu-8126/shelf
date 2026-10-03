import React, { useState } from 'react';
import Icon from './Icon';

const DEFAULT_BANNER_SLIDES = [
  {
    id: 'slide-tops',
    category: 'Tops & Tunics',
    label: 'TOPS & Y2K EDITS',
    title: 'Effortless layers, cute details',
    subtitle: 'Corset crops, ribbed knits & everyday chic.',
    sticker: 'TRENDING TOPS',
    action: 'Explore tops',
    theme: 'sage',
    image: 'https://images.meesho.com/images/products/682813217/hbo6b_512.webp',
    active: true
  },
  {
    id: 'slide-kurtis',
    category: 'Kurtis',
    label: 'ETHNIC & KURTIS',
    title: 'Heritage prints, modern ease',
    subtitle: 'Floral anarkalis, luxury sets & festive charm.',
    sticker: 'CURATED ETHNIC',
    action: 'Explore kurtis',
    theme: 'lilac',
    image: 'https://images.meesho.com/images/products/608249051/kpxyo_512.webp',
    active: true
  },
  {
    id: 'slide-dresses',
    category: 'Women Dresses',
    label: 'DRESSES & BODYCON',
    title: 'Main-character plans, sorted',
    subtitle: 'Ruched bodycons, satin maxis & party silhouettes.',
    sticker: 'SIGNATURE DRESSES',
    action: 'Explore dresses',
    theme: 'peach',
    image: 'https://images.meesho.com/images/products/665972551/lslwe_512.webp',
    active: true
  },
  {
    id: 'slide-winter',
    category: 'Winter',
    label: 'WINTER & KNITWEAR',
    title: 'Cold-weather luxury layers',
    subtitle: 'Oversized cardigans, fleece knits & chic puffers.',
    sticker: 'WINTER CAPSULE',
    action: 'Explore winter',
    theme: 'blue',
    image: 'https://images.meesho.com/images/products/653069151/lsqwe_512.webp',
    active: true
  }
];

export default function AdminBannersManager({ products = [], onSaveBanners }) {
  const [slides, setSlides] = useState(() => {
    try {
      const saved = localStorage.getItem('shelf_admin_banners');
      return saved ? JSON.parse(saved) : DEFAULT_BANNER_SLIDES;
    } catch {
      return DEFAULT_BANNER_SLIDES;
    }
  });

  const [activeSlideIndex, setActiveSlideIndex] = useState(0);
  const [editingSlide, setEditingSlide] = useState(null);
  const [previewDevice, setPreviewDevice] = useState('desktop'); // 'desktop' or 'mobile'
  const [saveNotice, setSaveNotice] = useState('');

  const currentSlide = slides[activeSlideIndex] || slides[0];

  const handleUpdateSlideField = (field, value) => {
    setSlides(prev => {
      const next = [...prev];
      if (next[activeSlideIndex]) {
        next[activeSlideIndex] = { ...next[activeSlideIndex], [field]: value };
      }
      return next;
    });
  };

  const handleToggleActive = (index) => {
    setSlides(prev => {
      const next = [...prev];
      next[index] = { ...next[index], active: !next[index].active };
      return next;
    });
  };

  const handleMoveSlide = (index, direction) => {
    const target = index + direction;
    if (target < 0 || target >= slides.length) return;
    setSlides(prev => {
      const next = [...prev];
      const temp = next[index];
      next[index] = next[target];
      next[target] = temp;
      return next;
    });
    setActiveSlideIndex(target);
  };

  const handleAddSlide = () => {
    const newSlide = {
      id: `slide-${Date.now()}`,
      category: 'New Category',
      label: 'CURATED DROP',
      title: 'Headline for this edit',
      subtitle: 'Supporting subtitle copy.',
      sticker: 'NEW COLLECTION',
      action: 'Shop Now',
      theme: 'sage',
      image: products[0]?.image || 'https://images.meesho.com/images/products/682813217/hbo6b_512.webp',
      active: true
    };
    setSlides(prev => [...prev, newSlide]);
    setActiveSlideIndex(slides.length);
  };

  const handleDeleteSlide = (index) => {
    if (slides.length <= 1) {
      alert('You must have at least one hero slide.');
      return;
    }
    if (window.confirm('Delete this banner slide?')) {
      setSlides(prev => prev.filter((_, i) => i !== index));
      setActiveSlideIndex(0);
    }
  };

  const handleSaveAll = () => {
    try {
      localStorage.setItem('shelf_admin_banners', JSON.stringify(slides));
      onSaveBanners?.(slides);
      setSaveNotice('✓ Storefront Hero & Banners Published Successfully!');
      setTimeout(() => setSaveNotice(''), 3000);
    } catch {
      setSaveNotice('Failed to save banners');
    }
  };

  return (
    <div className="admin-banners-manager" style={{ maxWidth: '1440px', margin: '0 auto', padding: '24px 20px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: '800', color: '#fff', display: 'flex', alignItems: 'center', gap: '10px' }}>
            🖼️ Storefront Hero &amp; Banners Manager
            <span style={{ fontSize: '12px', background: 'rgba(236, 72, 153, 0.15)', color: '#f472b6', border: '1px solid rgba(236, 72, 153, 0.3)', padding: '3px 10px', borderRadius: '999px', fontWeight: '700' }}>
              {slides.filter(s => s.active).length} Active Slides
            </span>
          </h1>
          <p style={{ fontSize: '13px', color: 'rgba(255, 255, 255, 0.65)', marginTop: '4px' }}>
            Directly control the public homepage carousel: customize headlines, background imagery, stickers, CTA buttons, and slide order.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <button
            type="button"
            onClick={handleAddSlide}
            style={{ background: 'rgba(255,255,255,0.08)', color: '#fff', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '10px', padding: '10px 16px', fontSize: '13px', fontWeight: '700', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <Icon name="plus" size={16} /> Add New Slide
          </button>
          <button
            type="button"
            onClick={handleSaveAll}
            style={{ background: 'linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%)', color: '#fff', border: 'none', borderRadius: '10px', padding: '10px 20px', fontSize: '13px', fontWeight: '750', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            🚀 Save &amp; Publish Banners
          </button>
        </div>
      </div>

      {saveNotice && (
        <div style={{ background: 'rgba(34, 197, 94, 0.15)', border: '1px solid rgba(34, 197, 94, 0.3)', color: '#4ade80', padding: '10px 16px', borderRadius: '10px', fontSize: '13px', fontWeight: '700', marginBottom: '16px' }}>
          {saveNotice}
        </div>
      )}

      {/* Main 2-Column Studio Grid: Editor on Left, Live Mockup on Right */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '20px', alignItems: 'start' }}>
        {/* Left Column: Slide List & Field Editor */}
        <div style={{ background: 'rgba(255, 255, 255, 0.04)', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: '16px', padding: '20px', backdropFilter: 'blur(16px)' }}>
          {/* Slide Tab Strip */}
          <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '12px', borderBottom: '1px solid rgba(255,255,255,0.1)', marginBottom: '16px' }}>
            {slides.map((s, idx) => (
              <button
                key={s.id || idx}
                type="button"
                onClick={() => setActiveSlideIndex(idx)}
                style={{
                  background: activeSlideIndex === idx ? 'linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%)' : 'rgba(255,255,255,0.06)',
                  border: '1px solid rgba(255,255,255,0.15)',
                  borderRadius: '8px',
                  padding: '8px 12px',
                  color: '#fff',
                  fontSize: '12px',
                  fontWeight: '700',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  whiteSpace: 'nowrap',
                  opacity: s.active ? 1 : 0.5
                }}
              >
                <span>Slide {idx + 1}: {s.category}</span>
                {!s.active && <span style={{ fontSize: '9px', background: '#eab30830', color: '#fde047', padding: '1px 4px', borderRadius: '3px' }}>Off</span>}
              </button>
            ))}
          </div>

          {/* Active Slide Form Editor */}
          {currentSlide && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '15px', fontWeight: '800', color: '#38bdf8' }}>
                  Editing Slide {activeSlideIndex + 1} ({currentSlide.category})
                </span>
                <div style={{ display: 'flex', gap: '6px' }}>
                  <button
                    type="button"
                    onClick={() => handleMoveSlide(activeSlideIndex, -1)}
                    disabled={activeSlideIndex === 0}
                    style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', padding: '4px 8px', borderRadius: '6px', fontSize: '11px', cursor: 'pointer' }}
                  >
                    ⬆️ Move Up
                  </button>
                  <button
                    type="button"
                    onClick={() => handleMoveSlide(activeSlideIndex, 1)}
                    disabled={activeSlideIndex === slides.length - 1}
                    style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', padding: '4px 8px', borderRadius: '6px', fontSize: '11px', cursor: 'pointer' }}
                  >
                    ⬇️ Move Down
                  </button>
                  <button
                    type="button"
                    onClick={() => handleToggleActive(activeSlideIndex)}
                    style={{ background: currentSlide.active ? 'rgba(34, 197, 94, 0.2)' : 'rgba(234, 179, 8, 0.2)', border: '1px solid rgba(255,255,255,0.2)', color: currentSlide.active ? '#4ade80' : '#fde047', padding: '4px 10px', borderRadius: '6px', fontSize: '11px', fontWeight: '700', cursor: 'pointer' }}
                  >
                    {currentSlide.active ? '● Active' : '○ Disabled'}
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDeleteSlide(activeSlideIndex)}
                    style={{ background: 'rgba(239, 68, 68, 0.2)', border: '1px solid rgba(239, 68, 68, 0.4)', color: '#f87171', padding: '4px 8px', borderRadius: '6px', fontSize: '11px', cursor: 'pointer' }}
                  >
                    🗑️
                  </button>
                </div>
              </div>

              {/* Form Fields */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ fontSize: '11.5px', color: '#9ca3af', fontWeight: '600', display: 'block', marginBottom: '4px' }}>Category Name</label>
                  <input
                    type="text"
                    value={currentSlide.category || ''}
                    onChange={(e) => handleUpdateSlideField('category', e.target.value)}
                    style={{ width: '100%', borderRadius: '8px', padding: '8px 12px', background: 'rgba(0,0,0,0.35)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', fontSize: '12px' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '11.5px', color: '#9ca3af', fontWeight: '600', display: 'block', marginBottom: '4px' }}>Top Kicker Label</label>
                  <input
                    type="text"
                    value={currentSlide.label || ''}
                    onChange={(e) => handleUpdateSlideField('label', e.target.value)}
                    style={{ width: '100%', borderRadius: '8px', padding: '8px 12px', background: 'rgba(0,0,0,0.35)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', fontSize: '12px' }}
                  />
                </div>
              </div>

              <div>
                <label style={{ fontSize: '11.5px', color: '#9ca3af', fontWeight: '600', display: 'block', marginBottom: '4px' }}>Headline Title</label>
                <input
                  type="text"
                  value={currentSlide.title || ''}
                  onChange={(e) => handleUpdateSlideField('title', e.target.value)}
                  style={{ width: '100%', borderRadius: '8px', padding: '8px 12px', background: 'rgba(0,0,0,0.35)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', fontSize: '13px', fontWeight: '700' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '11.5px', color: '#9ca3af', fontWeight: '600', display: 'block', marginBottom: '4px' }}>Subtitle Description</label>
                <textarea
                  rows={2}
                  value={currentSlide.subtitle || ''}
                  onChange={(e) => handleUpdateSlideField('subtitle', e.target.value)}
                  style={{ width: '100%', borderRadius: '8px', padding: '8px 12px', background: 'rgba(0,0,0,0.35)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', fontSize: '12px', resize: 'vertical' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ fontSize: '11.5px', color: '#9ca3af', fontWeight: '600', display: 'block', marginBottom: '4px' }}>Sticker Badge</label>
                  <input
                    type="text"
                    value={currentSlide.sticker || ''}
                    onChange={(e) => handleUpdateSlideField('sticker', e.target.value)}
                    style={{ width: '100%', borderRadius: '8px', padding: '8px 12px', background: 'rgba(0,0,0,0.35)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', fontSize: '12px' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '11.5px', color: '#9ca3af', fontWeight: '600', display: 'block', marginBottom: '4px' }}>CTA Button Label</label>
                  <input
                    type="text"
                    value={currentSlide.action || ''}
                    onChange={(e) => handleUpdateSlideField('action', e.target.value)}
                    style={{ width: '100%', borderRadius: '8px', padding: '8px 12px', background: 'rgba(0,0,0,0.35)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', fontSize: '12px' }}
                  />
                </div>
              </div>

              {/* Background Photo Selector */}
              <div>
                <label style={{ fontSize: '11.5px', color: '#9ca3af', fontWeight: '600', display: 'block', marginBottom: '4px' }}>Background Photo URL</label>
                <input
                  type="text"
                  value={currentSlide.image || ''}
                  onChange={(e) => handleUpdateSlideField('image', e.target.value)}
                  placeholder="https://images.meesho.com/..."
                  style={{ width: '100%', borderRadius: '8px', padding: '8px 12px', background: 'rgba(0,0,0,0.35)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', fontSize: '12px' }}
                />
                
                {/* Quick Catalog Image Picker */}
                <div style={{ marginTop: '8px' }}>
                  <span style={{ fontSize: '10.5px', color: '#9ca3af' }}>Or pick from catalog products:</span>
                  <div style={{ display: 'flex', gap: '6px', overflowX: 'auto', marginTop: '4px', paddingBottom: '4px' }}>
                    {products.slice(0, 10).map((p) => (
                      <img
                        key={p.id}
                        src={p.image}
                        alt=""
                        onClick={() => handleUpdateSlideField('image', p.image)}
                        style={{ width: '36px', height: '44px', objectFit: 'cover', borderRadius: '4px', cursor: 'pointer', border: currentSlide.image === p.image ? '2px solid #ec4899' : '1px solid rgba(255,255,255,0.15)' }}
                      />
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Live Interactive Mockup Preview */}
        <div style={{ background: 'rgba(255, 255, 255, 0.04)', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: '16px', padding: '20px', backdropFilter: 'blur(16px)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <span style={{ fontSize: '14px', fontWeight: '800', color: '#fff' }}>👁️ Live Storefront Mockup Preview</span>
            <div style={{ display: 'flex', gap: '4px', background: 'rgba(255,255,255,0.08)', borderRadius: '6px', padding: '2px' }}>
              <button
                type="button"
                onClick={() => setPreviewDevice('desktop')}
                style={{ background: previewDevice === 'desktop' ? '#3b82f6' : 'transparent', color: '#fff', border: 'none', padding: '3px 8px', borderRadius: '4px', fontSize: '11px', cursor: 'pointer' }}
              >
                🖥️ Desktop
              </button>
              <button
                type="button"
                onClick={() => setPreviewDevice('mobile')}
                style={{ background: previewDevice === 'mobile' ? '#3b82f6' : 'transparent', color: '#fff', border: 'none', padding: '3px 8px', borderRadius: '4px', fontSize: '11px', cursor: 'pointer' }}
              >
                📱 Mobile
              </button>
            </div>
          </div>

          {/* Hero Banner Visual Card */}
          <div
            style={{
              position: 'relative',
              borderRadius: '14px',
              overflow: 'hidden',
              minHeight: previewDevice === 'desktop' ? '300px' : '380px',
              background: '#151814',
              border: '1px solid rgba(255,255,255,0.15)',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              padding: '24px'
            }}
          >
            {/* Background Layer with scrim */}
            {currentSlide?.image && (
              <img
                src={currentSlide.image}
                alt=""
                style={{
                  position: 'absolute',
                  inset: 0,
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover',
                  opacity: 0.45,
                  filter: 'blur(2px)'
                }}
              />
            )}
            <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.85) 0%, rgba(15, 23, 42, 0.4) 100%)' }} />

            {/* Top Kicker */}
            <div style={{ position: 'relative', zIndex: 2 }}>
              <span style={{ fontSize: '10px', fontWeight: '800', letterSpacing: '0.08em', color: '#38bdf8', background: 'rgba(56, 189, 248, 0.15)', padding: '3px 8px', borderRadius: '999px', border: '1px solid rgba(56, 189, 248, 0.3)' }}>
                ● {currentSlide?.label || 'CURATED DROP'}
              </span>
            </div>

            {/* Middle Copy */}
            <div style={{ position: 'relative', zIndex: 2, margin: '20px 0' }}>
              <h2 style={{ fontSize: previewDevice === 'desktop' ? '24px' : '18px', fontWeight: '800', color: '#fff', lineHeight: 1.2, margin: '0 0 8px 0' }}>
                {currentSlide?.title || 'Headline'}
              </h2>
              <p style={{ fontSize: '12px', color: 'rgba(255,255,255,0.8)', margin: 0, lineHeight: 1.4 }}>
                {currentSlide?.subtitle || 'Subtitle'}
              </p>
            </div>

            {/* Bottom Actions */}
            <div style={{ position: 'relative', zIndex: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <button
                type="button"
                style={{ background: 'linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%)', color: '#fff', border: 'none', borderRadius: '8px', padding: '8px 16px', fontSize: '12px', fontWeight: '750', display: 'flex', alignItems: 'center', gap: '6px' }}
              >
                {currentSlide?.action || 'Explore'} ↗
              </button>
              {currentSlide?.sticker && (
                <span style={{ fontSize: '10px', fontWeight: '700', color: '#facc15', background: 'rgba(0,0,0,0.6)', padding: '3px 8px', borderRadius: '6px', border: '1px solid rgba(250, 204, 21, 0.3)' }}>
                  ✦ {currentSlide.sticker}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
