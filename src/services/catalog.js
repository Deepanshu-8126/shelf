import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = 'https://fniiiqowbvzcqaqbyjlb.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_mO6eijXzG97m-I0bSBroPA_EhGXkINZ';
export const MEESHO_CREATOR_LINK = 'https://www.meesho.com/afinvite/374453404:youtubelongform:12492338?p_id=542355935&ext_id=8ywkin&utm_source=youtube_long_form';

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

export const STATIC_PRODUCTS = [
  {
    id: 'p-meesho-side-dori-top',
    title: 'Yellow Ruched Side Dori Cropped Top',
    category: 'Tops & Tunics',
    price: 299,
    mrp: 899,
    discount: '67% OFF',
    rating: 4.8,
    reviewsCount: 342,
    image: '/images/meesho-side-dori-main.webp',
    images: ['/images/meesho-side-dori-main.webp', '/images/meesho-side-dori-main-view-front.webp', '/images/meesho-side-dori-main-view-side.webp'],
    sizes: ['XS', 'S', 'M', 'L', 'XL'],
    affiliateUrl: 'https://www.meesho.com/afinvite/374453404:youtubelongform:12492338?extid=8ywkin&utmsource=instagramreels',
    meeshoCode: 's-8ywkin',
    isPublished: true,
  },
  {
    id: 'p-meesho-peach-kurti',
    title: 'Peach Embroidered Dailywear Short Kurti',
    category: 'Kurtis',
    price: 349,
    mrp: 999,
    discount: '65% OFF',
    rating: 4.7,
    reviewsCount: 521,
    image: '/images/meesho-peach-short-kurti.webp',
    images: ['/images/meesho-peach-short-kurti.webp', '/images/meesho-peach-embroidered-tunic.webp'],
    sizes: ['S', 'M', 'L', 'XL', 'XXL'],
    affiliateUrl: 'https://www.meesho.com/afinvite/374453404:youtubelongform:12492338?extid=hgyhrb&utmsource=instagramreels',
    meeshoCode: 's-hgyhrb',
    isPublished: true,
  },
  {
    id: 'p-meesho-kurti-set',
    title: 'Ethnic Floral Printed Cotton Kurti Set',
    category: 'Ethnic Wear',
    price: 549,
    mrp: 1499,
    discount: '63% OFF',
    rating: 4.9,
    reviewsCount: 884,
    image: '/images/meesho-kurti-set.webp',
    images: ['/images/meesho-kurti-set.webp', '/images/meesho-kurti-dailywear-hgyjn7.webp'],
    sizes: ['M', 'L', 'XL', 'XXL'],
    affiliateUrl: 'https://www.meesho.com/afinvite/374453404:youtubelongform:12492338?extid=hgyjn7&utmsource=instagramreels',
    meeshoCode: 's-hgyjn7',
    isPublished: true,
  },
  {
    id: 'p-meesho-dress-ae6lv9',
    title: 'Aesthetic Floral Flare One-Piece Dress',
    category: 'Women Dresses',
    price: 499,
    mrp: 1299,
    discount: '62% OFF',
    rating: 4.8,
    reviewsCount: 412,
    image: '/images/meesho-dress-ae6lv9.webp',
    images: ['/images/meesho-dress-ae6lv9.webp', '/images/meesho-dress-gpc4vn.webp', '/images/meesho-dress-ibsnwj.webp'],
    sizes: ['XS', 'S', 'M', 'L'],
    affiliateUrl: 'https://www.meesho.com/afinvite/374453404:youtubelongform:12492338?extid=ae6lv9&utmsource=instagramreels',
    meeshoCode: 's-ae6lv9',
    isPublished: true,
  },
  {
    id: 'p-meesho-pink-puffer',
    title: 'Hot Pink Cropped Winter Puffer Jacket',
    category: 'Winter',
    price: 599,
    mrp: 1699,
    discount: '65% OFF',
    rating: 4.6,
    reviewsCount: 198,
    image: '/images/meesho-hot-pink-puffer.webp',
    images: ['/images/meesho-hot-pink-puffer.webp', '/images/meesho-puffer-vest.webp', '/images/meesho-black-cardigan.webp'],
    sizes: ['S', 'M', 'L', 'XL'],
    affiliateUrl: 'https://www.meesho.com/afinvite/374453404:youtubelongform:12492338?extid=7ubl63&utmsource=instagramreels',
    meeshoCode: 's-7ubl63',
    isPublished: true,
  },
  {
    id: 'p-meesho-flower-earrings',
    title: 'Delicate Floral Stud & Hoop Earrings Set',
    category: 'Accessories',
    price: 189,
    mrp: 499,
    discount: '62% OFF',
    rating: 4.7,
    reviewsCount: 650,
    image: '/images/meesho-flower-earrings.webp',
    images: ['/images/meesho-flower-earrings.webp', '/images/meesho-earrings-combo.webp'],
    sizes: ['Free Size'],
    affiliateUrl: 'https://www.meesho.com/afinvite/374453404:youtubelongform:12492338?extid=5xcd6h&utmsource=instagramreels',
    meeshoCode: 's-5xcd6h',
    isPublished: true,
  },
  {
    id: 'p-meesho-canvas-tote',
    title: 'Aesthetic Printed Heavy Canvas Carryall Tote',
    category: 'Accessories',
    price: 270,
    mrp: 699,
    discount: '61% OFF',
    rating: 4.8,
    reviewsCount: 420,
    image: '/images/meesho-canvas-tote.webp',
    images: ['/images/meesho-canvas-tote.webp'],
    sizes: ['One Size'],
    affiliateUrl: 'https://www.meesho.com/afinvite/374453404:youtubelongform:12492338?extid=6t8k9b&utmsource=instagramreels',
    meeshoCode: 's-6t8k9b',
    isPublished: true,
  },
  {
    id: 'p-meesho-black-cardigan',
    title: 'Ribbed Knit Y2K Crop Cardigan Top',
    category: 'Tops & Tunics',
    price: 379,
    mrp: 899,
    discount: '58% OFF',
    rating: 4.8,
    reviewsCount: 310,
    image: '/images/meesho-black-cardigan.webp',
    images: ['/images/meesho-black-cardigan.webp', '/images/meesho-casual-beige-girls-top.webp'],
    sizes: ['S', 'M', 'L'],
    affiliateUrl: 'https://www.meesho.com/afinvite/374453404:youtubelongform:12492338?extid=hofzfw&utmsource=instagramreels',
    meeshoCode: 's-hofzfw',
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

    return data.map((item) => {
      const imagesList = Array.isArray(item.images) && item.images.length > 0
        ? item.images
        : (item.main_image ? [item.main_image] : []);

      const extId = (item.product_url || item.affiliate_link || '').match(/\/p\/([a-zA-Z0-9]+)/)?.[1] || 'item';

      return {
        id: String(item.id),
        title: item.title || 'Curated Fashion Find',
        category: item.category || 'Tops & Tunics',
        price: Number(item.price || 399),
        mrp: Number(item.original_price || item.price * 2 || 999),
        discount: item.original_price ? `${Math.round((1 - item.price / item.original_price) * 100)}% OFF` : '50% OFF',
        rating: Number(item.rating || 4.8),
        reviewsCount: Number(item.reviews_count || item.rating_count || 120),
        image: item.main_image || imagesList[0] || '/images/meesho-dress-ae6lv9.webp',
        images: imagesList.length > 0 ? imagesList : ['/images/meesho-dress-ae6lv9.webp'],
        sizes: Array.isArray(item.sizes) ? item.sizes : ['S', 'M', 'L', 'XL'],
        affiliateUrl: item.affiliate_link || item.affiliate_url || MEESHO_CREATOR_LINK,
        meeshoCode: `s-${extId}`,
        isPublished: true,
      };
    });
  } catch {
    return STATIC_PRODUCTS;
  }
}
