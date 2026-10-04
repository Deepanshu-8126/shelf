import { createClient } from '@supabase/supabase-js';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const SUPABASE_URL = process.env.VITE_SUPABASE_URL || 'https://fniiiqowbvzcqaqbyjlb.supabase.co';
const SUPABASE_KEY = process.env.VITE_SUPABASE_ANON_KEY || 'sb_publishable_mO6eijXzG97m-I0bSBroPA_EhGXkINZ';

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

async function seed() {
  console.log('🚀 Reading local products from meesho-products.json...');
  const jsonPath = path.resolve(__dirname, '../src/meesho-products.json');
  if (!fs.existsSync(jsonPath)) {
    console.error('File not found:', jsonPath);
    return;
  }

  const raw = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));
  console.log(`Found ${raw.length} products to upload to Supabase...`);

  // Transform to Supabase schema
  const rows = raw.map((p, idx) => ({
    id: String(p.id || `meesho-${idx + 1}`),
    title: p.title || p.name || 'Trendy Fashion Item',
    category: p.category || 'Fashion',
    price: Number(p.price) || 299,
    original_price: Number(p.originalPrice || p.original_price) || (Number(p.price) || 299) * 1.3,
    rating: Number(p.rating) || 4.5,
    reviews_count: Number(p.reviewsCount || p.reviews_count) || 120,
    main_image: p.image || (Array.isArray(p.images) && p.images[0]) || '',
    images: Array.isArray(p.images) ? p.images : (p.image ? [p.image] : []),
    variations: Array.isArray(p.variations) ? p.variations : [],
    affiliate_link: p.affiliateLink || p.affiliate_link || '',
    store_name: p.store || 'Meesho',
    is_active: true,
  }));

  // Batch insert in chunks of 50
  const CHUNK_SIZE = 50;
  for (let i = 0; i < rows.length; i += CHUNK_SIZE) {
    const chunk = rows.slice(i, i + CHUNK_SIZE);
    console.log(`Uploading batch ${i + 1} to ${Math.min(i + CHUNK_SIZE, rows.length)}...`);
    
    const { data, error } = await supabase
      .from('products')
      .upsert(chunk, { onConflict: 'id' });

    if (error) {
      console.error(`Error uploading batch:`, error);
      return;
    }
  }

  console.log(`✅ SUCCESS! All ${rows.length} products uploaded to Supabase Cloud!`);
}

seed();
