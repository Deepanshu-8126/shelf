import React, { useEffect, useMemo, useRef, useState } from 'react';
import Icon from './Icon.jsx';
import ProductCard from './ProductCard.jsx';
import Pagination from './Pagination.jsx';
import CollectionCard from './CollectionCard.jsx';
import InstantOrderModal from './InstantOrderModal.jsx';
import ProductDetailModal from './ProductDetailModal.jsx';
import ProductPage from './ProductPage.jsx';
import ShelfHeader from './ShelfHeader.jsx';
import ShelfProductStage from './ShelfProductStage.jsx';
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
  onEditProduct,
  onOpenWishlink
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
  const [selectedShowroomProduct, setSelectedShowroomProduct] = useState(null);
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
    if (!Array.isArray(products)) return [];
    const valid = products.filter((product) =>
      product &&
      product.status !== 'pending_review' &&
      product.status !== 'draft' &&
      Boolean(product.image || product.main_image) &&
      Boolean(getProductClickUrl(product)) &&
      !EXCLUDED_CATEGORIES.has(product.category)
    );
    return [...valid].sort((a, b) => {
      const scoreA = (Number(a?.rating || 0) * 10) + (a?.sourceBatch ? 20 : 0);
      const scoreB = (Number(b?.rating || 0) * 10) + (b?.sourceBatch ? 20 : 0);
      if (Math.abs(scoreA - scoreB) > 5) {
        return scoreB - scoreA;
      }
      const strA = String(a?.id || '');
      const strB = String(b?.id || '');
      const hashA = (strA.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0) + sessionSeed) % 100;
      const hashB = (strB.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0) + sessionSeed) % 100;
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
  const publicCollections = (Array.isArray(collections) ? collections : []).map((collection) => {
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

  const [featuredProduct, setFeaturedProduct] = useState(null);
  const [cartCount, setCartCount] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('shelf_cart_count') || '0');
    } catch {
      return 0;
    }
  });
  const [showSearch, setShowSearch] = useState(false);

  // Active featured product: matches URL activeProductId, selected featuredProduct, or first prominent piece
  const activeFeaturedProduct = useMemo(() => {
    if (featuredProduct) return featuredProduct;
    if (activeProductId) {
      const matched = shopProducts.find((p) => String(p.id) === String(activeProductId));
      if (matched) return matched;
    }
    const preferred = shopProducts.find((p) => {
      const cat = (p.category || '').toLowerCase();
      const title = (p.title || '').toLowerCase();
      return cat.includes('kurti') || cat.includes('dress') || title.includes('kurti') || title.includes('dress');
    });
    return preferred || shopProducts[0] || null;
  }, [featuredProduct, activeProductId, shopProducts]);

  return (
    <div className="shelf-clean-storefront">
      {/* 1. Minimal Editorial Header (shelf.) */}
      <ShelfHeader
        activeCategory={categoryFilter}
        onSelectCategory={(cat) => {
          setCategoryFilter(cat);
          setCollectionFilter('all');
          document.getElementById('public-picks')?.scrollIntoView({ behavior: 'smooth' });
        }}
        searchQuery={query}
        onSearchChange={setQuery}
        showSearch={showSearch}
        onToggleSearch={() => setShowSearch(!showSearch)}
        wishlistCount={savedIds.length}
        cartCount={cartCount}
        onOpenWishlist={() => {
          setSavedOnly(!savedOnly);
          document.getElementById('public-picks')?.scrollIntoView({ behavior: 'smooth' });
        }}
        onOpenCart={() => {
          if (activeFeaturedProduct) setOrderModalProduct(activeFeaturedProduct);
        }}
      />

      {/* 2. Luxury 2-Column Product Stage (60% Gallery / 40% Details) */}
      <ShelfProductStage
        product={activeFeaturedProduct}
        onAddToCart={() => {
          setCartCount((prev) => {
            const next = prev + 1;
            try { localStorage.setItem('shelf_cart_count', next); } catch {}
            return next;
          });
        }}
        onToggleWishlist={(id) => toggleSave(id)}
        isWishlisted={savedIds.includes(activeFeaturedProduct?.id)}
        onOpenInstantOrder={(prod) => setOrderModalProduct(prod)}
      />

      {/* 3. Clean Curated Collection Grid Below */}
      <section className="shelf-collection-section" id="public-picks">
        <div className="shelf-collection-heading">
          <h2>{categoryFilter === 'All picks' ? 'Curated Collection' : categoryFilter}</h2>
          <span className="shelf-collection-count">{visibleProducts.length} pieces</span>
        </div>

        <div className="shelf-cards-grid">
          {visibleProducts.map((prod) => {
            const hasRealPrice = prod.price != null && !isNaN(Number(prod.price));
            const hasRealOldPrice = prod.originalPrice != null && !isNaN(Number(prod.originalPrice)) && Number(prod.originalPrice) > Number(prod.price);

            return (
              <article
                key={prod.id}
                className={`shelf-item-card ${activeFeaturedProduct?.id === prod.id ? 'is-active-item' : ''}`}
                onClick={() => {
                  setFeaturedProduct(prod);
                  setActiveProductId(prod.id);
                  try {
                    const url = new URL(window.location.href);
                    url.searchParams.set('product', prod.id);
                    window.history.pushState({ product: prod.id }, '', url.pathname + url.search);
                  } catch {}
                  window.scrollTo({ top: 0, behavior: 'smooth' });
                }}
              >
                <div className="shelf-item-img-box">
                  <img src={prod.image || prod.main_image} alt={prod.title || 'Product'} loading="lazy" />
                </div>
                <div className="shelf-item-info">
                  <h3 className="shelf-item-title">{prod.title || 'Untitled Listing'}</h3>
                  <div className="shelf-item-price-row">
                    {hasRealPrice ? (
                      <span className="shelf-item-price">₹{Number(prod.price).toLocaleString('en-IN')}</span>
                    ) : (
                      <span className="shelf-item-price">View price</span>
                    )}
                    {hasRealOldPrice && (
                      <span className="shelf-item-mrp">₹{Math.round(Number(prod.originalPrice)).toLocaleString('en-IN')}</span>
                    )}
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      </section>

      {/* Product Detail Modal (Luxury Clean White) */}
      {detailProduct && (
        <ProductDetailModal
          product={detailProduct}
          onClose={() => setDetailProduct(null)}
          onInstantOrder={(p) => {
            setDetailProduct(null);
            setOrderModalProduct(p);
          }}
          onToggleWishlist={(id) => toggleSave(id)}
          isWishlisted={savedIds.includes(detailProduct?.id)}
        />
      )}

      {/* Direct Instant Order Modal (Saves to Supabase Cloud) */}
      {orderModalProduct && (
        <InstantOrderModal
          product={orderModalProduct}
          onClose={() => setOrderModalProduct(null)}
          onSuccess={() => setOrderModalProduct(null)}
        />
      )}
    </div>
  );
}
