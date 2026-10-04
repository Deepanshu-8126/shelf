import React, { useState, useEffect, useMemo } from 'react';
import Icon from './Icon.jsx';
import { cleanDisplayTitle } from './ProductCard.jsx';

function money(v) {
  return `₹${Number(v || 0).toLocaleString('en-IN')}`;
}

export default function AdminWishlinkManager({
  products = [],
  onUpdateProduct,
  onToast = () => {}
}) {
  const [activeTab, setActiveTab] = useState('curator'); // 'curator' | 'profile'
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('All');
  const [config, setConfig] = useState({
    creatorName: 'Deepanshu',
    handle: '@deepanshu.fashion',
    bio: 'Viral Meesho finds, aesthetic streetwear & reel-tested outfits ✨ Tap to shop on Meesho or book via WhatsApp COD!',
    avatarUrl: '',
    instagramUrl: 'https://instagram.com',
    youtubeUrl: '',
    telegramUrl: 'https://t.me/ubstabot',
    defaultActionMode: 'dual'
  });
  const [savingConfig, setSavingConfig] = useState(false);
  const [editingImageId, setEditingImageId] = useState(null);
  const [customImageUrl, setCustomImageUrl] = useState('');

  // Fetch Wishlink settings from backend API
  useEffect(() => {
    fetch('/api/wishlink/config')
      .then((res) => res.json())
      .then((data) => {
        if (data.success && data.config) {
          setConfig((prev) => ({ ...prev, ...data.config }));
        }
      })
      .catch(() => {});
  }, []);

  const handleSaveConfig = async (e) => {
    e.preventDefault();
    setSavingConfig(true);
    try {
      const res = await fetch('/api/wishlink/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config })
      });
      const data = await res.json();
      if (data.success) {
        onToast('✓ Wishlink Creator profile saved successfully!');
      }
    } catch (err) {
      onToast('⚠️ Could not save settings: ' + err.message);
    } finally {
      setSavingConfig(false);
    }
  };

  const handleToggleWishlink = async (product) => {
    const isCurrentlyFeatured = Boolean(product.wishlink_featured !== false);
    const nextState = !isCurrentlyFeatured;
    await onUpdateProduct?.(product.id, { wishlink_featured: nextState });
    onToast(nextState ? `✨ Added "${cleanDisplayTitle(product.title).slice(0, 25)}" to Wishlink Haul` : `Removed from Wishlink Haul`);
  };

  const handleSaveAestheticImage = async (productId) => {
    if (!customImageUrl.trim()) return;
    await onUpdateProduct?.(productId, { wishlink_image: customImageUrl.trim() });
    setEditingImageId(null);
    setCustomImageUrl('');
    onToast('✓ Aesthetic Wishlink image updated!');
  };

  const handleResetImage = async (productId) => {
    await onUpdateProduct?.(productId, { wishlink_image: '' });
    onToast('Restored default catalog image');
  };

  const handleSetActionMode = async (productId, mode) => {
    await onUpdateProduct?.(productId, { action_mode: mode });
    onToast(`Action mode updated to "${mode}"`);
  };

  // Only Meesho & trending outfits can be featured on Wishlink
  const meeshoProducts = useMemo(() => {
    return products.filter((p) => {
      const s = String(p.store || '').toLowerCase();
      return s === 'meesho' || !p.store || s === 'other';
    });
  }, [products]);

  const categories = useMemo(() => {
    const set = new Set(['All']);
    meeshoProducts.forEach((p) => {
      if (p.category) set.add(p.category);
    });
    return Array.from(set);
  }, [meeshoProducts]);

  const filteredProducts = useMemo(() => {
    return meeshoProducts.filter((p) => {
      if (search.trim()) {
        const q = search.toLowerCase();
        const matchesTitle = (p.title || '').toLowerCase().includes(q);
        const matchesCat = (p.category || '').toLowerCase().includes(q);
        const matchesId = (p.id || '').toLowerCase().includes(q);
        if (!matchesTitle && !matchesCat && !matchesId) return false;
      }
      if (categoryFilter !== 'All' && (p.category || '') !== categoryFilter) {
        return false;
      }
      return true;
    });
  }, [meeshoProducts, search, categoryFilter]);

  const featuredCount = useMemo(() => {
    return meeshoProducts.filter((p) => p.wishlink_featured !== false).length;
  }, [meeshoProducts]);

  return (
    <div className="standard-view" style={{ maxWidth: '1440px', margin: '0 auto', padding: '24px 20px' }}>
      {/* ── Top Header ── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 style={{ fontSize: '24px', fontWeight: 800, color: 'var(--ink)' }}>
              🌸 Wishlink Creator Haul Studio
            </h1>
            <span style={{ fontSize: '12px', background: 'rgba(236, 72, 153, 0.12)', color: '#db2777', border: '1px solid rgba(236, 72, 153, 0.25)', padding: '3px 10px', borderRadius: '999px', fontWeight: 700 }}>
              {featuredCount} Active on Bio
            </span>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--muted)', marginTop: '4px' }}>
            Stealth Influencer Haul Manager · Curate outfits, swap catalog pictures with aesthetic model looks, and route Dual Action buttons.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <a
            href="/#wishlink"
            target="_blank"
            rel="noreferrer"
            className="button button-dark"
            style={{ fontSize: '13px', fontWeight: 700, gap: '6px', textDecoration: 'none' }}
          >
            <span>🔗</span> Preview Live Wishlink Page ↗
          </a>
        </div>
      </div>

      {/* ── Navigation Tabs ── */}
      <div style={{ display: 'flex', gap: '10px', borderBottom: '1px solid var(--line)', marginBottom: '24px' }}>
        <button
          type="button"
          onClick={() => setActiveTab('curator')}
          style={{
            padding: '12px 18px',
            fontSize: '13.5px',
            fontWeight: activeTab === 'curator' ? 800 : 600,
            color: activeTab === 'curator' ? 'var(--ink)' : 'var(--muted)',
            borderBottom: activeTab === 'curator' ? '2px solid var(--ink)' : '2px solid transparent',
            background: 'none',
            border: 'none',
            cursor: 'pointer'
          }}
        >
          👗 Curate Outfits &amp; Aesthetic Photos ({meeshoProducts.length})
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('profile')}
          style={{
            padding: '12px 18px',
            fontSize: '13.5px',
            fontWeight: activeTab === 'profile' ? 800 : 600,
            color: activeTab === 'profile' ? 'var(--ink)' : 'var(--muted)',
            borderBottom: activeTab === 'profile' ? '2px solid var(--ink)' : '2px solid transparent',
            background: 'none',
            border: 'none',
            cursor: 'pointer'
          }}
        >
          👤 Creator Bio &amp; Social Handles
        </button>
      </div>

      {/* ── Tab 1: Curate Outfits ── */}
      {activeTab === 'curator' && (
        <div>
          {/* Controls Filter Bar */}
          <div style={{ display: 'flex', gap: '12px', marginBottom: '20px', flexWrap: 'wrap', alignItems: 'center' }}>
            <div style={{ flex: '1 1 280px' }}>
              <input
                type="text"
                placeholder="Search outfits by title or category..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                style={{ width: '100%', height: '42px', borderRadius: '10px', border: '1px solid var(--line)', padding: '0 14px', fontSize: '13px', background: 'var(--paper)', color: 'var(--ink)' }}
              />
            </div>

            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              style={{ height: '42px', borderRadius: '10px', border: '1px solid var(--line)', padding: '0 14px', fontSize: '13px', background: 'var(--paper)', color: 'var(--ink)', cursor: 'pointer' }}
            >
              {categories.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          {/* Outfits List Table */}
          <div style={{ background: 'var(--paper)', borderRadius: '16px', border: '1px solid var(--line)', overflow: 'hidden' }}>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
                <thead>
                  <tr style={{ background: 'var(--canvas)', borderBottom: '1px solid var(--line)', color: 'var(--ink-soft)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    <th style={{ padding: '14px 16px', width: '90px' }}>Wishlink</th>
                    <th style={{ padding: '14px 16px', width: '220px' }}>Photo (Default vs Aesthetic)</th>
                    <th style={{ padding: '14px 16px' }}>Outfit Title &amp; Category</th>
                    <th style={{ padding: '14px 16px', width: '140px' }}>Pricing &amp; Margin</th>
                    <th style={{ padding: '14px 16px', width: '180px' }}>Action Button Mode</th>
                    <th style={{ padding: '14px 16px', textAlign: 'right', width: '120px' }}>Quick Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredProducts.map((p) => {
                    const isFeatured = p.wishlink_featured !== false;
                    const hasAestheticImg = Boolean(p.wishlink_image);
                    const displayImg = p.wishlink_image || p.image;
                    const currentMode = p.action_mode || config.defaultActionMode || 'dual';
                    const baseCost = p.base_cost || p.baseCost || Math.round((p.price || 499) * 0.70);
                    const margin = Math.max(0, (p.price || 499) - baseCost);

                    return (
                      <tr key={p.id} style={{ borderBottom: '1px solid var(--line)', verticalAlign: 'top', background: isFeatured ? 'transparent' : 'rgba(148, 163, 184, 0.05)' }}>
                        {/* Toggle Active */}
                        <td style={{ padding: '14px 16px' }}>
                          <button
                            type="button"
                            onClick={() => handleToggleWishlink(p)}
                            style={{
                              padding: '5px 10px',
                              borderRadius: '999px',
                              fontSize: '11px',
                              fontWeight: 700,
                              cursor: 'pointer',
                              border: isFeatured ? '1px solid #16a34a' : '1px solid var(--line)',
                              background: isFeatured ? '#dcfce7' : 'var(--canvas)',
                              color: isFeatured ? '#15803d' : 'var(--muted)'
                            }}
                          >
                            {isFeatured ? '✓ Active' : 'Hidden'}
                          </button>
                        </td>

                        {/* Image Preview & Swap */}
                        <td style={{ padding: '14px 16px' }}>
                          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                            <img
                              src={displayImg}
                              alt=""
                              style={{ width: '56px', height: '70px', objectFit: 'cover', borderRadius: '8px', border: hasAestheticImg ? '2px solid #ec4899' : '1px solid var(--line)' }}
                              onError={(e) => { e.currentTarget.src = '/images/meesho-peach-short-kurti.webp'; }}
                            />
                            <div>
                              {hasAestheticImg ? (
                                <span style={{ fontSize: '10.5px', background: 'rgba(236, 72, 153, 0.15)', color: '#db2777', padding: '2px 6px', borderRadius: '4px', fontWeight: 700, display: 'inline-block' }}>
                                  ✨ Aesthetic Look
                                </span>
                              ) : (
                                <span style={{ fontSize: '10.5px', background: 'var(--canvas)', color: 'var(--muted)', padding: '2px 6px', borderRadius: '4px', display: 'inline-block' }}>
                                  Default Catalog
                                </span>
                              )}
                              <div style={{ marginTop: '4px' }}>
                                <button
                                  type="button"
                                  onClick={() => {
                                    setEditingImageId(editingImageId === p.id ? null : p.id);
                                    setCustomImageUrl(p.wishlink_image || '');
                                  }}
                                  style={{ background: 'none', border: 'none', color: 'var(--primary)', fontSize: '11px', fontWeight: 700, cursor: 'pointer', padding: 0 }}
                                >
                                  {editingImageId === p.id ? 'Cancel' : 'Swap Image ✎'}
                                </button>
                                {hasAestheticImg && (
                                  <button
                                    type="button"
                                    onClick={() => handleResetImage(p.id)}
                                    style={{ background: 'none', border: 'none', color: '#ef4444', fontSize: '10.5px', cursor: 'pointer', display: 'block', marginTop: '2px', padding: 0 }}
                                  >
                                    Reset to Default
                                  </button>
                                )}
                              </div>
                            </div>
                          </div>

                          {/* Quick URL Input for Image Swap */}
                          {editingImageId === p.id && (
                            <div style={{ marginTop: '10px', background: 'var(--canvas)', padding: '8px', borderRadius: '8px', border: '1px solid var(--line)' }}>
                              <input
                                type="url"
                                placeholder="Paste Pinterest/Instagram aesthetic image URL..."
                                value={customImageUrl}
                                onChange={(e) => setCustomImageUrl(e.target.value)}
                                style={{ width: '100%', fontSize: '11.5px', padding: '6px 8px', borderRadius: '6px', border: '1px solid var(--line)', marginBottom: '6px', background: 'var(--paper)', color: 'var(--ink)' }}
                              />
                              <button
                                type="button"
                                onClick={() => handleSaveAestheticImage(p.id)}
                                style={{ background: '#ec4899', color: '#fff', border: 'none', borderRadius: '6px', padding: '4px 10px', fontSize: '11px', fontWeight: 700, cursor: 'pointer' }}
                              >
                                Save Photo
                              </button>
                            </div>
                          )}
                        </td>

                        {/* Title & Category */}
                        <td style={{ padding: '14px 16px' }}>
                          <strong style={{ fontSize: '13px', color: 'var(--ink)', display: 'block' }}>
                            {cleanDisplayTitle(p.title)}
                          </strong>
                          <span style={{ fontSize: '11.5px', color: 'var(--muted)' }}>{p.category || 'Trending'}</span>
                        </td>

                        {/* Pricing & Margin */}
                        <td style={{ padding: '14px 16px' }}>
                          <strong style={{ fontSize: '13.5px', color: 'var(--ink)', display: 'block' }}>{money(p.price)}</strong>
                          <span style={{ fontSize: '11px', color: '#16a34a', fontWeight: 700, display: 'block' }}>
                            Margin: +{money(margin)}
                          </span>
                        </td>

                        {/* Action Mode */}
                        <td style={{ padding: '14px 16px' }}>
                          <select
                            value={currentMode}
                            onChange={(e) => handleSetActionMode(p.id, e.target.value)}
                            style={{ width: '100%', padding: '6px 8px', fontSize: '12px', borderRadius: '6px', border: '1px solid var(--line)', background: 'var(--paper)', color: 'var(--ink)', cursor: 'pointer' }}
                          >
                            <option value="dual">🛍️ Dual (Affiliate + COD)</option>
                            <option value="affiliate_only">🚀 Direct Affiliate Only</option>
                            <option value="reseller_only">💬 WhatsApp COD Only</option>
                          </select>
                        </td>

                        {/* Quick View Link */}
                        <td style={{ padding: '14px 16px', textAlign: 'right' }}>
                          <a
                            href={p.productUrl || p.affiliateUrl || `https://meesho.com`}
                            target="_blank"
                            rel="noreferrer"
                            style={{ fontSize: '12px', color: 'var(--ink)', textDecoration: 'none', fontWeight: 700 }}
                          >
                            Meesho ↗
                          </a>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ── Tab 2: Creator Profile Settings ── */}
      {activeTab === 'profile' && (
        <form onSubmit={handleSaveConfig} style={{ background: 'var(--paper)', borderRadius: '16px', border: '1px solid var(--line)', padding: '28px', maxWidth: '680px' }}>
          <h2 style={{ fontSize: '18px', fontWeight: 800, color: 'var(--ink)', marginBottom: '6px' }}>
            Creator Bio &amp; Public Branding
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--muted)', marginBottom: '20px' }}>
            This branding appears on your public Wishlink Creator Haul page (`/#wishlink`).
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label style={{ fontSize: '12.5px', fontWeight: 700, color: 'var(--ink)', display: 'block', marginBottom: '6px' }}>
                Creator Display Name
              </label>
              <input
                type="text"
                value={config.creatorName}
                onChange={(e) => setConfig({ ...config, creatorName: e.target.value })}
                style={{ width: '100%', height: '42px', borderRadius: '10px', border: '1px solid var(--line)', padding: '0 14px', fontSize: '13px', background: 'var(--canvas)', color: 'var(--ink)' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '12.5px', fontWeight: 700, color: 'var(--ink)', display: 'block', marginBottom: '6px' }}>
                Instagram / Social Handle
              </label>
              <input
                type="text"
                value={config.handle}
                onChange={(e) => setConfig({ ...config, handle: e.target.value })}
                style={{ width: '100%', height: '42px', borderRadius: '10px', border: '1px solid var(--line)', padding: '0 14px', fontSize: '13px', background: 'var(--canvas)', color: 'var(--ink)' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '12.5px', fontWeight: 700, color: 'var(--ink)', display: 'block', marginBottom: '6px' }}>
                Creator Bio Description
              </label>
              <textarea
                rows={3}
                value={config.bio}
                onChange={(e) => setConfig({ ...config, bio: e.target.value })}
                style={{ width: '100%', borderRadius: '10px', border: '1px solid var(--line)', padding: '10px 14px', fontSize: '13px', background: 'var(--canvas)', color: 'var(--ink)', resize: 'vertical' }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div>
                <label style={{ fontSize: '12.5px', fontWeight: 700, color: 'var(--ink)', display: 'block', marginBottom: '6px' }}>
                  Instagram Profile URL
                </label>
                <input
                  type="url"
                  value={config.instagramUrl}
                  onChange={(e) => setConfig({ ...config, instagramUrl: e.target.value })}
                  style={{ width: '100%', height: '42px', borderRadius: '10px', border: '1px solid var(--line)', padding: '0 14px', fontSize: '13px', background: 'var(--canvas)', color: 'var(--ink)' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '12.5px', fontWeight: 700, color: 'var(--ink)', display: 'block', marginBottom: '6px' }}>
                  Telegram Channel / Bot
                </label>
                <input
                  type="url"
                  value={config.telegramUrl}
                  onChange={(e) => setConfig({ ...config, telegramUrl: e.target.value })}
                  style={{ width: '100%', height: '42px', borderRadius: '10px', border: '1px solid var(--line)', padding: '0 14px', fontSize: '13px', background: 'var(--canvas)', color: 'var(--ink)' }}
                />
              </div>
            </div>

            <div>
              <label style={{ fontSize: '12.5px', fontWeight: 700, color: 'var(--ink)', display: 'block', marginBottom: '6px' }}>
                Default CTA Mode for New Outfits
              </label>
              <select
                value={config.defaultActionMode}
                onChange={(e) => setConfig({ ...config, defaultActionMode: e.target.value })}
                style={{ width: '100%', height: '42px', borderRadius: '10px', border: '1px solid var(--line)', padding: '0 14px', fontSize: '13px', background: 'var(--canvas)', color: 'var(--ink)' }}
              >
                <option value="dual">🛍️ Dual (Show both "Buy on Meesho App" &amp; "WhatsApp COD")</option>
                <option value="affiliate_only">🚀 Direct Affiliate Only (Customer self-purchases on Meesho)</option>
                <option value="reseller_only">💬 WhatsApp COD Only (Maximize reselling margin profit)</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={savingConfig}
              className="button button-dark"
              style={{ height: '44px', borderRadius: '12px', fontSize: '13px', fontWeight: 800, marginTop: '12px' }}
            >
              {savingConfig ? 'Saving...' : 'Save Creator Settings'}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
