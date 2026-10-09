import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = 'https://fniiiqowbvzcqaqbyjlb.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_mO6eijXzG97m-I0bSBroPA_EhGXkINZ';
export const MEESHO_CREATOR_LINK = 'https://www.meesho.com/afinvite/374453404:youtubelongform:12492338?p_id=542355935&ext_id=8ywkin&utm_source=youtube_long_form';

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

export const STATIC_PRODUCTS = [
  {
    id: 'shf-1',
    title: 'Minimalist Ruched Corset Crop Top',
    category: 'Tops & Tunics',
    price: 349,
    mrp: 999,
    discount: '65% OFF',
    rating: 4.8,
    reviewsCount: 342,
    image: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=800&q=80',
    affiliateUrl: 'https://www.meesho.com/afinvite/374453404:youtubelongform:12492338?extid=8ywkin&utmsource=instagramreels',
    meeshoCode: 's-8ywkin',
    isPublished: true,
  },
  {
    id: 'shf-2',
    title: 'Aesthetic Linen Flare Summer Dress',
    category: 'Women Dresses',
    price: 549,
    mrp: 1499,
    discount: '63% OFF',
    rating: 4.9,
    reviewsCount: 521,
    image: 'https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?auto=format&fit=crop&w=800&q=80',
    affiliateUrl: 'https://www.meesho.com/afinvite/374453404:youtubelongform:12492338?extid=ae6lv9&utmsource=instagramreels',
    meeshoCode: 's-ae6lv9',
    isPublished: true,
  },
  {
    id: 'shf-3',
    title: 'Heritage Floral Embroidered Kurti Set',
    category: 'Kurtis',
    price: 499,
    mrp: 1299,
    discount: '62% OFF',
    rating: 4.8,
    reviewsCount: 884,
    image: 'https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?auto=format&fit=crop&w=800&q=80',
    affiliateUrl: 'https://www.meesho.com/afinvite/374453404:youtubelongform:12492338?extid=hgyjn7&utmsource=instagramreels',
    meeshoCode: 's-hgyjn7',
    isPublished: true,
  },
  {
    id: 'shf-4',
    title: 'Cropped Bubble Sleeve Cardigan Top',
    category: 'Tops & Tunics',
    price: 399,
    mrp: 899,
    discount: '56% OFF',
    rating: 4.7,
    reviewsCount: 412,
    image: 'https://images.unsplash.com/photo-1509631179647-0177331693ae?auto=format&fit=crop&w=800&q=80',
    affiliateUrl: 'https://www.meesho.com/afinvite/374453404:youtubelongform:12492338?extid=hofzfw&utmsource=instagramreels',
    meeshoCode: 's-hofzfw',
    isPublished: true,
  },
  {
    id: 'shf-5',
    title: 'Sculpted Golden Drop Stud Earrings',
    category: 'Accessories',
    price: 189,
    mrp: 499,
    discount: '62% OFF',
    rating: 4.9,
    reviewsCount: 650,
    image: 'https://images.unsplash.com/photo-1630019852942-f89202989a59?auto=format&fit=crop&w=800&q=80',
    affiliateUrl: 'https://www.meesho.com/afinvite/374453404:youtubelongform:12492338?extid=5xcd6h&utmsource=instagramreels',
    meeshoCode: 's-5xcd6h',
    isPublished: true,
  },
  {
    id: 'shf-6',
    title: 'Heavy Organic Canvas Carryall Tote',
    category: 'Accessories',
    price: 270,
    mrp: 699,
    discount: '61% OFF',
    rating: 4.8,
    reviewsCount: 420,
    image: 'https://images.unsplash.com/photo-1544816155-12df9643f363?auto=format&fit=crop&w=800&q=80',
    affiliateUrl: 'https://www.meesho.com/afinvite/374453404:youtubelongform:12492338?extid=6t8k9b&utmsource=instagramreels',
    meeshoCode: 's-6t8k9b',
    isPublished: true,
  },
  {
    id: 'shf-7',
    title: 'Boxy Quilted Winter Puffer Vest',
    category: 'Winter',
    price: 599,
    mrp: 1699,
    discount: '65% OFF',
    rating: 4.6,
    reviewsCount: 198,
    image: 'https://images.unsplash.com/photo-1548883354-7622d03aca27?auto=format&fit=crop&w=800&q=80',
    affiliateUrl: 'https://www.meesho.com/afinvite/374453404:youtubelongform:12492338?extid=7ubl63&utmsource=instagramreels',
    meeshoCode: 's-7ubl63',
    isPublished: true,
  },
  {
    id: 'shf-8',
    title: 'Satin Backless Cocktail Slip Dress',
    category: 'Women Dresses',
    price: 649,
    mrp: 1799,
    discount: '64% OFF',
    rating: 4.9,
    reviewsCount: 310,
    image: 'https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?auto=format&fit=crop&w=800&q=80',
    affiliateUrl: 'https://www.meesho.com/afinvite/374453404:youtubelongform:12492338?extid=gpc4vn&utmsource=instagramreels',
    meeshoCode: 's-gpc4vn',
    isPublished: true,
  }
];

export async function getAllProducts() {
  try {
    const { data, error } = await supabase
      .from('products')
      .select('*')
      .eq('is_active', true)
      .order('created_at', { ascending: false });

    if (error || !data || data.length === 0) {
      return STATIC_PRODUCTS;
    }

    return data.map((item, idx) => {
      const fallback = STATIC_PRODUCTS[idx % STATIC_PRODUCTS.length];
      const extId = (item.product_url || item.affiliate_link || '').match(/\/p\/([a-zA-Z0-9]+)/)?.[1] || 'find';

      return {
        id: String(item.id),
        title: item.title || fallback.title,
        category: item.category || fallback.category,
        price: Number(item.price || fallback.price),
        mrp: Number(item.original_price || item.price * 2 || fallback.mrp),
        discount: item.original_price ? `${Math.round((1 - item.price / item.original_price) * 100)}% OFF` : fallback.discount,
        rating: Number(item.rating || 4.8),
        reviewsCount: Number(item.reviews_count || item.rating_count || fallback.reviewsCount),
        image: item.main_image || fallback.image,
        affiliateUrl: item.affiliate_link || item.affiliate_url || fallback.affiliateUrl,
        meeshoCode: `s-${extId}`,
        isPublished: true,
      };
    });
  } catch {
    return STATIC_PRODUCTS;
  }
}
