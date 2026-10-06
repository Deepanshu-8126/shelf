import React from 'react';
import Icon from './Icon.jsx';

const FALLBACK_COLLECTION_IMAGES = [
  '/images/meesho-side-dori-main.webp',
  '/images/meesho-dress-ae6lv9.webp',
  '/images/meesho-hot-pink-puffer.webp',
  '/images/meesho-peach-short-kurti.webp',
  '/images/meesho-kurti-set.webp',
  '/images/meesho-western-square-print-top.webp',
];

export default function CollectionCard({ collection, count, onClick, small = false }) {
  const seenImages = new Set();
  const rawImages = (Array.isArray(collection.coverImages) ? collection.coverImages : []).filter((image) => {
    const key = String(image || '').trim().split(/[?#]/)[0].toLowerCase();
    if (!key || seenImages.has(key)) return false;
    seenImages.add(key);
    return true;
  });

  const images = rawImages.length ? rawImages.slice(0, 3) : FALLBACK_COLLECTION_IMAGES.slice(0, 3);
  while (images.length < 3) {
    const nextFallback = FALLBACK_COLLECTION_IMAGES.find((fb) => !images.includes(fb)) || FALLBACK_COLLECTION_IMAGES[0];
    images.push(nextFallback);
  }

  const handleImageError = (e, index) => {
    e.currentTarget.onerror = null;
    e.currentTarget.src = FALLBACK_COLLECTION_IMAGES[index % FALLBACK_COLLECTION_IMAGES.length];
  };

  return (
    <button
      className={`collection-card${small ? ' collection-card-small' : ''} tint-${collection.tint || 'sage'}`}
      type="button"
      onClick={onClick}
      aria-label={`Open ${collection.title}, ${count} products`}
    >
      <div className="collection-cover">
        <div className={`collection-mosaic mosaic-layout-${images.length}`}>
          <div className="mosaic-main">
            <img
              src={images[0]}
              alt=""
              loading="lazy"
              onError={(e) => handleImageError(e, 0)}
            />
          </div>
          {images.length > 1 && (
            <div className="mosaic-side">
              {images.slice(1).map((image, idx) => (
                <img
                  key={image + idx}
                  src={image}
                  alt=""
                  loading="lazy"
                  onError={(e) => handleImageError(e, idx + 1)}
                />
              ))}
            </div>
          )}
        </div>
        <span className="collection-count-chip">{count} PICKS</span>
        <span className="collection-open-icon"><Icon name="arrowUpRight" size={17} /></span>
        <span className="collection-cover-wash" />
      </div>
      <div className="collection-card-info">
        <div>
          <h3>{collection.title}</h3>
          <p>{collection.subtitle}</p>
        </div>
        <span className="collection-arrow"><Icon name="arrowRight" size={17} /></span>
      </div>
    </button>
  );
}
