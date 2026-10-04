import React, { useEffect, useMemo, useRef, useState } from 'react';
import Icon from './Icon.jsx';
import ProductCard from './ProductCard.jsx';
import Pagination from './Pagination.jsx';
import CollectionCard from './CollectionCard.jsx';
import InstantOrderModal from './InstantOrderModal.jsx';
import ProductDetailModal from './ProductDetailModal.jsx';
import ProductPage from './ProductPage.jsx';
const OutfitBuilderModal = React.lazy(() => import('./OutfitBuilderModal.jsx'));
const AIStylistModal = React.lazy(() => import('./AIStylistModal.jsx'));
const InteractiveShowroomModal = React.lazy(() => import('./InteractiveShowroomModal.jsx'));
const VirtualTryOnModal = React.lazy(() => import('./VirtualTryOnModal.jsx'));
const EarningScopeModal = React.lazy(() => import('./EarningScopeModal.jsx'));
const GenZStudioModal = React.lazy(() => import('./GenZStudioModal.jsx'));
import { getProductClickUrl } from '../affiliate.js';

const HERO_SLIDE_COPY = {
  'Tops & Tunics': {
    label: 'TOPS & Y2K EDITS',
    title: 'Effortless layers, cute details',
    subtitle: 'Corset crops, ribbed knits & everyday chic.',
    sticker: 'TRENDING TOPS',
    action: 'Explore tops',
    theme: 'sage',
  },
  Kurtis: {
    label: 'ETHNIC & KURTIS',
    title: 'Heritage prints, modern ease',
    subtitle: 'Floral anarkalis, luxury sets & festive charm.',
    sticker: 'CURATED ETHNIC',
    action: 'Explore kurtis',
    theme: 'lilac',
  },
  'Women Dresses': {
    label: 'DRESSES & BODYCON',
    title: 'Main-character plans, sorted',
    subtitle: 'Ruched bodycons, satin maxis & party silhouettes.',
    sticker: 'SIGNATURE DRESSES',
    action: 'Explore dresses',
    theme: 'peach',
  },
  Winter: {
    label: 'WINTER & KNITWEAR',
    title: 'Cold-weather luxury layers',
    subtitle: 'Oversized cardigans, fleece knits & chic puffers.',
    sticker: 'WINTER CAPSULE',
    action: 'Explore winter',
    theme: 'blue',
  },
};

