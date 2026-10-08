import React from 'react';

export default function ShelfHeader({ title, onBack, onShare }) {
  return (
    <header className="shelf-header-bar" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', background: 'rgba(255,255,255,0.9)', backdropFilter: 'blur(10px)', borderBottom: '1px solid rgba(0,0,0,0.06)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {onBack && (
          <button type="button" onClick={onBack} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '18px', padding: '4px' }}>
            ←
          </button>
        )}
        <span style={{ fontWeight: '700', fontSize: '15px' }}>{title || 'shelf.'}</span>
      </div>
      {onShare && (
        <button type="button" onClick={onShare} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '16px' }}>
          🔗
        </button>
      )}
    </header>
  );
}
