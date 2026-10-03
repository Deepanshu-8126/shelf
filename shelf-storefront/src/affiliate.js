// Mirrors the Meesho af_invite route pattern supplied by the creator.
// A working redirect does not by itself confirm commission attribution; verify in Meesho Creator.
const MEESHO_AFFILIATE_ID = import.meta.env.VITE_MEESHO_AFFILIATE_ID || '374453404';
const MEESHO_SOURCE = import.meta.env.VITE_MEESHO_SOURCE || 'youtube_long_form';
const MEESHO_CAMPAIGN_ID = import.meta.env.VITE_MEESHO_CAMPAIGN_ID || '12492338';

export function buildMeeshoAffiliateUrl(rawUrl) {
  if (!rawUrl) return '';
  try {
    const productUrl = new URL(rawUrl);
    if (!/(^|\.)meesho\.com$/i.test(productUrl.hostname)) return rawUrl;
    if (productUrl.pathname.toLowerCase().includes('/af_invite/')) return rawUrl;
    // `/s/p/{ext_id}` is a direct product page, not an existing creator link.
    // Other Meesho shortlinks are left untouched because their destination is ambiguous.
    const shortProductExtId = productUrl.pathname.match(/^\/s\/p\/([^/]+)\/?$/i)?.[1];
    if (/\/s\//i.test(productUrl.pathname) && !shortProductExtId) return rawUrl;

    const pathProductId = productUrl.pathname.match(/\/p\/(\d+)(?:\/|$)/i)?.[1];
    const pathExtId = shortProductExtId || productUrl.pathname.match(/\/p\/([^/]+)\/?$/i)?.[1];
    const productId = productUrl.searchParams.get('p_id') || pathProductId || '';
    const extId = productUrl.searchParams.get('ext_id') || pathExtId || '';
    if (!productId && !extId) return rawUrl;

    const params = new URLSearchParams();
    if (productId) params.set('p_id', productId);
    if (extId) params.set('ext_id', extId);
    params.set('utm_source', MEESHO_SOURCE);
    return `https://www.meesho.com/af_invite/${MEESHO_AFFILIATE_ID}:${MEESHO_SOURCE}:${MEESHO_CAMPAIGN_ID}?${params.toString()}`;
  } catch {
    return rawUrl;
  }
}

export function getProductClickUrl(product) {
  if (!product) return '';
  if (product.affiliateUrl) return product.affiliateUrl;
  const store = String(product.store || 'Meesho').trim().toLowerCase();
  if (store === 'meesho' && product.productUrl) {
    const route = buildMeeshoAffiliateUrl(product.productUrl);
    if (route && route.includes('/af_invite/')) return route;
    return product.productUrl;
  }
  if (product.productUrl) return product.productUrl;
  if (store === 'meesho' || !product.store) {
    return `https://www.meesho.com/search?q=${encodeURIComponent(product.title || 'trending fashion')}`;
  }
  return '';
}
