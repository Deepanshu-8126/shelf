import React, { useEffect, useState } from 'react';
import Icon from './Icon.jsx';
import StoreBadge from './StoreBadge.jsx';
import { detectStore, STORES } from '../data.js';

const categoryCover = {
  Style: ['/images/linen-set.jpg', '/images/crossbody-bag.jpg', '/images/canvas-sneakers.jpg'],
  'Tops & Tunics': ['/images/meesho-side-dori-main.webp', '/images/meesho-western-square-print-top.webp', '/images/meesho-plaid-bow-peplum-top.webp'],
  Kurtis: ['/images/meesho-peach-short-kurti.webp', '/images/meesho-peach-embroidered-tunic.webp', '/images/meesho-kurti-dailywear-hgyhrb.webp'],
  'Ethnic Wear': ['/images/meesho-kurti-set.webp', '/images/meesho-peach-embroidered-tunic.webp', '/images/meesho-kurti-dailywear-hgyhrb.webp'],
  'Women Dresses': ['/images/meesho-dress-ae6lv9.webp', '/images/meesho-dress-gpc4vn.webp', '/images/meesho-dress-ibsnwj.webp'],
  Bottomwear: ['/images/linen-set.jpg', '/images/canvas-sneakers.jpg', '/images/crossbody-bag.jpg'],
  Innerwear: ['/images/linen-set.jpg', '/images/crossbody-bag.jpg', '/images/gold-hoops.jpg'],
  Beauty: ['/images/face-serum.jpg', '/images/gold-hoops.jpg', '/images/ceramic-vases.jpg'],
  Home: ['/images/ceramic-vases.jpg', '/images/linen-set.jpg', '/images/face-serum.jpg'],
  'Under ₹999': ['/images/meesho-earrings-combo.webp', '/images/meesho-canvas-tote.webp', '/images/ceramic-vases.jpg'],
  Winter: ['/images/meesho-hot-pink-puffer.webp', '/images/meesho-puffer-vest.webp', '/images/meesho-kashmiri-shawl.webp'],
};