export default function Storefront({ 
  products, 
  collections, 
  creatorName = 'Aanya Mehta', 
  handle = '@aanya.edit', 
  bio = 'Thoughtful finds for everyday life.', 
  onBack, 
  onShare, 
  showStudioControls = false,
  isAdmin = false,
  onDeleteProduct,
  onTogglePublish,
  onEditProduct
}) {
  const [storeFilter, setStoreFilter] = useState('All stores');
  const [categoryFilter, setCategoryFilter] = useState('All picks');
  const [collectionFilter, setCollectionFilter] = useState('all');
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);
  const [heroIndex, setHeroIndex] = useState(() => Math.floor(Math.random() * 4));
  const [heroPaused, setHeroPaused] = useState(false);
  const [theme, setTheme] = useState(() => {
    try {
      return localStorage.getItem('shelf_theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    } catch {
      return 'light';
    }
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    try {
      localStorage.setItem('shelf_theme', theme);
    } catch {}
  }, [theme]);

  const [orderModalProduct, setOrderModalProduct] = useState(null);
  const [detailProduct, setDetailProduct] = useState(null);
  const [outfitModalOpen, setOutfitModalOpen] = useState(false);
  const [stylistModalOpen, setStylistModalOpen] = useState(false);
  const [tryOnModalOpen, setTryOnModalOpen] = useState(false);
  const [showroomModalOpen, setShowroomModalOpen] = useState(false);
  const [tryOnInitialProduct, setTryOnInitialProduct] = useState(null);
  const [earningModalOpen, setEarningModalOpen] = useState(false);
  const [genzModalOpen, setGenzModalOpen] = useState(false);
  const [shopMenuOpen, setShopMenuOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const menuButtonRef = useRef(null);

  useEffect(() => {
    if (!mobileMenuOpen) return;
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setMobileMenuOpen(false);
        menuButtonRef.current?.focus();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [mobileMenuOpen]);

  const [festiveConfig, setFestiveConfig] = useState(() => {
    try {
      const saved = localStorage.getItem('shelf_festive_config');
      if (saved) return JSON.parse(saved);
    } catch {}
    return {
      enabled: true,
      seasonKey: 'trending',
      title: 'Trending Fits & Wardrobe Edits',
      eyebrow: '✦ VIRAL FINDS 2026',
      ticker: '✦ Fresh Aesthetic Drops & Curated Outfits · Handpicked from Top Creators',
      theme: 'sage',
      icon: '✦',
      query: '',
      videoUrl: ''
    };
  });

  useEffect(() => {
    const handleStorage = (e) => {
      if (e.key === 'shelf_festive_config') {
        try {
          if (e.newValue) setFestiveConfig(JSON.parse(e.newValue));
        } catch {}
      }
      if (e.key === 'shelf_wishlist') {
        try {
          if (e.newValue) setSavedIds(JSON.parse(e.newValue));
        } catch {}
      }
      if (e.key === 'shelf_admin_banners') {
        try {
          window.dispatchEvent(new CustomEvent('shelf_banner_update'));
        } catch {}
      }
    };
    const handleBannerUpdate = () => {
      try {
        const saved = localStorage.getItem('shelf_festive_config');
        if (saved) setFestiveConfig(JSON.parse(saved));
      } catch {}
    };
    window.addEventListener('storage', handleStorage);
    window.addEventListener('shelf_banner_update', handleBannerUpdate);
    return () => {
      window.removeEventListener('storage', handleStorage);
      window.removeEventListener('shelf_banner_update', handleBannerUpdate);
    };
  }, []);

  const activeSeason = useMemo(() => ({
    tag: festiveConfig.eyebrow || '✦ TRENDING CAPSULE 2026',
    label: festiveConfig.title || 'Curated fashion, daily aesthetic repeats & viral picks',
    pill: festiveConfig.ticker || '✦ Fresh Wardrobe Drops Live'
  }), [festiveConfig]);
  const [savedIds, setSavedIds] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('shelf_wishlist') || '[]');
    } catch {
      return [];
    }
  });
  const [savedOnly, setSavedOnly] = useState(false);
  const [activeProductId, setActiveProductId] = useState(() => {
    try {
      return new URLSearchParams(window.location.search).get('product') || null;
    } catch {
      return null;
    }
  });

  useEffect(() => {
    const handlePopState = () => {
      try {
        const prod = new URLSearchParams(window.location.search).get('product');
        setActiveProductId(prod);
      } catch {}
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const toggleSave = (id) => {
    setSavedIds((prev) => {
      const next = prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id];
      try {
        localStorage.setItem('shelf_wishlist', JSON.stringify(next));
      } catch {}
      return next;
    });
  };

  const pageSize = 12;
  const [genderMode, setGenderMode] = useState('women');
  const [isTransitioning, setIsTransitioning] = useState(false);

  const switchGender = (mode) => {
    if (mode === genderMode) return;
    setIsTransitioning(true);
    setCategoryFilter('All picks');
    setCollectionFilter('all');
    setQuery('');
    setTimeout(() => {
      setGenderMode(mode);
      setIsTransitioning(false);
    }, 180);
  };

  const categoryPriority = ['Women Dresses', 'Co-ord Sets', 'Blokecore & Jerseys', 'Tops & Tunics', 'Kurtis', 'Ethnic Wear', 'Winter', 'Bottomwear', 'Accessories', 'Footwear'];
  const EXCLUDED_CATEGORIES = new Set(['Grocery', 'Pet Supplies', 'Lingerie', 'Innerwear']);

  // Dynamic Smart Shuffle / Freshness Rotation
  const [sessionSeed] = useState(() => Math.floor(Math.random() * 1000));

  const shopProducts = useMemo(() => {
    const valid = products.filter((product) =>
      product.status !== 'pending_review' &&
      product.status !== 'draft' &&
      Boolean(product.image) &&
      Boolean(getProductClickUrl(product)) &&
      !EXCLUDED_CATEGORIES.has(product.category)
    );
    return [...valid].sort((a, b) => {
      const scoreA = (Number(a.rating || 4.2) * 10) + (a.sourceBatch ? 20 : 0);
      const scoreB = (Number(b.rating || 4.2) * 10) + (b.sourceBatch ? 20 : 0);
      if (Math.abs(scoreA - scoreB) > 5) {
        return scoreB - scoreA;
      }
      const hashA = (a.id.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0) + sessionSeed) % 100;
      const hashB = (b.id.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0) + sessionSeed) % 100;
      return hashA - hashB;
    });
  }, [products, sessionSeed]);

  const availableStores = [...new Set(shopProducts.map((product) => product.store))];
  
  const availableCategories = useMemo(() => {
    if (genderMode === 'men') {
      return ['Viral Jerseys', 'Oversized Tees', 'Linen Shirts', 'Streetwear & Cargo', 'Jackets & Hoodies'];
    }
    return [...new Set(shopProducts.map((product) => product.category).filter((c) => Boolean(c) && !EXCLUDED_CATEGORIES.has(c)))]
      .sort((a, b) => {
        const first = categoryPriority.indexOf(a);
        const second = categoryPriority.indexOf(b);
        if (first < 0 && second < 0) return a.localeCompare(b);
        if (first < 0) return 1;
        if (second < 0) return -1;
        return first - second;
      });
  }, [genderMode, shopProducts]);

  const categoryCounts = useMemo(() => {
    const counts = { 'All picks': shopProducts.length };
    shopProducts.forEach((p) => {
      if (p.category) counts[p.category] = (counts[p.category] || 0) + 1;
    });
    return counts;
  }, [shopProducts]);

  const pinterestCount = useMemo(() => {
    return shopProducts.filter((p) => Boolean(
      p.isPinterestCombo || p.isTrending || (p.collectionId || '').includes('pinterest') ||
      (p.title || '').toLowerCase().includes('jersey') || (p.title || '').toLowerCase().includes('spider') ||
      (p.title || '').toLowerCase().includes('cargo') || (p.title || '').toLowerCase().includes('y2k') ||
      (p.category || '').toLowerCase().includes('accessories') || (p.category || '').toLowerCase().includes('baby tees')
    )).length;
  }, [shopProducts]);

  const trendSuggestions = useMemo(() => {
    if (genderMode === 'men') {
      return ['Downtown Girl', 'Leather Bomber', 'Brasilcore', 'Ferrari Racing', 'Spider-Man Tees', 'Viral Jerseys', 'Under ₹599'];
    }
    return ['Downtown Girl', 'Leather Bomber', 'Brasilcore', 'Ferrari Racing', 'Spider-Man Tees', 'Bodycon Maxi', 'Under ₹499'];
  }, [genderMode]);
  const imageKey = (image) => String(image || '').trim().split(/[?#]/)[0].toLowerCase();
  const usedCoverKeys = new Set();
  const publicCollections = collections.map((collection) => {
    const collectionProducts = shopProducts.filter((product) => product.collectionId === collection.id);
    if (!collectionProducts.length) return null;

    const eligibleImages = new Map(collectionProducts
      .filter((product) => Boolean(product.image))
      .map((product) => [imageKey(product.image), product.image]));
    const candidates = [
      ...(Array.isArray(collection.coverImages) ? collection.coverImages : []),
      ...collectionProducts.map((product) => product.image),
    ];
    const coverImages = [];
    const localCoverKeys = new Set();
    for (const candidate of candidates) {
      const key = imageKey(candidate);
      const eligibleImage = eligibleImages.get(key);
      if (!key || !eligibleImage || localCoverKeys.has(key) || usedCoverKeys.has(key)) continue;
      localCoverKeys.add(key);
      usedCoverKeys.add(key);
      coverImages.push(eligibleImage);
      if (coverImages.length === 3) break;
    }

    // Prefer the curated collection art above, but retain one real listing image if
    // every eligible image is already used by an earlier collection.
    if (!coverImages.length) {
      const fallbackImage = collectionProducts.find((product) => Boolean(product.image))?.image;
      if (fallbackImage) coverImages.push(fallbackImage);
    }

    return {
      ...collection,
      coverImages,
      publicCount: collectionProducts.length,
    };
  }).filter(Boolean);

  const availableHeroCategories = [...new Set(shopProducts.map((product) => product.category).filter(Boolean))];
  const requestedHeroCategories = ['Tops & Tunics', 'Kurtis', 'Women Dresses', 'Winter'];
  const orderedHeroCategories = [...new Set([
    ...requestedHeroCategories.filter((category) => availableHeroCategories.includes(category)),
    ...availableHeroCategories,
  ])].slice(0, 5);
  const usedHeroImages = new Set();
  const heroSlides = orderedHeroCategories.map((category, slideIndex) => {
    let categoryProducts = shopProducts.filter((product) => product.category === category);
    if (category === 'Women Dresses') {
      categoryProducts = [...categoryProducts].sort((a, b) => {
        const aBodycon = /bodycon/i.test(`${a.title} ${a.subtitle}`);
        const bBodycon = /bodycon/i.test(`${b.title} ${b.subtitle}`);
        return Number(bBodycon) - Number(aBodycon);
      });
    }

    const images = [];
    const slideKeys = new Set();
    for (const product of categoryProducts) {
      const image = product.galleryUseAsPrimary && product.galleryImages?.length
        ? product.galleryImages[0]
        : product.image;
      const key = imageKey(image);
      if (!key || slideKeys.has(key) || usedHeroImages.has(key)) continue;
      images.push({ image, product });
      slideKeys.add(key);
      if (images.length === 2) break;
    }
    // If a category has just one eligible listing, use a second genuine gallery view if supplied.
    if (images.length < 2) {
      for (const product of categoryProducts) {
        const gallery = Array.isArray(product.galleryImages) ? product.galleryImages : [];
        for (const image of gallery) {
          const key = imageKey(image);
          if (!key || slideKeys.has(key) || usedHeroImages.has(key)) continue;
          images.push({ image, product });
          slideKeys.add(key);
          if (images.length === 2) break;
        }
        if (images.length === 2) break;
      }
    }
    if (images.length === 2) images.forEach(({ image }) => usedHeroImages.add(imageKey(image)));
    let adminSlide = null;
    try {
      const rawBanners = localStorage.getItem('shelf_admin_banners');
      if (rawBanners) {
        const parsed = JSON.parse(rawBanners);
        adminSlide = parsed.find(
          (s) => s.active !== false && (s.category === category || s.title?.toLowerCase().includes(category.toLowerCase()))
        );
      }
    } catch {}

    const copy = adminSlide || HERO_SLIDE_COPY[category] || {
      label: `${category.toUpperCase()} EDIT`,
      title: `A little ${category.toLowerCase()} moment`,
      subtitle: 'A few handpicked finds for your next scroll.',
      sticker: category.toUpperCase(),
      action: `Explore ${category.toLowerCase()}`,
      theme: ['sage', 'peach', 'lilac', 'blue', 'butter'][slideIndex % 5],
    };
    return { id: category, category, images, ...copy };
  }).filter((slide) => slide.images.length === 2);

  const [sortBy, setSortBy] = useState('trending'); // 'trending', 'price_low', 'price_high', 'discount', 'rating'
  const [activeColorFilter, setActiveColorFilter] = useState('all');
  const [activeQuickFilter, setActiveQuickFilter] = useState('all'); // 'all', 'under_499', 'under_799', '70_off', 'festive', 'co_ord'
  
  // --- Style Mode & Festival Intelligence Engine ---
  const [styleMode, setStyleMode] = useState('all'); // 'all', 'streetwear', 'festivals', 'party', 'casual'
  const [selectedFestival, setSelectedFestival] = useState('diwali'); // 'diwali', 'navratri', 'janmashtami', 'onam', 'eid', 'durga_puja', 'holi', 'rakhi'

  const FESTIVAL_DETAILS = {
    diwali: {
      name: 'Diwali & Deepavali',
      icon: '🪔',
      tagline: 'Royal Banarasi Silk Sarees, Sequin Mirror Lehengas & Polki Kundan Chokers',
      query: 'diwali banarasi lehenga kundan',
      colors: ['Ruby Red', 'Gold Glam', 'Deep Wine Maroon']
    },
    navratri: {
      name: 'Navratri & Garba',
      icon: '💃',
      tagline: '9-Nights Kutchi Mirror Work Chaniya Cholis, LED Velvet Dandiya & Oxidised Jhumkas',
      query: 'garba navratri chaniya choli mirror dandiya',
      colors: ['Ruby Red', 'Butter Yellow', 'Sage Green']
    },
    janmashtami: {
      name: 'Janmashtami & Krishna Janam',
      icon: '🦚',
      tagline: 'Peacock Blue & Sunshine Yellow Radha-Gopi Flared Anarkalis & Jasmine Gajras',
      query: 'janmashtami radha gopi anarkali yellow',
      colors: ['Butter Yellow', 'Baby Blue', 'Sage Green']
    },
    onam: {
      name: 'Onam & Vishu (Kerala)',
      icon: '🌴',
      tagline: 'Authentic Kerala Kasavu Gold Zari Sarees, Pattu Pavadai & Temple Gold Jewelry',
      query: 'kasavu saree onam vishu pattu pavadai',
      colors: ['Pearl White', 'Gold Glam']
    },
    eid: {
      name: 'Eid & Festive Glam',
      icon: '🌙',
      tagline: 'Pastel Resham Hand-Embroidered Shararas, Designer Kaftans & Shimmer Hijabs',
      query: 'eid sharara anarkali kaftan hijab',
      colors: ['Dusty Rose Pink', 'Sage Green', 'Lavender Lilac']
    },
    durga_puja: {
      name: 'Durga Puja (Pujo Asthami)',
      icon: '🔱',
      tagline: 'Authentic Lal Paar Banarasi Sarees, Royal Nath with Chain & Heavy Polki Jewelry',
      query: 'durga puja pujo banarasi saree nath',
      colors: ['Ruby Red', 'Pearl White', 'Gold Glam']
    },
    holi: {
      name: 'Holi Festival of Colors',
      icon: '🎨',
      tagline: 'All-White Breathable Pure Cotton Kurti Dhoti Sets & Waterproof Fanny Packs',
      query: 'holi white kurti dhoti cotton',
      colors: ['Pearl White', 'Butter Yellow']
    },
    rakhi: {
      name: 'Raksha Bandhan',
      icon: '🎀',
      tagline: 'Breezy Pastel Organza Sarees, Lucknowi Chikankari Suits & Pearl Drops',
      query: 'rakhi pastel saree chikankari organza',
      colors: ['Dusty Rose Pink', 'Lavender Lilac', 'Pearl White']
    }
  };

  // --- Phonetic & Slang Synonym Dictionary ---
  const SYNONYM_MAP = {
    'chanya': 'chaniya choli lehenga',
    'choli': 'lehenga choli chaniya',
    'garba': 'chaniya choli dandiya navratri',
    'jumka': 'jhumka earring jewelry',
    'jumkas': 'jhumka earring jewelry',
    'jean': 'baggy jeans cargo denim',
    'jeens': 'baggy jeans cargo denim',
    'kurta': 'kurti kurta anarkali ethnic',
    'suit': 'salwar kameez sharara anarkali',
    'tee': 'baby tee graphic t-shirt jersey',
    'tees': 'baby tee graphic t-shirt jersey',
    'tshirt': 'baby tee graphic t-shirt jersey',
    'shoes': 'sneakers juttis footwear boots flats',
    'bag': 'handbag baguette tote crossbody clutch potli',
    'shades': 'sunglasses glasses eyewear'
  };

  const visibleProducts = useMemo(() => {
    let list = shopProducts.filter((product) => { 
      if (savedOnly && !savedIds.includes(product.id)) return false;
      const matchesStore = storeFilter === 'All stores' || product.store === storeFilter;
      const matchesCategory = categoryFilter === 'All picks' || 
        (categoryFilter === '📌 Pinterest Drops'
          ? Boolean(product.isPinterestCombo || product.isTrending || (product.collectionId || '').includes('pinterest') || (product.title || '').toLowerCase().includes('jersey') || (product.title || '').toLowerCase().includes('spider') || (product.title || '').toLowerCase().includes('cargo') || (product.title || '').toLowerCase().includes('y2k') || (product.category || '').toLowerCase().includes('accessories') || (product.category || '').toLowerCase().includes('baby tees'))
          : product.category === categoryFilter);
      const matchesCollection = collectionFilter === 'all' || product.collectionId === collectionFilter;
      
      const pPrice = Number(product.price) || 0;
      const pOldPrice = Number(product.oldPrice) || pPrice;
      const discountPercent = pOldPrice > pPrice ? Math.round(((pOldPrice - pPrice) / pOldPrice) * 100) : 0;
      const pTitle = (product.title || '').toLowerCase();
      const pSub = (product.subtitle || '').toLowerCase();
      const pCat = (product.category || '').toLowerCase();
      const pColl = (product.collectionId || '').toLowerCase();
      const pColor = (product.primaryColor || '').toLowerCase();
      const pColors = Array.isArray(product.colors) ? product.colors.join(' ').toLowerCase() : '';

      // --- 0. STYLE MODE RESTRICTION ---
      if (styleMode === 'streetwear') {
        const isStreet = Boolean(
          pTitle.includes('cargo') || pTitle.includes('baggy') || pTitle.includes('jersey') ||
          pTitle.includes('hoodie') || pTitle.includes('bomber') || pTitle.includes('sneaker') ||
          pTitle.includes('baby tee') || pTitle.includes('jorts') || pTitle.includes('denim') ||
          pTitle.includes('streetwear') || pColl.includes('streetwear') || pColl.includes('blokecore') ||
          pCat.includes('bottomwear') || pCat.includes('baby tees')
        );
        if (!isStreet) return false;
      } else if (styleMode === 'festivals') {
        const fest = FESTIVAL_DETAILS[selectedFestival];
        const festTokens = fest ? fest.query.toLowerCase().split(/\s+/) : ['ethnic', 'saree', 'lehenga', 'kurti'];
        const matchesFest = festTokens.some((tok) => `${pTitle} ${pSub} ${pCat} ${pColl}`.includes(tok)) ||
                            pCat.includes('ethnic') || pCat.includes('festive') || pCat.includes('kurti');
        if (!matchesFest) return false;
      } else if (styleMode === 'party') {
        const isParty = Boolean(
          pTitle.includes('bodycon') || pTitle.includes('satin') || pTitle.includes('dress') ||
          pTitle.includes('corset') || pTitle.includes('cowl') || pTitle.includes('heel') ||
          pCat.includes('dresses') || pColl.includes('dresses')
        );
        if (!isParty) return false;
      } else if (styleMode === 'casual') {
        const isCasual = Boolean(
          pTitle.includes('tee') || pTitle.includes('shirt') || pTitle.includes('linen') ||
          pTitle.includes('trouser') || pTitle.includes('tote') || pTitle.includes('flat') ||
          pCat.includes('tops') || pCat.includes('bottomwear')
        );
        if (!isCasual) return false;
      }

      // 1. Quick Filter Pills Match
      if (activeQuickFilter === 'under_499' && pPrice > 499) return false;
      if (activeQuickFilter === 'under_799' && pPrice > 799) return false;
      if (activeQuickFilter === '70_off' && discountPercent < 60) return false;
      if (activeQuickFilter === 'festive' && !pCat.includes('ethnic') && !pCat.includes('festive') && !pColl.includes('navratri') && !pColl.includes('diwali') && !pColl.includes('kurti')) return false;
      if (activeQuickFilter === 'co_ord' && !pCat.includes('co-ord') && !pTitle.includes('set') && !pTitle.includes('co-ord')) return false;
      if (activeQuickFilter === 'viral' && !product.isPinterestCombo && !product.isTrending && !pColl.includes('pinterest') && !(product.image || '').includes('pinimg.com') && !pTitle.includes('pinterest') && !pColl.includes('brasilcore') && !pColl.includes('spider')) return false;

      // 2. Color Swatch Filter Match
      if (activeColorFilter !== 'all') {
        const targetColor = activeColorFilter.toLowerCase();
        if (!pColor.includes(targetColor) && !pColors.includes(targetColor) && !pTitle.includes(targetColor)) {
          return false;
        }
      }

      // 3. Multi-Dimensional Search & Synonyms
      const cleanQ = query.replace(/[^\w\s₹]/gi, '').trim().toLowerCase();
      if (!cleanQ) return matchesStore && matchesCategory && matchesCollection;

      // Expand synonyms
      let expandedQuery = cleanQ;
      for (const [k, v] of Object.entries(SYNONYM_MAP)) {
        if (cleanQ.includes(k)) {
          expandedQuery += ` ${v}`;
        }
      }

      // Direct Price Intent in Query
      if (cleanQ.includes('under 399') || cleanQ.includes('under ₹399')) {
        if (pPrice > 399) return false;
      } else if (cleanQ.includes('under 499') || cleanQ.includes('under ₹499') || cleanQ.includes('under 500')) {
        if (pPrice > 499) return false;
      } else if (cleanQ.includes('under 599') || cleanQ.includes('under ₹599') || cleanQ.includes('under 600')) {
        if (pPrice > 599) return false;
      } else if (cleanQ.includes('under 799') || cleanQ.includes('under ₹799') || cleanQ.includes('under 800')) {
        if (pPrice > 799) return false;
      } else if (cleanQ.includes('under 999') || cleanQ.includes('under ₹999') || cleanQ.includes('under 1000')) {
        if (pPrice > 999) return false;
      }

      const searchTokens = expandedQuery.split(/\s+/).filter((tok) => tok.length > 1 && !tok.startsWith('under') && tok !== 'rs' && tok !== 'inr');
      if (searchTokens.length === 0) {
        return matchesStore && matchesCategory && matchesCollection;
      }

      const searchableBlob = `${pTitle} ${pSub} ${pCat} ${pColl} ${pColor} ${pColors} ${product.store || ''}`.toLowerCase();
      const matchesAllTokens = searchTokens.some((token) => searchableBlob.includes(token));

      return matchesStore && matchesCategory && matchesCollection && matchesAllTokens;
    });

    // 4. Dynamic Smart Sorting
    return list.sort((a, b) => {
      const priceA = Number(a.price) || 0;
      const priceB = Number(b.price) || 0;
      const ratingA = Number(a.rating) || 4.5;
      const ratingB = Number(b.rating) || 4.5;
      const discA = a.oldPrice ? ((a.oldPrice - a.price) / a.oldPrice) : 0;
      const discB = b.oldPrice ? ((b.oldPrice - b.price) / b.oldPrice) : 0;

      if (sortBy === 'price_low') return priceA - priceB;
      if (sortBy === 'price_high') return priceB - priceA;
      if (sortBy === 'discount') return discB - discA;
      if (sortBy === 'rating') return ratingB - ratingA;
      if (sortBy === 'newest') return (b.isTrending ? 1 : 0) - (a.isTrending ? 1 : 0);

      // Default: Trending Pinterest Score
      return (Number(b.ratingCount || 1000) * ratingB) - (Number(a.ratingCount || 1000) * ratingA);
    });
  }, [shopProducts, storeFilter, categoryFilter, collectionFilter, query, savedOnly, savedIds, sortBy, activeColorFilter, activeQuickFilter]);
  const pageCount = Math.ceil(visibleProducts.length / pageSize);
  const pageProducts = visibleProducts.slice((page - 1) * pageSize, page * pageSize);
  const heroSlide = heroSlides[heroIndex] || heroSlides[0] || {
    id: 'shelf-edit',
    category: 'Handpicked',
    label: 'A LITTLE COLLECTION OF GOOD THINGS',
    title: 'Fresh finds for every day',
    subtitle: bio,
    sticker: 'GOOD THINGS',
    action: 'Explore the shelf',
    theme: 'sage',
    images: shopProducts.slice(0, 2).map((product) => ({ image: product.image, product })),
  };

  useEffect(() => {
    if (heroSlides.length < 2 || heroPaused) return undefined;
    const timer = window.setInterval(() => {
      setHeroIndex((current) => (current + 1) % heroSlides.length);
    }, 3000);
    return () => window.clearInterval(timer);
  }, [heroIndex, heroPaused, heroSlides.length]);

  useEffect(() => setPage(1), [storeFilter, categoryFilter, collectionFilter, query]);

  const changeHeroSlide = (direction) => {
    if (heroSlides.length < 2) return;
    setHeroIndex((current) => (current + direction + heroSlides.length) % heroSlides.length);
  };

  const selectHeroCategory = () => {
    setStoreFilter('All stores');
    setCategoryFilter(availableHeroCategories.includes(heroSlide.category) ? heroSlide.category : 'All picks');
    setCollectionFilter('all');
    document.getElementById('public-picks')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const selectCollection = (id) => {
    setCollectionFilter(id);
    setCategoryFilter('All picks');
    document.getElementById('public-picks')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  if (activeProductId) {
    return (
      <ProductPage 
        productId={activeProductId}
        allProducts={shopProducts}
        onBack={() => {
          setActiveProductId(null);
          try {
            const url = new URL(window.location.href);
            url.searchParams.delete('product');
            url.searchParams.delete('view');
            const cleanUrl = url.pathname + (url.search ? url.search : '');
            if (window.history.state && window.history.state.product) {
              window.history.back();
            } else {
              window.history.replaceState(null, '', cleanUrl);
            }
          } catch {
            setActiveProductId(null);
          }
        }}
        onSelectProduct={(id) => {
          setActiveProductId(id);
          try {
            const url = new URL(window.location.href);
            url.searchParams.set('product', id);
            window.history.pushState({ product: id }, '', url.pathname + url.search);
          } catch {}
        }}
        savedIds={savedIds}
        onToggleSaved={toggleSave}
      />
    );
  }

  return (
    <div className="storefront-page">
      <header className="storefront-topbar">
        <div className="storefront-nav-left">
          <button className="storefront-brand" onClick={() => { setCollectionFilter('all'); setCategoryFilter('All picks'); setStyleMode('all'); }} type="button" aria-label="Back to all picks">
            <span className="brand-mark"><i /><i /><i /></span>
            <span>shelf<span className="brand-period">.</span></span>
          </button>
        </div>

        {/* Desktop Navigation Group */}
        <div className="storefront-top-right-group desktop-only-nav">
          <div className="gender-switcher" role="tablist" aria-label="Select collection department">
            <button 
              type="button" 
              className={`gender-tab${genderMode === 'women' ? ' is-active' : ''}`}
              onClick={() => switchGender('women')}
              aria-selected={genderMode === 'women'}
              role="tab"
            >
              Women
            </button>
            <span className="gender-divider" aria-hidden="true">/</span>
            <button 
              type="button" 
              className={`gender-tab${genderMode === 'men' ? ' is-active' : ''}`}
              onClick={() => switchGender('men')}
              aria-selected={genderMode === 'men'}
              role="tab"
            >
              Men
            </button>
          </div>

          <button 
            className="ai-concierge-pill tryon-trigger-pill"
            type="button"
            onClick={() => { setTryOnInitialProduct(null); setTryOnModalOpen(true); }}
            title="Open Atelier AI Virtual Try-On Studio"
          >
            <span style={{ fontSize: '13px' }}>🪞</span>
            <span>AI Try-On</span>
          </button>

          <button 
            className="ai-concierge-pill showroom-trigger-pill"
            type="button"
            onClick={() => setShowroomModalOpen(true)}
            title="Open Interactive 3D Style Studio"
          >
            <span style={{ fontSize: '13px' }}>✨</span>
            <span>3D Showroom</span>
          </button>

          <button 
            className="ai-concierge-pill"
            type="button"
            onClick={() => setStylistModalOpen(true)}
            title="Ask AI Stylist for aesthetic recommendations"
          >
            <Icon name="sparkles" size={13} />
            <span>AI Stylist</span>
          </button>

          <button 
            className="pinterest-drops-top-pill"
            type="button"
            onClick={() => setGenzModalOpen(true)}
            title="Browse Viral Pinterest & Gen-Z Aesthetic Drops"
          >
            <span>📌 Pinterest Drops</span>
          </button>

          <button 
            className={`wishlist-top-pill${savedOnly ? ' is-active' : ''}`}
            type="button"
            onClick={() => {
              setSavedOnly(!savedOnly);
              if (!savedOnly) {
                setCategoryFilter('All picks');
                setCollectionFilter('all');
              }
            }}
            aria-label={`View saved wishlist (${savedIds.length} items)`}
          >
            <Icon name="heart" size={14} strokeWidth={savedOnly || savedIds.length > 0 ? 2.2 : 1.8} />
            <span>Saved</span>
            {savedIds.length > 0 && <span className="wishlist-count-badge">{savedIds.length}</span>}
          </button>

          <button 
            className="theme-toggle-btn"
            type="button"
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
            title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          >
            {theme === 'dark' ? (
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="5"/>
                <line x1="12" y1="1" x2="12" y2="3"/>
                <line x1="12" y1="21" x2="12" y2="23"/>
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                <line x1="1" y1="12" x2="3" y2="12"/>
                <line x1="21" y1="12" x2="23" y2="12"/>
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
              </svg>
            ) : (
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
              </svg>
            )}
          </button>

          {onShare && (
            <button 
              className="icon-button storefront-share-btn" 
              type="button" 
              onClick={onShare} 
              aria-label="Copy storefront page link"
              title="Copy storefront link"
            >
              <Icon name="copy" size={15} />
            </button>
          )}

          {showStudioControls && onBack && (
            <button className="button button-dark button-sm" type="button" onClick={onBack}>
              Back to studio <Icon name="arrowUpRight" size={14} />
            </button>
          )}
        </div>

        {/* Mobile Action Controls (<768px) */}
        <div className="storefront-mobile-actions">
          <button 
            className="theme-toggle-btn mobile-theme-btn"
            type="button"
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
            title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          >
            {theme === 'dark' ? (
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="5"/>
                <line x1="12" y1="1" x2="12" y2="3"/>
                <line x1="12" y1="21" x2="12" y2="23"/>
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                <line x1="1" y1="12" x2="3" y2="12"/>
                <line x1="21" y1="12" x2="23" y2="12"/>
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
              </svg>
            ) : (
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
              </svg>
            )}
          </button>

          <button 
            className={`wishlist-top-pill${savedOnly ? ' is-active' : ''}`}
            type="button"
            onClick={() => {
              setSavedOnly(!savedOnly);
              if (!savedOnly) {
                setCategoryFilter('All picks');
                setCollectionFilter('all');
              }
            }}
            aria-label={`View saved wishlist (${savedIds.length} items)`}
          >
            <Icon name="heart" size={14} strokeWidth={savedOnly || savedIds.length > 0 ? 2.2 : 1.8} />
            {savedIds.length > 0 && <span className="wishlist-count-badge">{savedIds.length}</span>}
          </button>

          {onShare && (
            <button 
              className="icon-button storefront-share-btn" 
              type="button" 
              onClick={onShare} 
              aria-label="Copy storefront link"
              title="Copy storefront link"
            >
              <Icon name="copy" size={15} />
            </button>
          )}

          <button 
            ref={menuButtonRef}
            className="storefront-mobile-menu-btn" 
            type="button" 
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label={mobileMenuOpen ? 'Close navigation menu' : 'Open navigation menu'}
            aria-expanded={mobileMenuOpen}
            aria-controls="storefront-mobile-dropdown"
          >
            <Icon name={mobileMenuOpen ? 'close' : 'menu'} size={18} />
          </button>
        </div>

        {/* Accessible Mobile Dropdown Menu */}
        {mobileMenuOpen && (
          <nav 
            id="storefront-mobile-dropdown" 
            className="storefront-mobile-dropdown" 
            aria-label="Mobile navigation menu"
          >
            <div className="mobile-dropdown-header">
              <span className="creator-avatar">{creatorName.trim().charAt(0) || 'A'}</span>
              <div>
                <strong>{creatorName}</strong>
                <small>{handle}</small>
              </div>
            </div>

            <div className="mobile-dropdown-gender">
              <div className="gender-switcher" role="tablist" aria-label="Select collection department">
                <button 
                  type="button" 
                  className={`gender-tab${genderMode === 'women' ? ' is-active' : ''}`}
                  onClick={() => { switchGender('women'); setMobileMenuOpen(false); }}
                  aria-selected={genderMode === 'women'}
                >
                  Women
                </button>
                <span className="gender-divider">/</span>
                <button 
                  type="button" 
                  className={`gender-tab${genderMode === 'men' ? ' is-active' : ''}`}
                  onClick={() => { switchGender('men'); setMobileMenuOpen(false); }}
                  aria-selected={genderMode === 'men'}
                >
                  Men
                </button>
              </div>
            </div>

            <div className="mobile-dropdown-items">
              <button 
                type="button" 
                className="mobile-nav-link"
                onClick={() => { setTryOnInitialProduct(null); setTryOnModalOpen(true); setMobileMenuOpen(false); }}
              >
                <span style={{ fontSize: '15px' }}>🪞</span>
                <span>AI Virtual Try-On</span>
              </button>

              <button 
                type="button" 
                className="mobile-nav-link"
                onClick={() => { setShowroomModalOpen(true); setMobileMenuOpen(false); }}
              >
                <Icon name="sparkles" size={16} />
                <span>3D Style Showroom</span>
              </button>

              <button 
                type="button" 
                className="mobile-nav-link"
                onClick={() => { setStylistModalOpen(true); setMobileMenuOpen(false); }}
              >
                <Icon name="sparkles" size={16} />
                <span>AI Stylist</span>
              </button>

              <button 
                type="button" 
                className="mobile-nav-link"
                onClick={() => { setOutfitModalOpen(true); setMobileMenuOpen(false); }}
              >
                <Icon name="collections" size={16} />
                <span>Build Outfit Look</span>
              </button>

              <button 
                type="button" 
                className="mobile-nav-link"
                onClick={() => { setGenzModalOpen(true); setMobileMenuOpen(false); }}
              >
                <span>📌</span>
                <span>Pinterest Drops</span>
              </button>

              {isAdmin && (
                <button 
                  type="button" 
                  className="mobile-nav-link"
                  onClick={() => { setEarningModalOpen(true); setMobileMenuOpen(false); }}
                >
                  <Icon name="analytics" size={16} />
                  <span>Earnings Scope</span>
                </button>
              )}

              {showStudioControls && onBack && (
                <button 
                  type="button" 
                  className="mobile-nav-link is-studio-back"
                  onClick={() => { onBack(); setMobileMenuOpen(false); }}
                >
                  <Icon name="arrowUpRight" size={16} />
                  <span>Back to studio</span>
                </button>
              )}
            </div>
          </nav>
        )}
      </header>

      <main className={`storefront-main ${isTransitioning ? 'is-curtain-transition' : ''}`}>
        <section
          className={`storefront-hero hero-theme-${heroSlide.theme}`}
          onMouseEnter={() => setHeroPaused(true)}
          onMouseLeave={() => setHeroPaused(false)}
          onFocusCapture={() => setHeroPaused(true)}
          onBlurCapture={(event) => { if (!event.currentTarget.contains(event.relatedTarget)) setHeroPaused(false); }}
        >
          {festiveConfig.videoUrl && (
            <div className="hero-video-backdrop">
              <video autoPlay loop muted playsInline src={festiveConfig.videoUrl} />
              <span className="hero-video-overlay" />
            </div>
          )}
          <div className="storefront-hero-copy">
            <span className="public-kicker"><span className="kicker-dot" /> {festiveConfig.eyebrow || 'A LITTLE COLLECTION OF GOOD THINGS'}</span>
            <h1>My taste,<br /><em>your next find.</em></h1>
            <div className="hero-slide-caption" key={heroSlide.id}>
              <span className="hero-slide-category">{heroSlide.label} · {String(heroIndex + 1).padStart(2, '0')}</span>
              <strong>{heroSlide.title}</strong>
              <small>{heroSlide.subtitle}</small>
            </div>
            <p className="hero-bio">{bio}</p>
            <div className="storefront-hero-actions">
              <button className="button button-primary" type="button" onClick={selectHeroCategory}>{heroSlide.action} <Icon name="arrowDown" size={16} /></button>
              <span className="tiny-trust-note"><span className="trust-star">✦</span> handpicked by {creatorName.split(' ')[0]}</span>
            </div>
          </div>
          <div className="storefront-hero-art" aria-label={`Featured ${heroSlide.category} products`}>
            {/* Full-bleed editorial background — decorative, crossfades on slide change */}
            {heroSlide.images[0] && (
              <div className="hero-bg-layer" key={`bg-${heroSlide.id}`} aria-hidden="true">
                <img src={heroSlide.images[0].image} alt="" loading="eager" referrerPolicy="no-referrer" />
              </div>
            )}
            <div className="hero-copy-scrim" aria-hidden="true" />
            <div className="hero-sunburst" />
            <div className="hero-art-stage" key={heroSlide.id}>
              {heroSlide.images.slice(0, 2).map(({ image, product }, index) => (
                <a
                  className={`hero-art-image ${index === 0 ? 'art-img-one' : 'art-img-two'}`}
                  href={getProductClickUrl(product)}
                  target="_blank"
                  rel="noreferrer"
                  aria-label={`Shop ${product.title} on ${product.store}`}
                  key={`${product.id}-${index}`}
                >
                  <img src={image} alt={product.title} loading="eager" referrerPolicy="no-referrer" />
                  <span className="hero-art-product-label">{product.category} <b>Shop ↗</b></span>
                </a>
              ))}
            </div>
            <div className="hero-art-note"><span>{heroSlide.label}</span><b>{heroSlide.sticker} ↗</b></div>
            <span className="hero-art-sparkle sparkle-one" aria-hidden="true">✳</span><span className="hero-art-sparkle sparkle-two" aria-hidden="true">✦</span>
          </div>
          <div className="hero-bottomline">
            <span>SCROLL A LITTLE</span>
            <span className="hero-line" />
            {heroSlides.length > 1 && <div className="hero-slider-controls" aria-label="Featured category slides">
              <button className="hero-slider-arrow" type="button" aria-label="Previous category" onClick={() => changeHeroSlide(-1)}><Icon name="chevronLeft" size={13} /></button>
              <div className="hero-slide-dots">
                {heroSlides.map((slide, index) => <button
                  className={`hero-slide-dot${heroIndex === index ? ' is-active' : ''}`}
                  key={slide.id}
                  type="button"
                  aria-label={`Show ${slide.label} slide`}
                  aria-current={heroIndex === index ? 'true' : undefined}
                  onClick={() => setHeroIndex(index)}
                />)}
              </div>
              <button className="hero-slider-arrow" type="button" aria-label="Next category" onClick={() => changeHeroSlide(1)}><Icon name="chevronRight" size={13} /></button>
            </div>}
            <span className="hero-slide-counter">{String(heroIndex + 1).padStart(2, '0')} / {String(heroSlides.length || 1).padStart(2, '0')}</span>
          </div>
        </section>

        {/* Live Floating Seasonal & Festive Trend Ticker (Google Trend Engine) */}
        {festiveConfig.enabled !== false && festiveConfig.ticker && (
          <div className="storefront-festive-ticker-wrap">
            <button 
              className="floating-festive-ticker" 
              type="button"
              onClick={() => {
                if (festiveConfig.query) {
                  setQuery(festiveConfig.query);
                  setCategoryFilter('All picks');
                  setCollectionFilter('all');
                }
                document.getElementById('public-picks')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
              }}
            >
              <span className="ticker-sparkle">{festiveConfig.icon || '✦'}</span>
              <span className="ticker-title">{festiveConfig.ticker}</span>
              <span className="ticker-action">Explore Drops →</span>
            </button>
          </div>
        )}

        {publicCollections.length > 0 && <section className="public-collections-section">
          <div className="section-heading-row">
            <div><p className="eyebrow">THE GOOD STUFF, SORTED</p><h2>Browse my little edits</h2></div>
            <button className={`text-button${collectionFilter === 'all' ? ' is-active' : ''}`} type="button" onClick={() => { setCollectionFilter('all'); setCategoryFilter('All picks'); }}>See everything <Icon name="arrowRight" size={16} /></button>
          </div>
          <div className="public-collection-grid public-collection-carousel">
            {publicCollections.map((collection) => (
              <CollectionCard
                key={collection.id}
                collection={collection}
                count={collection.publicCount}
                onClick={() => selectCollection(collection.id)}
                small
              />
            ))}
          </div>
        </section>}

        <section className="public-picks-section" id="public-picks">
          <div className="section-heading-row public-picks-title-row">
            <div>
              <p className="eyebrow">{creatorName.split(' ')[0].toUpperCase()}'S CURRENT FAVOURITES</p>
              <h2>{collectionFilter === 'all' ? 'The whole shelf' : collections.find((collection) => collection.id === collectionFilter)?.title || 'The whole shelf'}</h2>
            </div>
            <div className="public-search-wrap">
              <Icon name="search" size={17} />
              <input 
                type="search" 
                placeholder="Search 'Bodycon', 'Y2K Tops', 'Kurtis'..." 
                value={query} 
                onChange={(event) => setQuery(event.target.value)} 
              />
              {query && (
                <button type="button" className="search-clear-btn" onClick={() => setQuery('')} aria-label="Clear search">
                  ✕
                </button>
              )}
            </div>
          </div>

          {/* Unified Clean Category Filter Strip */}
          <div className="filter-row public-category-filter-row" aria-label="Filter by category">
            <button 
              className={`filter-chip category-pill${categoryFilter === 'All picks' ? ' is-active' : ''}`} 
              type="button" 
              onClick={() => { setCategoryFilter('All picks'); setQuery(''); }}
            >
              <span>All picks</span>
              <span className="pill-count">{shopProducts.length}</span>
            </button>

            <button 
              className={`filter-chip category-pill pinterest-filter-pill${categoryFilter === '📌 Pinterest Drops' ? ' is-active' : ''}`} 
              type="button" 
              onClick={() => { setCategoryFilter('📌 Pinterest Drops'); setQuery(''); }}
            >
              <span>📌 Pinterest Drops</span>
              <span className="pill-count">{pinterestCount}</span>
            </button>

            {availableCategories.map((category) => (
              <button 
                key={category} 
                className={`filter-chip category-pill${categoryFilter === category ? ' is-active' : ''}`} 
                type="button" 
                onClick={() => {
                  setCategoryFilter(category);
                  setQuery('');
                }}
              >
                <span>{category}</span>
                {categoryCounts[category] !== undefined && <span className="pill-count">{categoryCounts[category]}</span>}
              </button>
            ))}
          </div>

          {categoryFilter === '📌 Pinterest Drops' && (
            <div className="pinterest-vault-banner">
              <div className="vault-banner-left">
                <span className="vault-kicker">📌 PINTEREST 2026 DROPS · VIRAL AESTHETIC VAULT</span>
                <h3>Viral Streetwear, Blokecore & Statement Accessories</h3>
                <p>Curated exclusively from global Pinterest aesthetic boards. Blokecore jerseys, spider tees, baggy jorts & vintage jewelry.</p>
              </div>
              <button 
                type="button" 
                className="button button-dark vault-open-btn"
                onClick={() => setGenzModalOpen(true)}
              >
                <span>Open Interactive Vault ✨</span>
              </button>
            </div>
          )}

          {/* Clean Quick Filters & Color Swatches */}
          <div className="discovery-control-strip">
            <div className="quick-filter-chips">
              <button 
                type="button" 
                className={`quick-pill${activeQuickFilter === 'all' ? ' is-active' : ''}`}
                onClick={() => setActiveQuickFilter('all')}
              >
                All
              </button>
              <button 
                type="button" 
                className={`quick-pill${activeQuickFilter === 'under_499' ? ' is-active' : ''}`}
                onClick={() => setActiveQuickFilter(activeQuickFilter === 'under_499' ? 'all' : 'under_499')}
              >
                Under ₹499
              </button>
              <button 
                type="button" 
                className={`quick-pill${activeQuickFilter === '70_off' ? ' is-active' : ''}`}
                onClick={() => setActiveQuickFilter(activeQuickFilter === '70_off' ? 'all' : '70_off')}
              >
                60%+ Off
              </button>
              <button 
                type="button" 
                className={`quick-pill${activeQuickFilter === 'festive' ? ' is-active' : ''}`}
                onClick={() => setActiveQuickFilter(activeQuickFilter === 'festive' ? 'all' : 'festive')}
              >
                Festive & Ethnic
              </button>
              <button 
                type="button" 
                className={`quick-pill${activeQuickFilter === 'co_ord' ? ' is-active' : ''}`}
                onClick={() => setActiveQuickFilter(activeQuickFilter === 'co_ord' ? 'all' : 'co_ord')}
              >
                Co-ord Sets
              </button>
              <button 
                type="button" 
                className={`quick-pill${activeQuickFilter === 'viral' ? ' is-active' : ''}`}
                onClick={() => setActiveQuickFilter(activeQuickFilter === 'viral' ? 'all' : 'viral')}
              >
                📌 Pinterest Viral
              </button>
            </div>

            <div className="discovery-right-controls">
              {/* Color Swatches */}
              <div className="color-swatch-row" title="Filter by colorway palette">
                {[
                  { name: 'all', label: 'All', hex: 'conic-gradient(red, yellow, lime, aqua, blue, magenta, red)' },
                  { name: 'black', label: 'Black', hex: '#18181b' },
                  { name: 'white', label: 'White', hex: '#f8fafc' },
                  { name: 'pink', label: 'Pink', hex: '#fda4af' },
                  { name: 'green', label: 'Green', hex: '#86efac' },
                  { name: 'brown', label: 'Brown', hex: '#a8715a' },
                  { name: 'red', label: 'Red', hex: '#e11d48' },
                  { name: 'yellow', label: 'Yellow', hex: '#fef08a' }
                ].map((col) => (
                  <button
                    key={col.name}
                    type="button"
                    className={`color-dot-btn${activeColorFilter === col.name ? ' is-active' : ''}`}
                    style={{ background: col.hex }}
                    onClick={() => setActiveColorFilter(activeColorFilter === col.name ? 'all' : col.name)}
                    aria-label={`Filter by ${col.label}`}
                    title={col.label}
                  />
                ))}
              </div>

              {/* Sort Selector */}
              <div className="sort-selector-wrap">
                <select 
                  value={sortBy} 
                  onChange={(e) => setSortBy(e.target.value)} 
                  className="smart-sort-select"
                  aria-label="Sort products"
                >
                  <option value="trending">🔥 Viral Trending</option>
                  <option value="price_low">💸 Price: Low to High</option>
                  <option value="price_high">💎 Price: High to Low</option>
                  <option value="discount">🎁 Max % Discount</option>
                  <option value="rating">⭐ Top Rated (4.8+)</option>
                  <option value="newest">⚡ New Drops First</option>
                </select>
              </div>
            </div>
          </div>

          {/* Active Search / Filter Stats Bar */}
          <div className="search-stats-bar">
            <span>Showing <strong>{visibleProducts.length}</strong> handpicked pieces</span>
            {(query || activeColorFilter !== 'all' || activeQuickFilter !== 'all' || categoryFilter !== 'All picks' || collectionFilter !== 'all') && (
              <button 
                type="button" 
                className="clear-all-filters-btn"
                onClick={() => {
                  setQuery('');
                  setCategoryFilter('All picks');
                  setCollectionFilter('all');
                  setActiveColorFilter('all');
                  setActiveQuickFilter('all');
                }}
              >
                Reset Filters ✕
              </button>
            )}
          </div>

          {visibleProducts.length ? (
            <div className="product-grid public-product-grid">
              {pageProducts.map((product) => (
                <ProductCard 
                  key={product.id} 
                  product={{ ...product, saved: savedIds.includes(product.id) }} 
                  isPublic 
                  isAdmin={isAdmin}
                  showStudioControls={showStudioControls}
                  onDeleteProduct={onDeleteProduct}
                  onTogglePublish={onTogglePublish}
                  onEditProduct={onEditProduct}
                  onToggleSaved={toggleSave}
                  onInstantOrder={(prod) => setOrderModalProduct(prod)}
                  onViewDetail={(prod) => {
                    setActiveProductId(prod.id);
                    try {
                      const url = new URL(window.location.href);
                      url.searchParams.set('product', prod.id);
                      window.history.pushState({ product: prod.id }, '', url.pathname + url.search);
                    } catch {}
                  }}
                />
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <span className="empty-state-icon"><Icon name="search" size={23} /></span>
              <h3>No picks matching &quot;{query}&quot;</h3>
              <p>Try another search keyword or browse all categories.</p>
              <button 
                type="button" 
                className="button button-dark" 
                style={{ marginTop: '16px', height: '38px', padding: '0 18px', fontSize: '12px' }}
                onClick={() => {
                  setQuery('');
                  setCategoryFilter('All picks');
                  setCollectionFilter('all');
                  setStyleMode('all');
                }}
              >
                Clear Search &amp; Show All Picks ↗
              </button>
            </div>
          )}
          <Pagination page={page} pageCount={pageCount} totalItems={visibleProducts.length} pageSize={pageSize} onPageChange={setPage} />
        </section>
        <footer className="storefront-footer">
          <div className="footer-brand"><span className="brand-mark"><i /><i /><i /></span><span>shelf<span className="brand-period">.</span></span></div>
          <p>Curated fashion & aesthetic edits. Made with taste & care.</p>
          <span className="public-preview-note">✦ Handpicked pieces & style edits</span>
        </footer>
      </main>

      {/* ==========================================================================
          PURPLE PLACE STYLE FLOATING LIQUID GLASS DOCK & CATEGORY POPUP
          ========================================================================== */}
      <div className="purple-dock-container" role="navigation" aria-label="Quick store navigation">
        {/* Category Popup Menu (Reveals above SHOP button) */}
        {shopMenuOpen && (
          <div className="purple-category-popup" role="menu" aria-label="Browse Collections">
            <button
              type="button"
              role="menuitem"
              className={`purple-menu-item${categoryFilter === 'All picks' ? ' is-active' : ''}`}
              onClick={() => {
                setCategoryFilter('All picks');
                setShopMenuOpen(false);
                document.getElementById('public-picks')?.scrollIntoView({ behavior: 'smooth' });
              }}
            >
              <span>SHOP ALL</span>
              <span className="purple-chevron">›</span>
            </button>
            <button
              type="button"
              role="menuitem"
              className={`purple-menu-item${categoryFilter === 'Tops & Tunics' ? ' is-active' : ''}`}
              onClick={() => {
                setCategoryFilter('Tops & Tunics');
                setShopMenuOpen(false);
                document.getElementById('public-picks')?.scrollIntoView({ behavior: 'smooth' });
              }}
            >
              <span>TOPS & BABY TEES</span>
              <span className="purple-chevron">›</span>
            </button>
            <button
              type="button"
              role="menuitem"
              className={`purple-menu-item${categoryFilter === 'Kurtis' || categoryFilter === 'Ethnic Wear' ? ' is-active' : ''}`}
              onClick={() => {
                setCategoryFilter('Kurtis');
                setShopMenuOpen(false);
                document.getElementById('public-picks')?.scrollIntoView({ behavior: 'smooth' });
              }}
            >
              <span>KURTIS & ETHNIC</span>
              <span className="purple-chevron">›</span>
            </button>
            <button
              type="button"
              role="menuitem"
              className={`purple-menu-item${categoryFilter === 'Women Dresses' ? ' is-active' : ''}`}
              onClick={() => {
                setCategoryFilter('Women Dresses');
                setShopMenuOpen(false);
                document.getElementById('public-picks')?.scrollIntoView({ behavior: 'smooth' });
              }}
            >
              <span>WOMEN DRESSES</span>
              <span className="purple-chevron">›</span>
            </button>
            <button
              type="button"
              role="menuitem"
              className={`purple-menu-item${categoryFilter === 'Winter' ? ' is-active' : ''}`}
              onClick={() => {
                setCategoryFilter('Winter');
                setShopMenuOpen(false);
                document.getElementById('public-picks')?.scrollIntoView({ behavior: 'smooth' });
              }}
            >
              <span>KNITWEARS & HOODIES</span>
              <span className="purple-chevron">›</span>
            </button>
            <button
              type="button"
              role="menuitem"
              className={`purple-menu-item${categoryFilter === 'Bottomwear' ? ' is-active' : ''}`}
              onClick={() => {
                setCategoryFilter('Bottomwear');
                setShopMenuOpen(false);
                document.getElementById('public-picks')?.scrollIntoView({ behavior: 'smooth' });
              }}
            >
              <span>PANTS & BOTTOMS</span>
              <span className="purple-chevron">›</span>
            </button>
            <button
              type="button"
              role="menuitem"
              className={`purple-menu-item${categoryFilter.includes('Accessories') || categoryFilter.includes('Bag') ? ' is-active' : ''}`}
              onClick={() => {
                const bagCat = availableCategories.find((c) => c.includes('Accessories') || c.includes('Bag')) || 'Bags & Accessories';
                setCategoryFilter(bagCat);
                setShopMenuOpen(false);
                document.getElementById('public-picks')?.scrollIntoView({ behavior: 'smooth' });
              }}
            >
              <span>ACCESSORIES & BAGS</span>
              <span className="purple-chevron">›</span>
            </button>
          </div>
        )}

        {/* Liquid Frosted Glass Bottom Dock Bar */}
        <div className="purple-glass-dock">
          <button 
            type="button" 
            className="purple-dock-item"
            onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          >
            HOME
          </button>

          <button 
            type="button" 
            className={`purple-dock-center-pill${shopMenuOpen ? ' is-open' : ''}`}
            onClick={() => setShopMenuOpen(!shopMenuOpen)}
            aria-expanded={shopMenuOpen}
            aria-label="Open categories menu"
          >
            SHOP
          </button>

          <button 
            type="button" 
            className={`purple-dock-item${savedOnly ? ' is-active' : ''}`}
            onClick={() => {
              setSavedOnly(!savedOnly);
              if (!savedOnly) {
                setCategoryFilter('All picks');
                setCollectionFilter('all');
              }
              document.getElementById('public-picks')?.scrollIntoView({ behavior: 'smooth' });
            }}
          >
            CART {savedIds.length > 0 && `(${savedIds.length})`}
          </button>

          <button 
            type="button" 
            className={`purple-dock-item${activeQuickFilter === '70_off' ? ' is-active' : ''}`}
            onClick={() => {
              setQuery('');
              setActiveQuickFilter(activeQuickFilter === '70_off' ? 'all' : '70_off');
              setCategoryFilter('All picks');
              document.getElementById('public-picks')?.scrollIntoView({ behavior: 'smooth' });
            }}
          >
            SALES
          </button>

          <button 
            type="button" 
            className="purple-dock-item"
            onClick={() => setStylistModalOpen(true)}
          >
            MORE
          </button>
        </div>
      </div>

      {detailProduct && (
        <ProductDetailModal 
          product={detailProduct} 
          allProducts={shopProducts} 
          onClose={() => setDetailProduct(null)} 
          onInstantOrder={(p) => setOrderModalProduct(p)} 
          onTryOnProduct={(p) => {
            setTryOnInitialProduct(p);
            setTryOnModalOpen(true);
          }}
        />
      )}

      {stylistModalOpen && (
        <React.Suspense fallback={null}>
          <AIStylistModal 
            allProducts={shopProducts} 
            onClose={() => setStylistModalOpen(false)} 
            onViewProduct={(id) => {
              setActiveProductId(id);
              try {
                const url = new URL(window.location.href);
                url.searchParams.set('product', id);
                window.history.pushState({ product: id }, '', url.pathname + url.search);
              } catch {}
            }}
            onInstantOrder={(p) => setOrderModalProduct(p)} 
          />
        </React.Suspense>
      )}

      {tryOnModalOpen && (
        <React.Suspense fallback={null}>
          <VirtualTryOnModal 
            allProducts={shopProducts} 
            initialProduct={tryOnInitialProduct}
            onClose={() => { setTryOnModalOpen(false); setTryOnInitialProduct(null); }} 
          />
        </React.Suspense>
      )}

      {showroomModalOpen && (
        <React.Suspense fallback={null}>
          <InteractiveShowroomModal 
            products={shopProducts} 
            onClose={() => setShowroomModalOpen(false)} 
            onOpenProduct={(p) => {
              setActiveProductId(p.id);
              setShowroomModalOpen(false);
            }}
          />
        </React.Suspense>
      )}

      {outfitModalOpen && (
        <React.Suspense fallback={null}>
          <OutfitBuilderModal 
            allProducts={shopProducts} 
            onClose={() => setOutfitModalOpen(false)} 
          />
        </React.Suspense>
      )}

      {orderModalProduct && (
        <InstantOrderModal 
          product={orderModalProduct} 
          onClose={() => setOrderModalProduct(null)} 
        />
      )}

      {earningModalOpen && (
        <React.Suspense fallback={null}>
          <EarningScopeModal
            products={shopProducts}
            creatorName={creatorName}
            onClose={() => setEarningModalOpen(false)}
          />
        </React.Suspense>
      )}

      {genzModalOpen && (
        <React.Suspense fallback={null}>
          <GenZStudioModal
            isOpen={genzModalOpen}
            onClose={() => setGenzModalOpen(false)}
            products={shopProducts}
            savedIds={savedIds}
            onToggleSaved={toggleSave}
            onInstantOrder={(p) => setOrderModalProduct(p)}
            onViewDetail={(p) => {
              setActiveProductId(p.id);
              setGenzModalOpen(false);
              try {
                const url = new URL(window.location.href);
                url.searchParams.set('product', p.id);
                window.history.pushState({ product: p.id }, '', url.pathname + url.search);
              } catch {}
            }}
          />
        </React.Suspense>
      )}
    </div>
  );
}
