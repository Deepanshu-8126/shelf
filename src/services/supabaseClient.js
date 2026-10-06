import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || 'https://fniiiqowbvzcqaqbyjlb.supabase.co';
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || 'sb_publishable_mO6eijXzG97m-I0bSBroPA_EhGXkINZ';

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

/**
 * Fetch all active products directly from Supabase Cloud.
 */
export async function getCloudProducts() {
  try {
    const { data, error } = await supabase
      .from('products')
      .select('*')
      .eq('is_active', true)
      .order('created_at', { ascending: false });

    if (error) {
      console.warn('[Supabase] Error fetching cloud products, falling back to local:', error);
      return null;
    }

    if (!data || data.length === 0) {
      return null;
    }

    // Format products strictly from real database fields with ZERO manufactured fallbacks
    return data.map((item) => {
      const imagesList = Array.isArray(item.images) && item.images.length > 0
        ? item.images
        : (item.main_image ? [item.main_image] : []);

      return {
        id: String(item.id),
        title: item.title || 'Untitled Listing',
        category: item.category || null,
        price: item.price != null ? Number(item.price) : null,
        oldPrice: item.original_price != null ? Number(item.original_price) : null,
        originalPrice: item.original_price != null ? Number(item.original_price) : null,
        rating: item.rating != null ? Number(item.rating) : null,
        ratingCount: item.reviews_count != null ? Number(item.reviews_count) : (item.rating_count != null ? Number(item.rating_count) : null),
        reviewsCount: item.reviews_count != null ? Number(item.reviews_count) : (item.rating_count != null ? Number(item.rating_count) : null),
        image: item.main_image || (imagesList[0] || null),
        images: imagesList,
        galleryImages: imagesList,
        colors: Array.isArray(item.colors) ? item.colors : (Array.isArray(item.variations?.colors) ? item.variations.colors : null),
        sizes: Array.isArray(item.sizes) ? item.sizes : (Array.isArray(item.variations?.sizes) ? item.variations.sizes : null),
        affiliateUrl: item.affiliate_link || item.affiliate_url || '',
        productUrl: item.product_url || '',
        store: item.store_name || 'Meesho',
        isCloud: true,
      };
    });
  } catch (err) {
    console.error('[Supabase] Network error:', err);
    return null;
  }
}

/**
 * Submit an instant customer order to Supabase Cloud.
 */
export async function submitCloudOrder(orderData) {
  try {
    const { data, error } = await supabase.from('orders').insert([
      {
        product_id: orderData.productId,
        product_title: orderData.productTitle,
        customer_name: orderData.customerName,
        customer_phone: orderData.customerPhone,
        address: orderData.address,
        status: 'pending',
      },
    ]);

    if (error) throw error;
    return { success: true, data };
  } catch (err) {
    console.error('[Supabase] Failed to submit order:', err);
    return { success: false, error: err.message };
  }
}