export function AddProductModal({ product, collections, onClose, onSave }) {
  const [url, setUrl] = useState(product?.affiliateUrl || '');
  const [title, setTitle] = useState(product?.title || '');
  const [price, setPrice] = useState(product?.price ? String(product.price) : '');
  const [category, setCategory] = useState(product?.category || 'Fashion');
  const [store, setStore] = useState(product?.store || 'Meesho');
  const [collectionId, setCollectionId] = useState(product?.collectionId || collections[0]?.id || '');
  const detectedStore = detectStore(url);
  const isMeeshoInvite = detectedStore === 'Meesho' && url.toLowerCase().includes('/af_invite/');
  const isDirectListingUrl = Boolean(product?.productUrl && url.trim() === product.productUrl);
  const hasGeneratedMeeshoRoute = product?.store === 'Meesho' && Boolean(product?.productUrl) && !product?.affiliateUrl;
  const isMeeshoProductShortUrl = /^https?:\/\/(?:www\.)?meesho\.com\/s\/p\/[^/?#]+\/?(?:[?#]|$)/i.test(url.trim());
  const isPreformattedAffiliateUrl = /af_invite\/|ekaro\.in|earnkaro\.com|wishlink\.com|clnk\.in|cuelinks\.com|amzn\.to|bit\.ly|tinyurl\.com|[?&](?:referral|affid|tag)=/i.test(url.trim()) || (/meesho\.com\/s\//i.test(url.trim()) && !isMeeshoProductShortUrl);
  const newMeeshoDirectListing = !product && detectedStore === 'Meesho' && Boolean(url.trim()) && !isPreformattedAffiliateUrl;

  useEffect(() => {
    if (detectedStore) setStore(detectedStore);
  }, [detectedStore]);

  const submit = (event) => {
    event.preventDefault();
    onSave({
      id: product?.id,
      title: title.trim() || `${store} product pick`,
      subtitle: product?.subtitle || 'A new find, saved to your shelf',
      brand: product?.brand || store,
      store: detectedStore || store,
      category,
      collectionId,
      price: Number(price) || 599,
      oldPrice: product?.oldPrice || null,
      clicks: product?.clicks || 0,
      commission: product?.commission || 'Add rate',
      image: product?.image || '/images/crossbody-bag.jpg',
      imagePosition: product?.imagePosition || 'center',
      imageFit: product?.imageFit || 'cover',
      tint: product?.tint || 'sage',
      saved: product?.saved || false,
      productUrl: product?.productUrl || (isPreformattedAffiliateUrl ? '' : url.trim()),
      affiliateUrl: product ? url.trim() : (isPreformattedAffiliateUrl ? url.trim() : ''),
    });
  };

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className="modal-card" role="dialog" aria-modal="true" aria-labelledby="add-product-title">
        <div className="modal-topline">
          <span className="modal-icon"><Icon name="link" size={20} /></span>
          <button className="icon-button modal-close" type="button" onClick={onClose} aria-label="Close"><Icon name="close" size={18} /></button>
        </div>
        <p className="eyebrow">QUICK ADD</p>
        <h2 id="add-product-title">{product ? 'Add your affiliate link' : 'Add a pick to your shelf'}</h2>
        <p className="modal-copy">Paste the product or affiliate URL. We’ll detect Amazon, Flipkart, Myntra or Meesho for you.</p>
        <form onSubmit={submit}>
          <label className="field-label" htmlFor="product-url">Product / affiliate link</label>
          <div className="input-with-status">
            <input id="product-url" type="url" placeholder="https://www.meesho.com/..." value={url} onChange={(event) => setUrl(event.target.value)} required autoFocus />
            {detectedStore && <span className="detected-store"><StoreBadge store={detectedStore} /></span>}
          </div>
          {!detectedStore && (
            <div className="form-field">
              <label className="field-label" htmlFor="product-store">Marketplace (choose if the URL is shortened)</label>
              <select id="product-store" value={store} onChange={(event) => setStore(event.target.value)}>
                {STORES.map((storeName) => <option key={storeName}>{storeName}</option>)}
              </select>
            </div>
          )}
          <div className="field-grid">
            <div className="form-field">
              <label className="field-label" htmlFor="product-name">Pick name</label>
              <input id="product-name" type="text" placeholder="e.g. The perfect tote" value={title} onChange={(event) => setTitle(event.target.value)} />
            </div>
            <div className="form-field">
              <label className="field-label" htmlFor="product-price">Price (₹)</label>
              <input id="product-price" type="number" min="0" placeholder="599" value={price} onChange={(event) => setPrice(event.target.value)} />
            </div>
          </div>
          <div className="field-grid">
            <div className="form-field">
              <label className="field-label" htmlFor="product-category">Category</label>
              <select id="product-category" value={category} onChange={(event) => setCategory(event.target.value)}>
                <option>Fashion</option><option>Tops & Tunics</option><option>Kurtis</option><option>Ethnic Wear</option><option>Women Dresses</option><option>Bottomwear</option><option>Innerwear</option><option>Winter</option><option>Beauty</option><option>Home</option><option>Accessories</option>
              </select>
            </div>
            <div className="form-field">
              <label className="field-label" htmlFor="product-collection">Add to collection</label>
              <select id="product-collection" value={collectionId} onChange={(event) => setCollectionId(event.target.value)}>
                {collections.map((collection) => <option value={collection.id} key={collection.id}>{collection.title}</option>)}
              </select>
            </div>
          </div>
          {isMeeshoInvite ? (
            <div className="modal-note modal-note-warning"><Icon name="sparkles" size={16} /><span>This looks like your Meesho invite URL, not a product link. Keep it under Integrations and paste a unique Meesho product affiliate URL here.</span></div>
          ) : isDirectListingUrl ? (
            <div className="modal-note modal-note-warning"><Icon name="sparkles" size={16} /><span>This is the public product page, not a verified tracking link. Paste the unique creator-generated URL for this item.</span></div>
          ) : newMeeshoDirectListing ? (
            <div className="modal-note modal-note-warning"><Icon name="sparkles" size={16} /><span>This public Meesho URL will be saved separately and routed through your af_invite pattern. Check commission attribution in Meesho Creator after testing.</span></div>
          ) : hasGeneratedMeeshoRoute ? (
            <div className="modal-note modal-note-warning"><Icon name="sparkles" size={16} /><span>This pick currently uses the Meesho af_invite pattern from your script. The destination redirect was checked; commission attribution still needs verification in your Meesho Creator account.</span></div>
          ) : (
            <div className="modal-note"><Icon name="sparkles" size={16} /><span>Store detection is automatic. Shelf saves the URL as entered; confirm tracking in your creator dashboard.</span></div>
          )}
          <div className="modal-actions">
            <button className="button button-quiet" type="button" onClick={onClose}>Cancel</button>
            <button className="button button-primary" type="submit" disabled={isMeeshoInvite || isDirectListingUrl}>{product ? 'Save affiliate link' : 'Add to my shelf'} <Icon name="arrowRight" size={16} /></button>
          </div>
        </form>
      </section>
    </div>
  );
}

export function AddCollectionModal({ onClose, onSave }) {
  const [title, setTitle] = useState('');
  const [subtitle, setSubtitle] = useState('');
  const [category, setCategory] = useState('Style');

  const submit = (event) => {
    event.preventDefault();
    onSave({
      id: `collection-${Date.now()}`,
      title: title.trim(),
      subtitle: subtitle.trim() || 'A fresh little edit',
      category,
      coverImages: categoryCover[category] || categoryCover.Style,
      tint: ['Beauty', 'Tops & Tunics', 'Kurtis', 'Women Dresses'].includes(category) ? 'peach' : category === 'Home' ? 'lilac' : category === 'Under ₹999' ? 'butter' : category === 'Winter' ? 'blue' : 'sage',
    });
  };

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className="modal-card modal-card-small" role="dialog" aria-modal="true" aria-labelledby="add-collection-title">
        <div className="modal-topline">
          <span className="modal-icon modal-icon-sun"><Icon name="sparkles" size={20} /></span>
          <button className="icon-button modal-close" type="button" onClick={onClose} aria-label="Close"><Icon name="close" size={18} /></button>
        </div>
        <p className="eyebrow">MAKE A LITTLE CORNER</p>
        <h2 id="add-collection-title">New collection</h2>
        <p className="modal-copy">Give your next edit a name. You can add picks to it right after.</p>
        <form onSubmit={submit}>
          <div className="form-field">
            <label className="field-label" htmlFor="collection-name">Collection name</label>
            <input id="collection-name" type="text" placeholder="e.g. Sunday reset" value={title} onChange={(event) => setTitle(event.target.value)} required autoFocus />
          </div>
          <div className="form-field">
            <label className="field-label" htmlFor="collection-subtitle">A little description</label>
            <input id="collection-subtitle" type="text" placeholder="What belongs in this edit?" value={subtitle} onChange={(event) => setSubtitle(event.target.value)} />
          </div>
          <div className="form-field">
            <label className="field-label" htmlFor="collection-category">Cover mood</label>
            <select id="collection-category" value={category} onChange={(event) => setCategory(event.target.value)}>
              <option>Style</option><option>Tops & Tunics</option><option>Kurtis</option><option>Ethnic Wear</option><option>Women Dresses</option><option>Bottomwear</option><option>Innerwear</option><option>Winter</option><option>Beauty</option><option>Home</option><option>Under ₹999</option>
            </select>
          </div>
          <div className="modal-actions">
            <button className="button button-quiet" type="button" onClick={onClose}>Cancel</button>
            <button className="button button-primary" type="submit">Create collection <Icon name="arrowRight" size={16} /></button>
          </div>
        </form>
      </section>
    </div>
  );
}
