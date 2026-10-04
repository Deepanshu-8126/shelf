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

    // Format products to match storefront schema
    return data.map((item) => ({
      id: item.id,
      title: item.title,
      category: item.category || 'Fashion',
      price: Number(item.price),
      originalPrice: item.original_price ? Number(item.original_price) : Number(item.price) * 1.3,
      rating: Number(item.rating) || 4.5,
      reviewsCount: item.reviews_count || 120,
      image: item.main_image,
      images: Array.isArray(item.images) ? item.images : [item.main_image],
      variations: Array.isArray(item.variations) ? item.variations : [],
      affiliateLink: item.affiliate_link || '',
      store: item.store_name || 'Meesho',
      isCloud: true,
    }));
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
