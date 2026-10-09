import React, { useState } from 'react';
import Icon from '../ui/Icon.jsx';

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

  const [trendCampaign, setTrendCampaign] = useState(() => {
    try {
      const saved = localStorage.getItem('shelf_festive_config');
      if (saved) return JSON.parse(saved);
    } catch {}
    return {
      enabled: true,
      seasonKey: 'trending',
      title: 'Trending Fits & Wardrobe Edits',
      eyebrow: '✦ VIRAL FINDS 2026',
      ticker: '✦ Fresh Aesthetic Drops & Curated Outfits · Handpicked from Top Creators',
      theme: 'sage',
      icon: '✦',
      query: ''
    };
  });

  const TREND_PRESETS = [
    {
      key: 'spring_2026',
      name: '🌸 Spring Drop 2026 (Floral Chiffon & Y2K Tops)',
      title: 'Spring Blossom & Y2K Tops Edit',
      eyebrow: '🌸 SPRING CAPSULE 2026',
      ticker: '🌸 Spring Wardrobe Drops Live · Chiffon Tops, Ribbed Crops & Dresses from ₹299',
      theme: 'sage',
      icon: '🌸',
      query: 'tops'
    },
    {
      key: 'pinterest_viral',
      name: '📌 Viral Pinterest & Gen-Z Aesthetic Drop',
      title: 'Viral Aesthetic & Downtown Chic',
      eyebrow: '📌 PINTEREST DROPS',
      ticker: '📌 Viral Pinterest & Gen-Z Outfits Live · Streetwear, Bombers & Y2K from ₹399',
      theme: 'lilac',
      icon: '📌',
      query: 'pinterest'
    },
    {
      key: 'summer_vacay',
      name: '☀️ Summer Vacation, Linen Sets & Chic Crops',
      title: 'Summer Getaway & Linen Edit',
      eyebrow: '☀️ SUMMER EDIT 2026',
      ticker: '☀️ Summer Vacation & Linen Co-ord Sets Live · Handpicked from ₹449',
      theme: 'peach',
      icon: '☀️',
      query: 'co-ord'
    },
    {
      key: 'diwali_festive',
      name: '🪔 Diwali & Festive Glam Capsule',
      title: 'Diwali & Festive Glam',
      eyebrow: '🪔 FESTIVE CAPSULE 2026',
      ticker: '🪔 Diwali & Festive Glam Capsule Live · Handpicked Outfits from ₹349',
      theme: 'peach',
      icon: '🪔',
      query: 'festive'
    },
    {
      key: 'navratri_garba',
      name: '💃 Navratri & Garba Ethnic Edit',
      title: 'Navratri & Garba Ethnic Edit',
      eyebrow: '💃 GARBA NIGHTS 2026',
      ticker: '💃 Navratri & Garba Outfits Live · Designer Kurtis & Sets Starting ₹279',
      theme: 'lilac',
      icon: '💃',
      query: 'kurti'
    },
    {
      key: 'winter_cozy',
      name: '❄️ Winter Cozy & Bomber Jackets',
      title: 'Winter Cold-Girl Era',
      eyebrow: '❄️ WINTER CAPSULE 2026',
      ticker: '❄️ Winter Cozy Layers & F1 Bombers Live · Under ₹999',
      theme: 'blue',
      icon: '❄️',
      query: 'winter'
    }
  ];

  const handleApplyTrendPreset = (preset) => {
    const updated = {
      ...trendCampaign,
      seasonKey: preset.key,
      title: preset.title,
      eyebrow: preset.eyebrow,
      ticker: preset.ticker,
      theme: preset.theme,
      icon: preset.icon,
      query: preset.query
    };
    setTrendCampaign(updated);
    localStorage.setItem('shelf_festive_config', JSON.stringify(updated));
    window.dispatchEvent(new Event('shelf_banner_update'));
    setSaveNotice(`✓ Activated Google Trend Campaign: "${preset.title}"`);
    setTimeout(() => setSaveNotice(''), 3000);
  };

  const handleSaveTrendCampaign = () => {
    localStorage.setItem('shelf_festive_config', JSON.stringify(trendCampaign));
    window.dispatchEvent(new Event('shelf_banner_update'));
    setSaveNotice('✓ Header Trend Campaign updated & live on storefront!');
    setTimeout(() => setSaveNotice(''), 3000);
  };

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
      localStorage.setItem('shelf_festive_config', JSON.stringify(trendCampaign));
      window.dispatchEvent(new CustomEvent('shelf_banner_update'));
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
          <h1 style={{ fontSize: '24px', fontWeight: '800', color: 'var(--ink)', display: 'flex', alignItems: 'center', gap: '10px' }}>
            🖼️ Storefront Hero &amp; Banners Manager
            <span style={{ fontSize: '12px', background: 'var(--green-pale)', color: 'var(--green-deep)', border: '1px solid var(--line)', padding: '3px 10px', borderRadius: '999px', fontWeight: '700' }}>
              {slides.filter(s => s.active).length} Active Slides
            </span>
          </h1>
          <p style={{ fontSize: '13px', color: 'var(--muted)', marginTop: '4px' }}>
            Directly control the public homepage carousel: customize headlines, background imagery, stickers, CTA buttons, and slide order.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <button
            type="button"
            onClick={handleAddSlide}
            style={{ background: '#ffffff', color: 'var(--ink)', border: '1px solid #d0dad0', borderRadius: '9px', padding: '9px 16px', fontSize: '12.5px', fontWeight: '700', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <Icon name="plus" size={16} /> Add New Slide
          </button>
          <button
            type="button"
            onClick={handleSaveAll}
            style={{ background: 'var(--green-deep)', color: '#fff', border: 'none', borderRadius: '9px', padding: '9px 20px', fontSize: '12.5px', fontWeight: '750', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            🚀 Save &amp; Publish Banners
          </button>
        </div>
      </div>

      {saveNotice && (
        <div style={{ background: '#dcfce7', border: '1px solid #86efac', color: '#15803d', padding: '10px 16px', borderRadius: '10px', fontSize: '13px', fontWeight: '700', marginBottom: '16px' }}>
          {saveNotice}
        </div>
      )}

      {/* Google Trend Engine & Header Campaign Control Bar */}
      <div style={{ background: 'var(--paper)', border: '1px solid var(--line)', borderRadius: '16px', padding: '20px', marginBottom: '22px', boxShadow: 'var(--shadow)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', marginBottom: '14px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '18px' }}>🔥</span>
              <strong style={{ fontSize: '15px', color: 'var(--ink)' }}>Google Trend Engine · Live Seasonal Header Campaign</strong>
              <span style={{ fontSize: '11px', background: trendCampaign.enabled ? '#eef5eb' : '#fee2e2', color: trendCampaign.enabled ? '#059669' : '#b91c1c', border: `1px solid ${trendCampaign.enabled ? '#c9dac5' : '#fca5a5'}`, padding: '2px 10px', borderRadius: '99px', fontWeight: '700' }}>
                {trendCampaign.enabled ? '● LIVE ON STOREFRONT' : '○ DISABLED'}
              </span>
            </div>
            <p style={{ fontSize: '12.5px', color: 'var(--muted)', marginTop: '4px' }}>
              Control the top animated announcement pill and seasonal curation. No out-of-date festivals appear unless you select them.
            </p>
          </div>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <button
              type="button"
              onClick={() => {
                const next = { ...trendCampaign, enabled: !trendCampaign.enabled };
                setTrendCampaign(next);
                localStorage.setItem('shelf_festive_config', JSON.stringify(next));
                window.dispatchEvent(new Event('shelf_banner_update'));
              }}
              style={{ background: trendCampaign.enabled ? '#fee2e2' : '#dcfce7', border: `1px solid ${trendCampaign.enabled ? '#fca5a5' : '#86efac'}`, color: trendCampaign.enabled ? '#b91c1c' : '#15803d', padding: '6px 12px', borderRadius: '8px', fontSize: '12px', fontWeight: '700', cursor: 'pointer' }}
            >
              {trendCampaign.enabled ? 'Disable Ticker' : 'Enable Ticker'}
            </button>
            <button
              type="button"
              onClick={handleSaveTrendCampaign}
              style={{ background: 'var(--green-deep)', border: 'none', color: '#fff', padding: '6px 14px', borderRadius: '8px', fontSize: '12px', fontWeight: '700', cursor: 'pointer' }}
            >
              Save Trend
            </button>
          </div>
        </div>

        {/* Quick Presets Strip */}
        <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '10px', marginBottom: '14px', alignItems: 'center' }}>
          <span style={{ fontSize: '11.5px', color: 'var(--muted)', fontWeight: '600', whiteSpace: 'nowrap' }}>Trend Presets:</span>
          {TREND_PRESETS.map((preset) => (
            <button
              key={preset.key}
              type="button"
              onClick={() => handleApplyTrendPreset(preset)}
              style={{
                background: trendCampaign.seasonKey === preset.key ? 'var(--green-deep)' : '#f4f8f3',
                border: '1px solid #d2dcd0',
                borderRadius: '99px',
                padding: '4px 12px',
                color: trendCampaign.seasonKey === preset.key ? '#fff' : 'var(--ink)',
                fontSize: '11.5px',
                fontWeight: '650',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                transition: 'all 0.18s ease'
              }}
            >
              {preset.name}
            </button>
          ))}
        </div>

        {/* Campaign Input Fields */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '11.5px', color: 'var(--ink)', marginBottom: '4px', fontWeight: '700' }}>Header Eyebrow Tag</label>
            <input
              value={trendCampaign.eyebrow}
              onChange={(e) => setTrendCampaign({ ...trendCampaign, eyebrow: e.target.value })}
              placeholder="e.g. 🌸 SPRING CAPSULE 2026"
              style={{ width: '100%', background: '#ffffff', border: '1px solid #d4ded2', borderRadius: '8px', padding: '8px 12px', color: 'var(--ink)', fontSize: '12.5px' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '11.5px', color: 'var(--ink)', marginBottom: '4px', fontWeight: '700' }}>Live Announcement Ticker Text</label>
            <input
              value={trendCampaign.ticker}
              onChange={(e) => setTrendCampaign({ ...trendCampaign, ticker: e.target.value })}
              placeholder="e.g. 🌸 Spring Wardrobe Drops Live · Tops from ₹299"
              style={{ width: '100%', background: '#ffffff', border: '1px solid #d4ded2', borderRadius: '8px', padding: '8px 12px', color: 'var(--ink)', fontSize: '12.5px' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '11.5px', color: 'var(--ink)', marginBottom: '4px', fontWeight: '700' }}>Filter Query on Click</label>
            <input
              value={trendCampaign.query}
              onChange={(e) => setTrendCampaign({ ...trendCampaign, query: e.target.value })}
              placeholder="e.g. tops or kurti (leave blank for all)"
              style={{ width: '100%', background: '#ffffff', border: '1px solid #d4ded2', borderRadius: '8px', padding: '8px 12px', color: 'var(--ink)', fontSize: '12.5px' }}
            />
          </div>
        </div>
      </div>

      {/* Main 2-Column Studio Grid: Editor on Left, Live Mockup on Right */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '20px', alignItems: 'start' }}>
        {/* Left Column: Slide List & Field Editor */}
        <div style={{ background: 'var(--paper)', border: '1px solid var(--line)', borderRadius: '16px', padding: '20px', boxShadow: 'var(--shadow)' }}>
          {/* Slide Tab Strip */}
          <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '12px', borderBottom: '1px solid var(--line)', marginBottom: '16px' }}>
            {slides.map((s, idx) => (
              <button
                key={s.id || idx}
                type="button"
                onClick={() => setActiveSlideIndex(idx)}
                style={{
                  background: activeSlideIndex === idx ? 'var(--green-deep)' : '#f4f8f3',
                  border: '1px solid #d2dcd0',
                  borderRadius: '8px',
                  padding: '8px 12px',
                  color: activeSlideIndex === idx ? '#fff' : 'var(--ink)',
                  fontSize: '12px',
                  fontWeight: '700',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  whiteSpace: 'nowrap',
                  opacity: s.active ? 1 : 0.6
                }}
              >
                <span>Slide {idx + 1}: {s.category}</span>
                {!s.active && <span style={{ fontSize: '9px', background: '#fef08a', color: '#854d0e', padding: '1px 5px', borderRadius: '3px' }}>Off</span>}
              </button>
            ))}
          </div>

          {/* Active Slide Form Editor */}
          {currentSlide && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '15px', fontWeight: '800', color: 'var(--green-deep)' }}>
                  Editing Slide {activeSlideIndex + 1} ({currentSlide.category})
                </span>
                <div style={{ display: 'flex', gap: '6px' }}>
                  <button
                    type="button"
                    onClick={() => handleMoveSlide(activeSlideIndex, -1)}
                    disabled={activeSlideIndex === 0}
                    style={{ background: '#ffffff', border: '1px solid #d0dad0', color: 'var(--ink)', padding: '4px 8px', borderRadius: '6px', fontSize: '11px', cursor: 'pointer', fontWeight: '650' }}
                  >
                    ⬆️ Move Up
                  </button>
                  <button
                    type="button"
                    onClick={() => handleMoveSlide(activeSlideIndex, 1)}
                    disabled={activeSlideIndex === slides.length - 1}
                    style={{ background: '#ffffff', border: '1px solid #d0dad0', color: 'var(--ink)', padding: '4px 8px', borderRadius: '6px', fontSize: '11px', cursor: 'pointer', fontWeight: '650' }}
                  >
                    ⬇️ Move Down
                  </button>
                  <button
                    type="button"
                    onClick={() => handleToggleActive(activeSlideIndex)}
                    style={{ background: currentSlide.active ? '#dcfce7' : '#fef08a', border: '1px solid #86efac', color: currentSlide.active ? '#15803d' : '#854d0e', padding: '4px 10px', borderRadius: '6px', fontSize: '11px', fontWeight: '700', cursor: 'pointer' }}
                  >
                    {currentSlide.active ? '● Active' : '○ Disabled'}
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDeleteSlide(activeSlideIndex)}
                    style={{ background: '#fee2e2', border: '1px solid #fca5a5', color: '#b91c1c', padding: '4px 8px', borderRadius: '6px', fontSize: '11px', cursor: 'pointer', fontWeight: '700' }}
                  >
                    🗑️
                  </button>
                </div>
              </div>

              {/* Form Fields */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ fontSize: '11.5px', color: 'var(--ink)', fontWeight: '700', display: 'block', marginBottom: '4px' }}>Category Name</label>
                  <input
                    type="text"
                    value={currentSlide.category || ''}
                    onChange={(e) => handleUpdateSlideField('category', e.target.value)}
                    style={{ width: '100%', borderRadius: '8px', padding: '8px 12px', background: '#ffffff', border: '1px solid #d4ded2', color: 'var(--ink)', fontSize: '12.5px' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '11.5px', color: 'var(--ink)', fontWeight: '700', display: 'block', marginBottom: '4px' }}>Top Kicker Label</label>
                  <input
                    type="text"
                    value={currentSlide.label || ''}
                    onChange={(e) => handleUpdateSlideField('label', e.target.value)}
                    style={{ width: '100%', borderRadius: '8px', padding: '8px 12px', background: '#ffffff', border: '1px solid #d4ded2', color: 'var(--ink)', fontSize: '12.5px' }}
                  />
                </div>
              </div>

              <div>
                <label style={{ fontSize: '11.5px', color: 'var(--ink)', fontWeight: '700', display: 'block', marginBottom: '4px' }}>Headline Title</label>
                <input
                  type="text"
                  value={currentSlide.title || ''}
                  onChange={(e) => handleUpdateSlideField('title', e.target.value)}
                  style={{ width: '100%', borderRadius: '8px', padding: '8px 12px', background: '#ffffff', border: '1px solid #d4ded2', color: 'var(--ink)', fontSize: '13px', fontWeight: '700' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '11.5px', color: 'var(--ink)', fontWeight: '700', display: 'block', marginBottom: '4px' }}>Subtitle Description</label>
                <textarea
                  rows={2}
                  value={currentSlide.subtitle || ''}
                  onChange={(e) => handleUpdateSlideField('subtitle', e.target.value)}
                  style={{ width: '100%', borderRadius: '8px', padding: '8px 12px', background: '#ffffff', border: '1px solid #d4ded2', color: 'var(--ink)', fontSize: '12.5px', resize: 'vertical' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ fontSize: '11.5px', color: 'var(--ink)', fontWeight: '700', display: 'block', marginBottom: '4px' }}>Sticker Badge</label>
                  <input
                    type="text"
                    value={currentSlide.sticker || ''}
                    onChange={(e) => handleUpdateSlideField('sticker', e.target.value)}
                    style={{ width: '100%', borderRadius: '8px', padding: '8px 12px', background: '#ffffff', border: '1px solid #d4ded2', color: 'var(--ink)', fontSize: '12.5px' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '11.5px', color: 'var(--ink)', fontWeight: '700', display: 'block', marginBottom: '4px' }}>CTA Button Label</label>
                  <input
                    type="text"
                    value={currentSlide.action || ''}
                    onChange={(e) => handleUpdateSlideField('action', e.target.value)}
                    style={{ width: '100%', borderRadius: '8px', padding: '8px 12px', background: '#ffffff', border: '1px solid #d4ded2', color: 'var(--ink)', fontSize: '12.5px' }}
                  />
                </div>
              </div>

              {/* Background Photo Selector */}
              <div>
                <label style={{ fontSize: '11.5px', color: 'var(--ink)', fontWeight: '700', display: 'block', marginBottom: '4px' }}>Background Photo URL</label>
                <input
                  type="text"
                  value={currentSlide.image || ''}
                  onChange={(e) => handleUpdateSlideField('image', e.target.value)}
                  placeholder="https://images.meesho.com/..."
                  style={{ width: '100%', borderRadius: '8px', padding: '8px 12px', background: '#ffffff', border: '1px solid #d4ded2', color: 'var(--ink)', fontSize: '12.5px' }}
                />
                
                {/* Quick Catalog Image Picker */}
                <div style={{ marginTop: '8px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--muted)', fontWeight: '600' }}>Or pick from catalog products:</span>
                  <div style={{ display: 'flex', gap: '6px', overflowX: 'auto', marginTop: '4px', paddingBottom: '4px' }}>
                    {products.slice(0, 10).map((p) => (
                      <img
                        key={p.id}
                        src={p.image}
                        alt=""
                        onClick={() => handleUpdateSlideField('image', p.image)}
                        style={{ width: '36px', height: '44px', objectFit: 'cover', borderRadius: '4px', cursor: 'pointer', border: currentSlide.image === p.image ? '2px solid var(--green-deep)' : '1px solid var(--line)' }}
                      />
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Live Interactive Mockup Preview */}
        <div style={{ background: 'var(--paper)', border: '1px solid var(--line)', borderRadius: '16px', padding: '20px', boxShadow: 'var(--shadow)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <span style={{ fontSize: '14px', fontWeight: '800', color: 'var(--ink)' }}>👁️ Live Storefront Mockup Preview</span>
            <div style={{ display: 'flex', gap: '4px', background: '#edf3eb', borderRadius: '6px', padding: '2px' }}>
              <button
                type="button"
                onClick={() => setPreviewDevice('desktop')}
                style={{ background: previewDevice === 'desktop' ? 'var(--green-deep)' : 'transparent', color: previewDevice === 'desktop' ? '#fff' : 'var(--ink)', border: 'none', padding: '4px 10px', borderRadius: '5px', fontSize: '11px', cursor: 'pointer', fontWeight: '700' }}
              >
                🖥️ Desktop
              </button>
              <button
                type="button"
                onClick={() => setPreviewDevice('mobile')}
                style={{ background: previewDevice === 'mobile' ? 'var(--green-deep)' : 'transparent', color: previewDevice === 'mobile' ? '#fff' : 'var(--ink)', border: 'none', padding: '4px 10px', borderRadius: '5px', fontSize: '11px', cursor: 'pointer', fontWeight: '700' }}
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
