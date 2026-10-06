import React, { useMemo, useState } from 'react';
import Icon from './Icon.jsx';

/* ─── Commission rates by store ───────────────────────────────────────── */
const COMMISSION_RATES = {
  Meesho: 0.10,   // 10% Meesho affiliate
  Myntra: 0.08,   // 8% Myntra affiliate
  Amazon: 0.07,   // 7% Amazon Associates
  Flipkart: 0.09, // 9% Flipkart affiliate
  Ajio: 0.08,     // 8% Ajio affiliate
  Nykaa: 0.09,    // 9% Nykaa affiliate
  default: 0.08,  // 8% generic
};

/* ─── Monthly traffic conversion scenarios ────────────────────────────── */
const SCENARIOS = [
  { label: 'Starter',    visitors: 300,   ctr: 0.08, cvr: 0.025, emoji: '🌱' },
  { label: 'Growing',   visitors: 1000,  ctr: 0.10, cvr: 0.030, emoji: '📈' },
  { label: 'Viral',     visitors: 5000,  ctr: 0.12, cvr: 0.035, emoji: '🚀' },
  { label: 'Influencer', visitors: 20000, ctr: 0.15, cvr: 0.040, emoji: '⭐' },
];

function money(v) {
  return `₹${Number(v || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
}

function getCommissionRate(store) {
  return COMMISSION_RATES[store] || COMMISSION_RATES.default;
}

export function getProductEarning(product) {
  const price = Number(product.price || 0);
  if (!price) return 0;
  return Math.round(price * getCommissionRate(product.store));
}

export default function EarningScopeModal({ products, creatorName = 'You', onClose }) {
  const [scenarioIdx, setScenarioIdx] = useState(1);
  const scenario = SCENARIOS[scenarioIdx];

  const stats = useMemo(() => {
    const validProducts = products.filter((p) => Number(p.price) > 0);
    const totalProducts = validProducts.length;
    const avgPrice = totalProducts
      ? validProducts.reduce((s, p) => s + Number(p.price), 0) / totalProducts
      : 0;

    // Store breakdown
    const byStore = {};
    validProducts.forEach((p) => {
      const store = p.store || 'Other';
      if (!byStore[store]) byStore[store] = { count: 0, commTotal: 0 };
      byStore[store].count++;
      byStore[store].commTotal += getProductEarning(p);
    });

    // Top earning products
    const topProducts = [...validProducts]
      .map((p) => ({ ...p, _earn: getProductEarning(p) }))
      .sort((a, b) => b._earn - a._earn)
      .slice(0, 5);

    // Scenario projection
    const avgCommPerProduct = totalProducts
      ? validProducts.reduce((s, p) => s + getProductEarning(p), 0) / totalProducts
      : 0;
    const clicks = Math.round(scenario.visitors * scenario.ctr);
    const orders = Math.round(clicks * scenario.cvr);
    const monthlyEarn = Math.round(orders * avgCommPerProduct);
    const yearlyEarn = monthlyEarn * 12;

    return { totalProducts, avgPrice, avgCommPerProduct, topProducts, byStore, clicks, orders, monthlyEarn, yearlyEarn };
  }, [products, scenarioIdx]);

  return (
    <div className="earn-scope-overlay" role="dialog" aria-modal="true" aria-label="Earning Scope Dashboard" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="earn-scope-modal">
        {/* Header */}
        <div className="earn-scope-header">
          <div className="earn-scope-title-group">
            <span className="earn-scope-icon">💰</span>
            <div>
              <h2 className="earn-scope-title">Earning Scope</h2>
              <p className="earn-scope-subtitle">Bhai, yeh tera asli potential hai 🔥</p>
            </div>
          </div>
          <button className="earn-scope-close" type="button" onClick={onClose} aria-label="Close earnings modal">
            <Icon name="x" size={20} />
          </button>
        </div>

        {/* KPI Strip */}
        <div className="earn-kpi-strip">
          <div className="earn-kpi-card earn-kpi-primary">
            <span className="earn-kpi-label">Monthly Potential</span>
            <span className="earn-kpi-value earn-kpi-big">{money(stats.monthlyEarn)}</span>
            <span className="earn-kpi-note">{scenario.emoji} {scenario.label} traffic</span>
          </div>
          <div className="earn-kpi-card">
            <span className="earn-kpi-label">Yearly Estimate</span>
            <span className="earn-kpi-value">{money(stats.yearlyEarn)}</span>
            <span className="earn-kpi-note">If sustained</span>
          </div>
          <div className="earn-kpi-card">
            <span className="earn-kpi-label">Products Listed</span>
            <span className="earn-kpi-value">{stats.totalProducts}</span>
            <span className="earn-kpi-note">Earning-eligible</span>
          </div>
          <div className="earn-kpi-card">
            <span className="earn-kpi-label">Avg Commission</span>
            <span className="earn-kpi-value">{money(stats.avgCommPerProduct)}</span>
            <span className="earn-kpi-note">Per order placed</span>
          </div>
        </div>

        {/* Scenario Switcher */}
        <div className="earn-scenario-section">
          <p className="earn-section-label">📊 Traffic Scenario — choose yours</p>
          <div className="earn-scenario-tabs">
            {SCENARIOS.map((s, idx) => (
              <button
                key={s.label}
                type="button"
                className={`earn-scenario-tab${scenarioIdx === idx ? ' is-active' : ''}`}
                onClick={() => setScenarioIdx(idx)}
              >
                <span className="earn-scenario-emoji">{s.emoji}</span>
                <span className="earn-scenario-name">{s.label}</span>
                <span className="earn-scenario-visitors">{s.visitors.toLocaleString('en-IN')}/mo</span>
              </button>
            ))}
          </div>
          <div className="earn-scenario-breakdown">
            <div className="earn-breakdown-item">
              <span>Monthly Visitors</span>
              <strong>{scenario.visitors.toLocaleString('en-IN')}</strong>
            </div>
            <span className="earn-breakdown-arrow">→</span>
            <div className="earn-breakdown-item">
              <span>Product Clicks</span>
              <strong>~{stats.clicks.toLocaleString('en-IN')}</strong>
            </div>
            <span className="earn-breakdown-arrow">→</span>
            <div className="earn-breakdown-item">
              <span>Orders</span>
              <strong>~{stats.orders}</strong>
            </div>
            <span className="earn-breakdown-arrow">→</span>
            <div className="earn-breakdown-item earn-breakdown-result">
              <span>You Earn</span>
              <strong>{money(stats.monthlyEarn)}</strong>
            </div>
          </div>
        </div>

        {/* Top Earning Products */}
        <div className="earn-top-products-section">
          <p className="earn-section-label">🏆 Your Top 5 Highest-Earning Products</p>
          <div className="earn-top-products-list">
            {stats.topProducts.map((product, idx) => (
              <div key={product.id} className="earn-top-product-row">
                <span className="earn-rank">#{idx + 1}</span>
                {product.image && (
                  <img
                    src={product.image}
                    alt={product.title}
                    className="earn-product-thumb"
                    onError={(e) => { e.currentTarget.style.display = 'none'; }}
                  />
                )}
                <div className="earn-product-info">
                  <span className="earn-product-name">{product.title?.slice(0, 48) || 'Product'}</span>
                  <span className="earn-product-store">{product.store} · {money(product.price)}</span>
                </div>
                <div className="earn-product-commission">
                  <span className="earn-commission-amount">{money(product._earn)}</span>
                  <span className="earn-commission-rate">{Math.round(getCommissionRate(product.store) * 100)}% commission</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Store Breakdown */}
        <div className="earn-store-breakdown-section">
          <p className="earn-section-label">🏪 Earnings by Platform</p>
          <div className="earn-store-grid">
            {Object.entries(stats.byStore).sort((a, b) => b[1].count - a[1].count).slice(0, 6).map(([store, data]) => (
              <div key={store} className="earn-store-card">
                <span className="earn-store-name">{store}</span>
                <span className="earn-store-rate">{Math.round((COMMISSION_RATES[store] || COMMISSION_RATES.default) * 100)}% commission</span>
                <span className="earn-store-count">{data.count} products</span>
                <span className="earn-store-potential">{money(data.commTotal)} pool</span>
              </div>
            ))}
          </div>
        </div>

        {/* Motivational Footer */}
        <div className="earn-scope-footer">
          <div className="earn-motivation-card">
            <span className="earn-motivation-icon">🎯</span>
            <div>
              <strong>Bhai, ek viral post = {money(stats.monthlyEarn * 3)} extra in a month!</strong>
              <p>These crazy clothes have real buying demand. Real users, real orders, real commissions. Start pushing traffic now. 🚀</p>
            </div>
          </div>
          <p className="earn-disclaimer">* Projections based on typical Indian affiliate conversion rates. Actual earnings depend on traffic quality, product demand, and platform commission structures.</p>
        </div>
      </div>
    </div>
  );
}
