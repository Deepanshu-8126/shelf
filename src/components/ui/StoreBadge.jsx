import React from 'react';
import { STORE_CONFIG } from '../../data.js';

export default function StoreBadge({ store, compact = false }) {
  const config = STORE_CONFIG[store] || { color: '#68726a', pale: '#eef1ec' };
  return (
    <span
      className={`store-badge${compact ? ' store-badge-compact' : ''}`}
      style={{ '--store-color': config.color, '--store-pale': config.pale }}
    >
      <span className="store-dot" />
      {!compact && <span>{store}</span>}
      {compact && <span className="store-badge-short">{store?.slice(0, 1)}</span>}
    </span>
  );
}
