import React, { useState, useMemo } from 'react';
import Icon from '../ui/Icon.jsx';
import { getProductClickUrl } from '../../affiliate.js';
import { cleanDisplayTitle } from '../ui/ProductCard.jsx';
import InstantOrderModal from '../modals/InstantOrderModal.jsx';
import './WishlinkView.css';

function money(v) {
  return `₹${Number(v || 0).toLocaleString('en-IN')}`;
}

export function extractMeeshoCode(product) {
  if (!product) return 's-find';
  const url = product.productUrl || product.affiliateUrl || '';
  if (url) {
    const match = url.match(/\/p\/([a-zA-Z0-9]+)/i) || url.match(/[?&](?:p_id|ext_id)=([a-zA-Z0-9]+)/i);
    if (match && match[1]) {
      return `s-${match[1]}`;
    }
  }
  const cleanId = String(product.id || '').replace(/[^0-9]/g, '');
  return cleanId ? `s-${cleanId.slice(0, 9)}` : `s-${Math.abs(hashCode(product.title || 'meesho')) % 1000000}`;
}

function hashCode(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = (hash << 5) - hash + str.charCodeAt(i);
    hash |= 0;
  }
  return hash;
}

export default function WishlinkView({
  products = [],
  creatorName: defaultName = 'Deepanshu',
  handle: defaultHandle = '@deepanshu.fashion',
  bio: defaultBio = 'Viral Meesho finds, aesthetic streetwear & reel-tested outfits ✨ Tap to shop on Meesho or book via WhatsApp COD!',
  onInstantOrder,
  onToast = () => {}
}) {
  const [activeCategory, setActiveCategory] = useState('All');
  const [search, setSearch] = useState('');
  const [copiedCodeId, setCopiedCodeId] = useState(null);
  const [showExplainer, setShowExplainer] = useState(false);
  const [orderModalProduct, setOrderModalProduct] = useState(null);
  const [wishConfig, setWishConfig] = useState({
    creatorName: defaultName,
    handle: defaultHandle,
    bio: defaultBio,
    avatarUrl: '',
    instagramUrl: 'https://instagram.com',
    youtubeUrl: '',
    telegramUrl: 'https://t.me/ubstabot',
    defaultActionMode: 'dual'
  });

  // Fetch real creator settings from backend
  useEffect(() => {
    fetch('/api/wishlink/config')
      .then((res) => res.json())
      .then((data) => {
        if (data.success && data.config) {
          setWishConfig((prev) => ({ ...prev, ...data.config }));
        }
      })
      .catch(() => {});
  }, []);

  // Filter only products relevant to Meesho and creator hauls, respecting admin curation
  const meeshoCatalog = useMemo(() => {
    return products.filter((p) => {
      if (p.wishlink_featured === false) return false;
      const store = String(p.store || '').toLowerCase();
      return store === 'meesho' || !p.store || store === 'other';
    });
  }, [products]);

  const categories = useMemo(() => {
    return [
      'All',
      '🔥 Under ₹499',
      'Tops & Tunics',
      'Kurtis',
      'Ethnic Wear',
      'Women Dresses',
      'Accessories'
    ];
  }, []);

  const filteredProducts = useMemo(() => {
    return meeshoCatalog.filter((p) => {
      if (search.trim()) {
        const q = search.toLowerCase();
        const matchesTitle = (p.title || '').toLowerCase().includes(q);
        const matchesCat = (p.category || '').toLowerCase().includes(q);
        if (!matchesTitle && !matchesCat) return false;
      }
      if (activeCategory === '🔥 Under ₹499') {
        return Number(p.price || 0) <= 499;
      }
      if (activeCategory !== 'All') {
        return (p.category || '').toLowerCase() === activeCategory.toLowerCase();
      }
      return true;
    });
  }, [meeshoCatalog, activeCategory, search]);

  const handleCopyCode = (product, e) => {
    e.stopPropagation();
    const code = extractMeeshoCode(product);
    navigator.clipboard?.writeText(code);
    setCopiedCodeId(product.id);
    onToast(`📋 Meesho Code "${code}" copied! Search it directly in the Meesho App.`);
    setTimeout(() => setCopiedCodeId(null), 2500);
  };

  const handleShareWishlink = () => {
    const url = `${window.location.origin}${window.location.pathname}#wishlink`;
    navigator.clipboard?.writeText(url);
    onToast('🔗 Wishlink URL copied! Paste this in your Instagram Bio or YouTube description.');
  };

  return (
    <div className="wishlink-container">
      {/* ── Stealth Creator Profile Hero (No Store Backlinks) ── */}
      <div className="wishlink-profile-hero">
        <div className="wishlink-hero-content">
          <div className="wishlink-creator-identity">
            <div className="wishlink-avatar-wrap">
              {wishConfig.avatarUrl ? (
                <img src={wishConfig.avatarUrl} alt="" className="wishlink-avatar-img" />
              ) : (
                <div className="wishlink-avatar-fallback">✨</div>
              )}
              <span className="wishlink-verified-chip" title="Verified Fashion Curator">✓</span>
            </div>
            <div className="wishlink-creator-info">
              <h1>
                {wishConfig.creatorName}'s Wishlink Haul
                <span style={{ fontSize: '18px' }}>🌸</span>
              </h1>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                <span className="wishlink-handle-badge">
                  <Icon name="sparkles" size={13} /> {wishConfig.handle}
                </span>
                {wishConfig.instagramUrl && (
                  <a
                    href={wishConfig.instagramUrl}
                    target="_blank"
                    rel="noreferrer"
                    style={{ fontSize: '12px', color: 'var(--ink)', textDecoration: 'none', background: 'var(--canvas)', padding: '3px 8px', borderRadius: '6px', border: '1px solid var(--line)', fontWeight: 700 }}
                  >
                    Instagram ↗
                  </a>
                )}
                {wishConfig.telegramUrl && (
                  <a
                    href={wishConfig.telegramUrl}
                    target="_blank"
                    rel="noreferrer"
                    style={{ fontSize: '12px', color: '#2563eb', textDecoration: 'none', background: 'rgba(37, 99, 235, 0.08)', padding: '3px 8px', borderRadius: '6px', border: '1px solid rgba(37, 99, 235, 0.2)', fontWeight: 700 }}
                  >
                    Telegram Deals ↗
                  </a>
                )}
              </div>
              <p className="wishlink-bio-text">{wishConfig.bio}</p>
            </div>
          </div>

          <div className="wishlink-hero-actions">
            <button
              type="button"
              className="wishlink-btn-share"
              onClick={handleShareWishlink}
              title="Copy link for Instagram Bio"
            >
              <Icon name="link" size={15} /> Copy Bio Link
            </button>
            <button
              type="button"
              className="wishlink-btn-explainer"
              onClick={() => setShowExplainer(true)}
            >
              <Icon name="sparkles" size={15} /> How You Earn
            </button>
          </div>
        </div>
      </div>

      {/* ── Dual Monetization Explainer Strip ── */}
      <div className="wishlink-model-banner">
        <div className="wishlink-model-item">
          <span className="wishlink-model-icon">🛍️</span>
          <div>
            <strong>Direct Meesho Creator Links (100% Automated)</strong>
            <div style={{ fontSize: '12px', color: 'var(--muted)' }}>
              Shopper taps "Buy on Meesho" → Delivered by Meesho with 10-15% creator commission credited.
            </div>
          </div>
        </div>

        <div className="wishlink-model-item">
          <span className="wishlink-model-icon">📦</span>
          <div>
            <strong>Cash on Delivery Reselling (Zero Advance Payment)</strong>
            <div style={{ fontSize: '12px', color: 'var(--muted)' }}>
              Shopper books with COD → AI auto-fulfills on Meesho with reseller margin profit!
            </div>
          </div>
        </div>
      </div>

      {/* ── Filter & Search Controls ── */}
      <div className="wishlink-controls">
        <div className="wishlink-filter-pills">
          {categories.map((cat) => (
            <button
              key={cat}
              type="button"
              className={`wishlink-pill${activeCategory === cat ? ' is-active' : ''}`}
              onClick={() => setActiveCategory(cat)}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className="wishlink-search-box">
          <span className="wishlink-search-icon">
            <Icon name="search" size={16} />
          </span>
          <input
            type="text"
            className="wishlink-search-input"
            placeholder="Search hauls, sarees, dresses..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {/* ── Products Grid ── */}
      {filteredProducts.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px 20px', background: 'var(--paper)', borderRadius: '20px', border: '1px solid var(--line)' }}>
          <span style={{ fontSize: '40px', display: 'block', marginBottom: '10px' }}>🔍</span>
          <h3 style={{ fontSize: '18px', fontWeight: 800 }}>No Outfits Found</h3>
          <p style={{ fontSize: '13px', color: 'var(--muted)' }}>Try selecting another category or clear your search.</p>
        </div>
      ) : (
        <div className="wishlink-grid">
          {filteredProducts.map((product) => {
            const meeshoCode = extractMeeshoCode(product);
            const clickUrl = getProductClickUrl(product);
            const discountPct = product.oldPrice && product.price
              ? Math.round(((Number(product.oldPrice) - Number(product.price)) / Number(product.oldPrice)) * 100)
              : null;
            
            // Aesthetic Image Override (Pinterest / Instagram look)
            const displayImage = product.wishlink_image || product.image;
            const isAestheticLook = Boolean(product.wishlink_image);
            const actionMode = product.action_mode || wishConfig.defaultActionMode || 'dual';

            return (
              <div key={product.id} className="wishlink-card">
                <div className="wishlink-card-image-wrap">
                  <img
                    src={displayImage}
                    alt={product.title}
                    className="wishlink-card-img"
                    loading="lazy"
                    onError={(e) => { e.currentTarget.src = '/images/meesho-peach-short-kurti.webp'; }}
                  />
                  <span className="wishlink-badge-store">
                    {isAestheticLook ? '✨ Curated Look' : '🏪 Meesho Find'}
                  </span>
                  {discountPct && discountPct > 0 && (
                    <span className="wishlink-discount-pill">{discountPct}% OFF</span>
                  )}

                  {/* 1-Click Meesho Code Copier */}
                  <div className="wishlink-code-bar">
                    <span>Code: {meeshoCode}</span>
                    <button
                      type="button"
                      className="wishlink-code-btn"
                      onClick={(e) => handleCopyCode(product, e)}
                    >
                      {copiedCodeId === product.id ? '✓ Copied' : '📋 Copy'}
                    </button>
                  </div>
                </div>

                <div className="wishlink-card-body">
                  <span className="wishlink-product-category">{product.category || 'Trending'}</span>
                  <h2 className="wishlink-product-title" title={product.title}>
                    {cleanDisplayTitle(product.title)}
                  </h2>

                  <div className="wishlink-price-line">
                    <span className="wishlink-current-price">{money(product.price)}</span>
                    {product.oldPrice && <span className="wishlink-old-price">{money(product.oldPrice)}</span>}
                  </div>

                  {/* Dynamic Action Buttons Router */}
                  <div className="wishlink-actions-stack">
                    {/* Option A: Direct Affiliate purchase on Meesho */}
                    {(actionMode === 'dual' || actionMode === 'affiliate_only') && (
                      <a
                        href={clickUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="wishlink-buy-meesho-btn"
                        onClick={() => onToast?.(`🚀 Opening Meesho for "${cleanDisplayTitle(product.title).slice(0, 20)}..."`)}
                        style={{ width: '100%' }}
                      >
                        <Icon name="arrowUpRight" size={15} /> Buy on Meesho App
                      </a>
                    )}

                    {/* Option B: WhatsApp COD Reselling */}
                    {(actionMode === 'dual' || actionMode === 'reseller_only') && (
                      <button
                        type="button"
                        className="wishlink-reseller-btn"
                        onClick={() => onInstantOrder ? onInstantOrder(product) : setOrderModalProduct(product)}
                        style={{ width: '100%' }}
                      >
                        <span>💬 WhatsApp COD Order</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ── Instant Order Modal for WhatsApp COD Reselling ── */}
      {orderModalProduct && (
        <InstantOrderModal
          product={orderModalProduct}
          creatorName={creatorName}
          onClose={() => setOrderModalProduct(null)}
          onToast={onToast}
        />
      )}

      {/* ── Explainer Modal (Affiliate vs Reseller) ── */}
      {showExplainer && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(15, 23, 42, 0.65)',
            backdropFilter: 'blur(8px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
            padding: '20px'
          }}
          onClick={() => setShowExplainer(false)}
        >
          <div
            style={{
              background: 'var(--paper, #ffffff)',
              borderRadius: '24px',
              maxWidth: '560px',
              width: '100%',
              padding: '32px',
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
              position: 'relative'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h2 style={{ fontSize: '20px', fontWeight: 800, margin: 0, color: 'var(--ink)' }}>
                💰 How This Wishlink Page Makes You Money
              </h2>
              <button
                type="button"
                onClick={() => setShowExplainer(false)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--muted)' }}
              >
                <Icon name="x" size={20} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', fontSize: '13.5px', lineHeight: '1.5', color: 'var(--ink)' }}>
              <div style={{ background: 'rgba(163, 72, 162, 0.08)', padding: '16px', borderRadius: '16px', border: '1px solid rgba(163, 72, 162, 0.2)' }}>
                <strong style={{ color: '#a348a2', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '15px', marginBottom: '6px' }}>
                  🚀 Stream 1: Direct Meesho Affiliate Commission (Hands-Free)
                </strong>
                <p style={{ margin: 0, color: 'var(--muted)' }}>
                  Jab customer <strong>"Buy on Meesho"</strong> par click karta hai, woh aapke personal creator referral tag ke saath Meesho app/website par redirect ho jata hai. Meesho delivery, COD collection, aur returns khud handle karta hai. Meesho Creator Program aapko <strong>10% se 15% commission</strong> direct aapke bank account mein pay karta hai.
                </p>
              </div>

              <div style={{ background: 'rgba(34, 197, 94, 0.08)', padding: '16px', borderRadius: '16px', border: '1px solid rgba(34, 197, 94, 0.2)' }}>
                <strong style={{ color: '#15803d', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '15px', marginBottom: '6px' }}>
                  📦 Stream 2: Meesho Reseller Margin (Big Profit per Order)
                </strong>
                <p style={{ margin: 0, color: 'var(--muted)' }}>
                  Jo customers Meesho app use nahi karna chahte, woh <strong>"WhatsApp COD Order"</strong> par click karte hain. Aapko unka Name, Phone aur Address milta hai. Aap Meesho app mein ja kar woh product unke address par order karte hain aur apna <strong>Reseller Margin</strong> (e.g. ₹150–₹250) add kar dete hain. Meesho parcel par aapke store ka naam print karta hai aur COD cash collect karke margin aapke bank account mein bhejta hai.
                </p>
              </div>

              <div style={{ background: 'var(--canvas)', padding: '14px', borderRadius: '12px', fontSize: '12.5px', color: 'var(--muted)' }}>
                💡 <strong>Influencer Tip:</strong> Apne Instagram Bio aur YouTube video descriptions mein yeh URL daalo: <code>{window.location.origin}#wishlink</code>. Followers ko bolo: <em>"Link in bio for all Meesho codes & outfits!"</em>.
              </div>
            </div>

            <button
              type="button"
              onClick={() => setShowExplainer(false)}
              style={{
                width: '100%',
                marginTop: '24px',
                background: '#0f172a',
                color: '#fff',
                border: 'none',
                padding: '12px',
                borderRadius: '12px',
                fontWeight: 700,
                cursor: 'pointer'
              }}
            >
              Got it, let's start earning!
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
