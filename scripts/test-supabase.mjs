import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = 'https://fniiiqowbvzcqaqbyjlb.supabase.co';
const SUPABASE_KEY = 'sb_publishable_mO6eijXzG97m-I0bSBroPA_EhGXkINZ';

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

async function verify() {
  const { count, data, error } = await supabase
    .from('products')
    .select('id, title, price, category', { count: 'exact' })
    .limit(3);

  console.log('Total Products in Supabase Cloud:', count);
  console.log('Sample Products:', data);
  if (error) console.error('Error:', error);
}

verify();
