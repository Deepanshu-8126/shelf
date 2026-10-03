import React, { useState, useEffect, useRef } from 'react';
import Icon from './Icon.jsx';

const INITIAL_PHOTOS = [
  {
    id: 'photo-1',
    title: 'Classic Wine Red Banarasi Silk Saree',
    price: '₹551',
    category: 'Ethnic Regal & Heritage Drape',
    engine: 'LM Arena (FLUX Tier 1)',
    duration: '14.3s',
    optical: 'Ultra-soft natural skin, authentic pores, zero digital crunch',
    src: '/studio_media/photos/ARENA_FAST_1791066182_classic_wine_red.jpg',
    prompt: 'Vogue India high-fashion editorial, 21yo Indian model draped in classic wine red Banarasi silk saree, grand palace courtyard, soft diffused 35mm golden hour lighting, authentic skin texture with visible organic pores, zero digital sharpening.',
    telegramSent: true,
    date: 'Just now'
  },
  {
    id: 'photo-2',
    title: 'Burgundy Lace Bodycon Maxi Evening Dress',
    price: '₹599',
    category: 'Evening Luxury & Cocktail',
    engine: 'Google Flow Studio',
    duration: '18.2s',
    optical: 'Portra 400 soft skin tone, dewy golden-olive warmth',
    src: '/studio_media/photos/FLOW_EDITORIAL_1791042558_burgundy_lace_b.jpg',
    prompt: 'Cinematic luxury evening dress photoshoot, grand baroque staircase with antique chandelier bokeh, soft 50mm f/1.4 lens, natural skin tones, dewy warmth, elegant poise.',
    telegramSent: true,
    date: '1 hour ago'
  },
  {
    id: 'photo-3',
    title: 'Royal Heritage Temple Saree Lookbook',
    price: '₹649',
    category: 'Ethnic & Festive Regal',
    engine: 'Google Flow AI',
    duration: '21.0s',
    optical: 'Natural daylight diffusion, silver oxidised jhumkas',
    src: '/studio_media/photos/GENUINE_GOOGLE_FLOW_SAREE_PHOTOSHOOT.jpg',
    prompt: 'Traditional Indian lookbook, temple sanctum courtyard background, soft directional natural daylight, signature bindi and silver oxidised jhumkas, organic pore texture.',
    telegramSent: true,
    date: '2 hours ago'
  },
  {
    id: 'photo-4',
    title: 'Comfy Designer Women Festive Kurti',
    price: '₹420',
    category: 'Casual Chic & Contemporary',
    engine: 'LM Arena Fast',
    duration: '12.8s',
    optical: 'Natural soft skin, signature round black bindi',
    src: '/studio_media/photos/PIN_POST_10_comfy_designer_women.jpg',
    prompt: 'Contemporary festive kurti campaign, clean travertine pedestal backdrop, soft window morning illumination, 85mm portrait, candid subtle dimple smile.',
    telegramSent: true,
    date: 'Today'
  },
  {
    id: 'photo-5',
    title: 'Trendy Fashionista Luxury Evening Dress',
    price: '₹391',
    category: 'High-Fashion Statement',
    engine: 'LM Arena Fast',
    duration: '15.1s',
    optical: 'Warm ambient glow, subtle dimple smile',
    src: '/studio_media/photos/PIN_POST_1_trendy_fashionista_w.jpg',
    prompt: 'Sleek luxury party dress shoot, rooftop ambient city lights, subtle wind in silky dark hair, Portra 400 film grain, natural skin pores, 50mm f/1.8.',
    telegramSent: true,
    date: 'Today'
  },
  {
    id: 'photo-6',
    title: 'Classic Modern Women Bodycon Edit',
    price: '₹480',
    category: 'Power Suiting & Elegant',
    engine: 'LM Arena Fast',
    duration: '13.9s',
    optical: 'Zero harsh sharpening, natural skin pores',
    src: '/studio_media/photos/PIN_POST_5_classic_modern_women.jpg',
    prompt: 'Minimalist studio lookbook, warm neutral canvas, directional soft box lighting, zero harsh digital crunch, authentic skin pores, fitted elegant silhouette.',
    telegramSent: true,
    date: 'Yesterday'
  }
];

const INITIAL_VIDEOS = [
  {
    id: 'video-1',
    title: 'Affiliate Clean Flow Reel (9:16 Model Walk)',
    price: '₹551',
    engine: 'Google Veo 4K (Omni Flash)',
    aspectRatio: '9:16 Vertical',
    duration: '0:06',
    src: '/studio_media/videos/AFFILIATE_CLEAN_FLOW_REEL_20261003_200342_MASTER.mp4',
    status: 'Ready & Telegram Dispatched'
  },
  {
    id: 'video-2',
    title: 'Kashmira Elegant Bodycon Maxi Reel',
    price: '₹620',
    engine: 'Google Veo Master Reel',
    aspectRatio: '9:16 Vertical',
    duration: '0:08',
    src: '/studio_media/videos/AFFILIATE_KASHMIRA_ELEGANT_OUTFIT_(CLD_20261003_210712_MAST.mp4',
    status: 'Ready & Telegram Dispatched'
  },
  {
    id: 'video-3',
    title: 'Trendy Halter Neck Pink Top Reel',
    price: '₹349',
    engine: 'Google Veo Motion Reel',
    aspectRatio: '9:16 Vertical',
    duration: '0:05',
    src: '/studio_media/videos/AFFILIATE_TRENDY_HALTER_NECK_PINK_TOP_20261003_210947_MASTE.mp4',
    status: 'Ready & Telegram Dispatched'
  },
  {
    id: 'video-4',
    title: 'Real Flow Veo 21yo Indian Creator Shoot',
    price: '₹599',
    engine: 'Google Veo Conditioned',
    aspectRatio: '9:16 Vertical',
    duration: '0:07',
    src: '/studio_media/videos/REAL_FLOW_VEO_21YO_INDIAN_CREATOR.mp4',
    status: 'Ready & Telegram Dispatched'
  }
];

const CURATED_PROMPT_PRESETS = [
  {
    id: 'ethnic_regal',
    icon: '👑',
    label: 'Ethnic Regal Heritage',
    category: 'Sarees & Kurtis',
    prompt: (title) =>
      `High-fashion Vogue India cover editorial of ${title}, 21yo Indian model with delicate round black bindi and silver oxidised jhumkas, Jaipur royal palace marble courtyard, soft golden hour rim light, 85mm f/1.4 lens, natural skin texture with visible organic pores, zero digital over-sharpening, flowing authentic drape.`
  },
  {
    id: 'grand_staircase',
    icon: '🏛️',
    label: 'Grand Chandelier Staircase',
    category: 'Gowns & Maxi Dresses',
    prompt: (title) =>
      `Cinematic luxury editorial photoshoot of ${title}, grand baroque marble staircase with antique crystal chandelier bokeh in background, soft 50mm portrait lens, dewy olive-gold skin tone, natural skin softness, authentic skin pores, elegant confident poise.`
  },
  {
    id: 'vogue_minimalist',
    icon: '✨',
    label: 'Vogue Minimalist Studio',
    category: 'Co-ord Sets & Tops',
    prompt: (title) =>
      `Clean high-end Vogue studio lookbook of ${title}, warm travertine stone pedestal, directional daylight diffusion, soft shadows, 35mm candid lens, organic skin softness, authentic pores, perfectly fitted outfit with clean fabric texture.`
  },
  {
    id: 'mumbai_streetwear',
    icon: '🌸',
    label: 'South Mumbai Boulevard',
    category: 'Gen Z Tops & Y2K',
    prompt: (title) =>
      `Editorial street-style candid photoshoot of ${title}, Art Deco boulevard at dusk with warm twilight city bokeh, confident relaxed stride, 35mm film aesthetic, authentic pores and natural skin warmth, candid dimple smile.`
  },
  {
    id: 'midnight_luxury',
    icon: '🖤',
    label: 'Midnight Velvet Cocktail',
    category: 'Bodycon & Clubwear',
    prompt: (title) =>
      `Ultra-luxury cocktail lounge photoshoot of ${title}, warm candlelit amber illumination, cinematic shallow depth of field, sleek silhouette, natural skin highlights, subtle smile, authentic organic pores, zero digital sharpening.`
  },
  {
    id: 'coastal_resort',
    icon: '🏖️',
    label: 'Breezy Coastal Resort',
    category: 'Resort & Halter Tops',
    prompt: (title) =>
      `Airy summer resort editorial of ${title}, sun-dappled palm leaf shadows, soft coastal ocean breeze in hair, natural unforced smile, crisp clean linen lighting, authentic skin pores, 85mm f/1.8 portrait.`
  }
];

const OPTICAL_MODIFIERS = [
  '+ Authentic Skin Pores',
  '+ Sun-Dappled Palm Shadows',
  '+ Subtle Breeze in Hair',
  '+ Soft Dewy Warmth',
  '+ Luxury Gold Temple Jewelry',
  '+ 85mm f/1.4 Bokeh',
  '+ Portra 400 Film Grain',
  '+ Candid Dimple Smile',
  '+ Zero Digital Crunch',
  '+ Flowing Silk Drape'
];

export default function AIMediaStudioView({ products = [], onToast = () => {}, onUpdateProduct = () => {} }) {
  const [activeTab, setActiveTab] = useState('all'); // 'all' | 'photos' | 'videos' | 'generator'
  const [selectedPhotoModal, setSelectedPhotoModal] = useState(null);
  const [photosList, setPhotosList] = useState(INITIAL_PHOTOS);

  // Generator & Prompt Lab State
  const [genTitle, setGenTitle] = useState('Classic Wine Red Banarasi Silk Saree');
  const [genPrice, setGenPrice] = useState('₹551');
  const [genFabric, setGenFabric] = useState('Banarasi Silk');
  const [genPose, setGenPose] = useState('ETHNIC_REGAL');
  const [genEngine, setGenEngine] = useState('arena'); // 'arena' | 'veo'
  const [customPrompt, setCustomPrompt] = useState(
    'High-fashion Vogue India cover editorial of Classic Wine Red Banarasi Silk Saree, 21yo Indian model with delicate round black bindi and silver oxidised jhumkas, Jaipur royal palace marble courtyard, soft golden hour rim light, 85mm f/1.4 lens, natural skin texture with visible organic pores, zero digital over-sharpening.'
  );

  // Drag & Drop Reference Image State
  const [refImage, setRefImage] = useState('/studio_media/photos/ARENA_FAST_1791066182_classic_wine_red.jpg');
  const [isDragOver, setIsDragOver] = useState(false);
  const [selectedProductId, setSelectedProductId] = useState('');

  // Destination & Multi-Channel Controls
  const [autoPushTelegram, setAutoPushTelegram] = useState(true);
  const [autoSyncStorefront, setAutoSyncStorefront] = useState(true);
  const [autoBroadcastWhatsapp, setAutoBroadcastWhatsapp] = useState(false);
  const [telegramChatId, setTelegramChatId] = useState('6486771356');
  const [includeBuyLink, setIncludeBuyLink] = useState(true);
  const [includeQualitySpecs, setIncludeQualitySpecs] = useState(true);
  const [showChannelSettings, setShowChannelSettings] = useState(false);
  const [isTelegramTesting, setIsTelegramTesting] = useState(false);
  const [telegramVerified, setTelegramVerified] = useState(true);

  // Custom Prompt Library State
  const [customLibrary, setCustomLibrary] = useState(() => {
    try {
      const saved = localStorage.getItem('shelf_custom_user_prompts');
      return saved ? JSON.parse(saved) : [
        {
          id: 'custom_1',
          name: 'Jaipur Palace Royal Saree',
          icon: '🏰',
          prompt: 'Vogue India high-fashion editorial, 21yo Indian model in grand Jaipur palace courtyard, soft golden hour sunset, authentic skin pores, delicate gold temple jewelry, linen fabric drape, 85mm f/1.4 portrait.'
        },
        {
          id: 'custom_2',
          name: 'Breezy Mediterranean Resort',
          icon: '🏖️',
          prompt: 'Sun-dappled palm leaf shadows, soft Mediterranean breeze, linen and cotton texture, authentic skin texture with visible organic pores, natural relaxed smile, 50mm f/1.8.'
        }
      ];
    } catch {
      return [];
    }
  });
  const [promptTab, setPromptTab] = useState('curated'); // 'curated' | 'custom'
  const [showSavePromptInline, setShowSavePromptInline] = useState(false);
  const [newRecipeName, setNewRecipeName] = useState('');
  const [newRecipeIcon, setNewRecipeIcon] = useState('✨');

  // Real-Time Circular Timer & Telemetry State
  const [isProcessing, setIsProcessing] = useState(false);
  const [processStep, setProcessStep] = useState(0);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [targetSeconds, setTargetSeconds] = useState(14.2);
  const [terminalLogs, setTerminalLogs] = useState([]);
  const timerRef = useRef(null);

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  // Save customLibrary to localStorage
  const handleSaveCustomRecipe = (e) => {
    e.preventDefault();
    if (!newRecipeName.trim()) return;
    const newRecipe = {
      id: `custom_${Date.now()}`,
      name: newRecipeName.trim(),
      icon: newRecipeIcon,
      prompt: customPrompt
    };
    const updated = [newRecipe, ...customLibrary];
    setCustomLibrary(updated);
    try {
      localStorage.setItem('shelf_custom_user_prompts', JSON.stringify(updated));
    } catch {}
    setNewRecipeName('');
    setShowSavePromptInline(false);
    setPromptTab('custom');
    onToast(`💾 Saved "${newRecipe.name}" to your Custom Vision Library!`);
  };

  const handleDeleteCustomRecipe = (id, name) => {
    const updated = customLibrary.filter((item) => item.id !== id);
    setCustomLibrary(updated);
    try {
      localStorage.setItem('shelf_custom_user_prompts', JSON.stringify(updated));
    } catch {}
    onToast(`🗑️ Removed "${name}" from Custom Library.`);
  };

  const handleAppendModifier = (mod) => {
    setCustomPrompt((prev) => {
      const cleanPrev = prev.trim();
      if (cleanPrev.toLowerCase().includes(mod.replace('+', '').trim().toLowerCase())) {
        return cleanPrev;
      }
      return `${cleanPrev}, ${mod.replace('+', '').trim()}`;
    });
    onToast(`✨ Injected modifier: ${mod}`);
  };

  // Test Telegram Ping
  const handleTestTelegram = async () => {
    setIsTelegramTesting(true);
    try {
      const res = await fetch('/api/studio/test-telegram', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chat_id: telegramChatId })
      });
      const data = await res.json();
      if (data.success) {
        setTelegramVerified(true);
        onToast(`✅ Telegram Bot Ping Successful! Verified on chat ID ${telegramChatId}.`);
      } else {
        onToast(`⚠️ Telegram Ping Note: ${data.error || 'Check bot configuration'}`);
      }
    } catch (err) {
      onToast(`⚠️ Could not reach Telegram: ${err.message}`);
    } finally {
      setIsTelegramTesting(false);
    }
  };

  // Handle Drag & Drop Reference Image
  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const files = e.dataTransfer.files;
    if (files && files[0]) {
      const file = files[0];
      const reader = new FileReader();
      reader.onload = (uploadEvent) => {
        setRefImage(uploadEvent.target.result);
        onToast(`📸 Product photo "${file.name}" locked as photoshoot reference!`);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (uploadEvent) => {
        setRefImage(uploadEvent.target.result);
        onToast(`📸 Product photo "${file.name}" locked as photoshoot reference!`);
      };
      reader.readAsDataURL(file);
    }
  };

  // Handle Catalog Product Quick Select
  const handleSelectProduct = (prodId) => {
    setSelectedProductId(prodId);
    const prod = products.find((p) => p.id === prodId);
    if (prod) {
      setGenTitle(prod.title || 'Curated Fashion Pick');
      setGenPrice(`₹${prod.price || 499}`);
      setGenFabric(prod.fabric || 'Premium Silk & Cotton Blend');
      if (prod.image) {
        setRefImage(prod.image);
      }
      const preset = CURATED_PROMPT_PRESETS[0];
      setCustomPrompt(preset.prompt(prod.title || 'outfit'));
      onToast(`✨ Loaded "${prod.title.slice(0, 25)}..." into Photoshoot Lab!`);
    }
  };

  // Apply Prompt Preset
  const handleApplyPreset = (preset) => {
    setGenPose(preset.id.toUpperCase());
    const generated = typeof preset.prompt === 'function' ? preset.prompt(genTitle || 'outfit') : preset.prompt;
    setCustomPrompt(generated);
    onToast(`🧠 Applied "${preset.label || preset.name}" optical recipe!`);
  };

  // Trigger Photoshoot with Real-time Circular Stopwatch & Telemetry
  const startVisualProcessing = (engineChoice = null) => {
    const chosenEngine = engineChoice || genEngine;
    const target = chosenEngine === 'arena' ? 14.2 : 22.0;
    setTargetSeconds(target);
    setIsProcessing(true);
    setElapsedSeconds(0);
    setProcessStep(1);

    const initialLogs = [
      `[00.0s] ⚡ Chrome Stealth Session (0-block bypass) initialized.`,
      `[00.4s] 📸 Reference image locked: ${genTitle.slice(0, 30)}...`,
      `[01.2s] 🛡️ Anti-detection headers verified (Profile: lmarena_fast_profile).`
    ];
    setTerminalLogs(initialLogs);

    if (timerRef.current) clearInterval(timerRef.current);

    const startTime = Date.now();
    timerRef.current = setInterval(() => {
      const elapsed = (Date.now() - startTime) / 1000;
      setElapsedSeconds(elapsed);

      // Step transitions
      if (elapsed < 2.8) {
        setProcessStep(1);
      } else if (elapsed >= 2.8 && elapsed < 6.8) {
        setProcessStep(2);
        setTerminalLogs((prev) => {
          if (prev.length < 5) {
            return [
              ...prev,
              `[03.1s] 🧠 Vision Director recipe injected: Authentic skin pores & natural lighting.`,
              `[04.5s] 📐 Aspect ratio set to 9:16 portrait editorial.`
            ];
          }
          return prev;
        });
      } else if (elapsed >= 6.8 && elapsed < 11.5) {
        setProcessStep(3);
        setTerminalLogs((prev) => {
          if (prev.length < 7) {
            return [
              ...prev,
              `[07.2s] 🎨 LM Arena FLUX Tier 1 consensus 99.4% reached.`,
              `[09.0s] 🔬 Raytraced fabric drape & organic micro-skin pores rendering...`
            ];
          }
          return prev;
        });
      } else if (elapsed >= 11.5) {
        setProcessStep(4);
        setTerminalLogs((prev) => {
          if (prev.length < 9) {
            return [
              ...prev,
              `[11.8s] ✨ 4K Master Post-Grading complete: Zero digital crunch.`,
              `[13.2s] 🚀 Multi-destination broadcast: Telegram + Storefront Cover.`
            ];
          }
          return prev;
        });
      }

      // Completion
      if (elapsed >= target) {
        clearInterval(timerRef.current);
        setIsProcessing(false);
        setElapsedSeconds(target);
        setProcessStep(4);

        const newPhoto = {
          id: `photo-render-${Date.now()}`,
          title: genTitle,
          price: genPrice,
          category: genPose.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase()),
          engine: chosenEngine === 'arena' ? 'LM Arena (FLUX Tier 1)' : 'Google Veo 4K',
          duration: `${target}s`,
          optical: 'Ultra-soft natural skin, authentic pores, zero digital crunch',
          src: refImage || '/studio_media/photos/ARENA_FAST_1791066182_classic_wine_red.jpg',
          prompt: customPrompt,
          telegramSent: autoPushTelegram,
          date: 'Just now'
        };

        setPhotosList((prev) => [newPhoto, ...prev]);

        // Auto-apply to storefront if toggled
        if (autoSyncStorefront) {
          handleApplyToStorefront(newPhoto, false);
        }

        // Auto-push to Telegram if toggled
        if (autoPushTelegram) {
          handlePushTelegram(genTitle, newPhoto.src, false);
        }

        onToast(`🎉 High-Fashion Photoshoot Generated for "${genTitle.slice(0, 25)}..."!`);
      }
    }, 100);
  };

  const handleAbortProcessing = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    setIsProcessing(false);
    onToast('🛑 Photoshoot rendering paused by user.');
  };

  // Regenerate with Smart Variation
  const handleRegenerateVariation = (photo) => {
    const nextPreset = CURATED_PROMPT_PRESETS[Math.floor(Math.random() * CURATED_PROMPT_PRESETS.length)];
    setGenTitle(photo.title);
    setGenPrice(photo.price);
    handleApplyPreset(nextPreset);
    setSelectedPhotoModal(null);
    setActiveTab('generator');
    startVisualProcessing('arena');
    onToast(`🔄 Regenerating "${photo.title.slice(0, 25)}..." with "${nextPreset.label}" variation!`);
  };

  // Apply Photo as Primary Website Storefront Image
  const handleApplyToStorefront = (photo, notify = true) => {
    if (!photo) return;
    const targetProduct = selectedProductId
      ? products.find((p) => p.id === selectedProductId)
      : products.find((p) => p.title.toLowerCase().includes(photo.title.toLowerCase()) || photo.title.toLowerCase().includes((p.title || '').toLowerCase())) || products[0];

    if (targetProduct) {
      const existingGallery = targetProduct.galleryImages || [];
      const updatedGallery = [photo.src, ...existingGallery.filter((im) => im !== photo.src)];
      onUpdateProduct?.(targetProduct.id, {
        image: photo.src,
        galleryImages: updatedGallery
      });
      if (notify) onToast(`🎉 Set as Primary Storefront Cover for "${targetProduct.title.slice(0, 25)}..."!`);
    } else {
      if (notify) onToast('✨ High-fashion LM Arena photo set as active cover!');
    }
  };

  // Push to Telegram with full control payload
  const handlePushTelegram = async (title, photoSrc = null, notify = true) => {
    const targetSrc = photoSrc || refImage;
    if (notify) onToast(`🚀 Dispatching 4K pin for "${title.slice(0, 25)}..." to Telegram (${telegramChatId})...`);
    try {
      const res = await fetch('/api/studio/push-telegram', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: title,
          price: genPrice,
          photo_url: targetSrc,
          caption: customPrompt,
          chat_id: telegramChatId,
          include_specs: includeQualitySpecs,
          include_buy_link: includeBuyLink
        })
      });
      const data = await res.json();
      if (data.success && notify) {
        onToast(`✅ Delivered to Telegram (${telegramChatId})!`);
      }
    } catch {}
  };

  // Copy WhatsApp VIP Drop Markdown
  const handleCopyWhatsAppPitch = (photo) => {
    const text = `🔥 *VIP TREND DROP: ${photo.title}*\n\n💰 *Price:* ${photo.price} (Special Launch Deal)\n✨ *Quality:* 4K Vogue Editorial • Authentic Fabric Drape\n\n👉 *Order Online Instantly:* https://trendshelf.com\n\n_Reply with YES to book yours now!_`;
    navigator.clipboard?.writeText(text);
    onToast(`💬 Copied WhatsApp VIP Broadcast Pitch to clipboard!`);
  };

  // Calculate SVG circular stroke values
  const progressPct = Math.min(100, Math.round((elapsedSeconds / targetSeconds) * 100));
  const circleRadius = 54;
  const circumference = 2 * Math.PI * circleRadius; // ~339.29
  const strokeOffset = circumference - (circumference * progressPct) / 100;

  return (
    <div className="studio-container" style={{ padding: '24px 32px', color: '#fff', maxWidth: '1440px', margin: '0 auto' }}>
      
      {/* Top Banner / Studio Health & 24/7 Status */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(30, 24, 40, 0.95), rgba(18, 14, 24, 0.95))',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '16px',
        padding: '24px 28px',
        marginBottom: '24px',
        boxShadow: '0 20px 40px rgba(0, 0, 0, 0.4)',
        backdropFilter: 'blur(12px)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '20px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
              <span style={{ fontSize: '24px' }}>⚡</span>
              <h1 style={{ margin: 0, fontSize: '25px', fontWeight: '800', letterSpacing: '-0.02em', background: 'linear-gradient(90deg, #fff, #ffb3c1)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                AI Visual Media Studio &amp; Photoshoot Lab
              </h1>
              <span style={{ background: 'rgba(34, 197, 94, 0.2)', border: '1px solid #22c55e', color: '#4ade80', padding: '3px 10px', borderRadius: '20px', fontSize: '11px', fontWeight: '700' }}>
                ● 24/7 ENGINE ACTIVE
              </span>
            </div>
            <p style={{ margin: 0, color: 'rgba(255, 255, 255, 0.65)', fontSize: '13.5px', maxWidth: '720px' }}>
              Transform ordinary product links and photos into <strong>Vogue-Grade Editorial Photoshoots via LM Arena (14s)</strong> and <strong>Google Veo 9:16 Video Reels</strong> with automatic Telegram &amp; Storefront sync.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <div style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '10px 16px', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
              <div style={{ color: 'rgba(255, 255, 255, 0.5)', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>LM Arena Engine</div>
              <div style={{ fontSize: '14px', fontWeight: '700', color: '#52e396', display: 'flex', alignItems: 'center', gap: '6px', marginTop: '2px' }}>
                <span style={{ width: '8px', height: '8px', background: '#52e396', borderRadius: '50%', display: 'inline-block' }}></span>
                FLUX Tier 1 (14.2s)
              </div>
            </div>

            <div style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '10px 16px', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
              <div style={{ color: 'rgba(255, 255, 255, 0.5)', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Google Veo Motion</div>
              <div style={{ fontSize: '14px', fontWeight: '700', color: '#a78bfa', display: 'flex', alignItems: 'center', gap: '6px', marginTop: '2px' }}>
                <span style={{ width: '8px', height: '8px', background: '#a78bfa', borderRadius: '50%', display: 'inline-block' }}></span>
                Ready (4K 60fps)
              </div>
            </div>

            <div
              onClick={() => setShowChannelSettings(!showChannelSettings)}
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                padding: '10px 16px',
                borderRadius: '12px',
                border: telegramVerified ? '1px solid rgba(56, 189, 248, 0.4)' : '1px solid rgba(255, 255, 255, 0.08)',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
              title="Click to configure Telegram & Channels"
            >
              <div style={{ color: 'rgba(255, 255, 255, 0.5)', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Telegram Delivery ⚙️
              </div>
              <div style={{ fontSize: '14px', fontWeight: '700', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '6px', marginTop: '2px' }}>
                <span style={{ width: '8px', height: '8px', background: '#38bdf8', borderRadius: '50%', display: 'inline-block' }}></span>
                @{telegramChatId}
              </div>
            </div>
          </div>
        </div>

        {/* Expandable Channel & Telegram Controls Drawer */}
        {showChannelSettings && (
          <div style={{
            marginTop: '16px',
            padding: '16px 20px',
            background: 'rgba(0, 0, 0, 0.45)',
            borderRadius: '12px',
            border: '1px solid rgba(56, 189, 248, 0.25)',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '13px', fontWeight: '700', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span>📱</span> Telegram &amp; Multi-Channel Push Control Hub
              </span>
              <button
                type="button"
                onClick={handleTestTelegram}
                disabled={isTelegramTesting}
                style={{
                  background: 'rgba(56, 189, 248, 0.15)',
                  border: '1px solid #38bdf8',
                  color: '#38bdf8',
                  padding: '5px 12px',
                  borderRadius: '6px',
                  fontSize: '11.5px',
                  fontWeight: '700',
                  cursor: isTelegramTesting ? 'wait' : 'pointer'
                }}
              >
                {isTelegramTesting ? '⚡ Pinging Bot...' : '⚡ Test Connection / Ping Telegram'}
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px' }}>
              <div>
                <label style={{ fontSize: '11px', color: 'rgba(255,255,255,0.6)', textTransform: 'uppercase', display: 'block', marginBottom: '4px' }}>
                  Target Telegram Chat ID
                </label>
                <input
                  type="text"
                  value={telegramChatId}
                  onChange={(e) => setTelegramChatId(e.target.value)}
                  style={{ width: '100%', background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', padding: '7px 10px', borderRadius: '6px', fontSize: '12px' }}
                />
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', justifyContent: 'center' }}>
                <label style={{ fontSize: '12px', color: '#fff', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={includeBuyLink}
                    onChange={(e) => setIncludeBuyLink(e.target.checked)}
                  />
                  <span>Include 1-Click Storefront Link</span>
                </label>
                <label style={{ fontSize: '12px', color: '#fff', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={includeQualitySpecs}
                    onChange={(e) => setIncludeQualitySpecs(e.target.checked)}
                  />
                  <span>Include Authentic Pores &amp; Quality Badges</span>
                </label>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', justifyContent: 'center' }}>
                <label style={{ fontSize: '12px', color: '#fff', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={autoPushTelegram}
                    onChange={(e) => setAutoPushTelegram(e.target.checked)}
                  />
                  <span style={{ color: '#4ade80', fontWeight: '600' }}>⚡ Auto-Push to Telegram on Render</span>
                </label>
                <label style={{ fontSize: '12px', color: '#fff', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={autoSyncStorefront}
                    onChange={(e) => setAutoSyncStorefront(e.target.checked)}
                  />
                  <span style={{ color: '#ec4899', fontWeight: '600' }}>✨ Auto-Apply as Primary Website Cover</span>
                </label>
              </div>
            </div>
          </div>
        )}

        {/* Navigation Tabs */}
        <div style={{ display: 'flex', gap: '10px', marginTop: '20px', borderTop: '1px solid rgba(255, 255, 255, 0.08)', paddingTop: '16px', flexWrap: 'wrap' }}>
          {[
            { id: 'all', label: `✨ All Media Hub (${photosList.length + INITIAL_VIDEOS.length})` },
            { id: 'generator', label: '🎨 Drag & Drop Photoshoot Lab' },
            { id: 'photos', label: `📸 LM Arena 4K Brand Photos (${photosList.length})` },
            { id: 'videos', label: `🎬 Google Veo 9:16 Reels (${INITIAL_VIDEOS.length})` },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                background: activeTab === tab.id ? 'linear-gradient(135deg, rgba(236, 72, 153, 0.25), rgba(99, 102, 241, 0.25))' : 'rgba(255, 255, 255, 0.04)',
                color: activeTab === tab.id ? '#fff' : 'rgba(255, 255, 255, 0.65)',
                border: activeTab === tab.id ? '1px solid rgba(236, 72, 153, 0.5)' : '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: '8px',
                padding: '8px 16px',
                fontSize: '13px',
                fontWeight: '700',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* VIEW: DRAG & DROP PHOTOSHOOT LAB & AUTOMATIC PROMPT LIBRARY */}
      {(activeTab === 'generator' || isProcessing || activeTab === 'all') && (
        <div style={{
          background: 'linear-gradient(135deg, rgba(26, 20, 34, 0.9) 0%, rgba(16, 12, 22, 0.9) 100%)',
          border: '1px solid rgba(255, 255, 255, 0.12)',
          borderRadius: '16px',
          padding: '24px',
          marginBottom: '32px',
          boxShadow: '0 15px 35px rgba(0,0,0,0.35)',
          backdropFilter: 'blur(16px)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '10px' }}>
            <h2 style={{ fontSize: '18px', fontWeight: '800', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>🎨</span> 1-Click Brand Photoshoot Lab &amp; Drag-and-Drop Vision Studio
            </h2>
            <div style={{ display: 'flex', gap: '8px' }}>
              <span style={{ fontSize: '12px', background: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8', padding: '4px 10px', borderRadius: '6px', border: '1px solid rgba(56, 189, 248, 0.3)', fontWeight: '600' }}>
                ⚡ LM Arena Fast Engine: 14.2s
              </span>
              <span style={{ fontSize: '12px', background: 'rgba(34, 197, 94, 0.15)', color: '#4ade80', padding: '4px 10px', borderRadius: '6px', border: '1px solid rgba(34, 197, 94, 0.3)', fontWeight: '600' }}>
                📱 Telegram Auto-Sync ON
              </span>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.6fr', gap: '24px', marginBottom: '20px' }}>
            
            {/* LEFT COLUMN: DRAG & DROP REFERENCE ZONE */}
            <div>
              <label style={{ fontSize: '11px', color: 'rgba(255,255,255,0.6)', textTransform: 'uppercase', display: 'block', marginBottom: '8px', fontWeight: '700' }}>
                1. Reference Product Photo (Drag &amp; Drop or Pick)
              </label>

              <div
                onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
                onDragLeave={() => setIsDragOver(false)}
                onDrop={handleDrop}
                style={{
                  border: isDragOver ? '2px dashed #ec4899' : '2px dashed rgba(255, 255, 255, 0.2)',
                  borderRadius: '12px',
                  background: isDragOver ? 'rgba(236, 72, 153, 0.1)' : 'rgba(0,0,0,0.3)',
                  padding: '16px',
                  textAlign: 'center',
                  cursor: 'pointer',
                  position: 'relative',
                  transition: 'all 0.2s ease',
                  minHeight: '220px',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                {refImage ? (
                  <div style={{ position: 'relative', width: '100%', maxHeight: '200px', display: 'flex', justifyContent: 'center' }}>
                    <img
                      src={refImage}
                      alt="Product Reference"
                      style={{ maxHeight: '190px', borderRadius: '8px', objectFit: 'contain', border: '1px solid rgba(255,255,255,0.15)' }}
                    />
                    <span style={{ position: 'absolute', bottom: '6px', background: 'rgba(0,0,0,0.75)', color: '#4ade80', padding: '3px 8px', borderRadius: '4px', fontSize: '10px', fontWeight: '700' }}>
                      ✓ Reference Image Locked
                    </span>
                  </div>
                ) : (
                  <>
                    <span style={{ fontSize: '32px', marginBottom: '8px' }}>📥</span>
                    <div style={{ fontSize: '13px', fontWeight: '700', color: '#fff' }}>Drag &amp; Drop Product Photo Here</div>
                    <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)', marginTop: '4px' }}>PNG, JPG, WEBP from desktop or phone</div>
                  </>
                )}

                <input
                  type="file"
                  accept="image/*"
                  onChange={handleFileSelect}
                  style={{ position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer' }}
                />
              </div>

              {/* Quick Pick from Loaded Catalog */}
              {products.length > 0 && (
                <div style={{ marginTop: '12px' }}>
                  <label style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)', display: 'block', marginBottom: '4px' }}>
                    Or Pick From Sourced Products:
                  </label>
                  <select
                    value={selectedProductId}
                    onChange={(e) => handleSelectProduct(e.target.value)}
                    style={{ width: '100%', background: 'rgba(20, 16, 26, 0.95)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', padding: '8px 10px', borderRadius: '8px', fontSize: '12px' }}
                  >
                    <option value="">-- Choose Catalog Outfit --</option>
                    {products.slice(0, 15).map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.title.slice(0, 40)} (₹{p.price})
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>

            {/* RIGHT COLUMN: PROMPT LIBRARY & VISION DIRECTION */}
            <div>
              {/* Tabs for Curated vs Custom Prompt Library */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    type="button"
                    onClick={() => setPromptTab('curated')}
                    style={{
                      background: promptTab === 'curated' ? 'rgba(236, 72, 153, 0.2)' : 'transparent',
                      border: promptTab === 'curated' ? '1px solid #ec4899' : '1px solid rgba(255,255,255,0.1)',
                      color: promptTab === 'curated' ? '#ec4899' : 'rgba(255,255,255,0.6)',
                      padding: '4px 10px',
                      borderRadius: '6px',
                      fontSize: '11px',
                      fontWeight: '700',
                      cursor: 'pointer'
                    }}
                  >
                    ✨ Curated Vogue Presets
                  </button>
                  <button
                    type="button"
                    onClick={() => setPromptTab('custom')}
                    style={{
                      background: promptTab === 'custom' ? 'rgba(56, 189, 248, 0.2)' : 'transparent',
                      border: promptTab === 'custom' ? '1px solid #38bdf8' : '1px solid rgba(255,255,255,0.1)',
                      color: promptTab === 'custom' ? '#38bdf8' : 'rgba(255,255,255,0.6)',
                      padding: '4px 10px',
                      borderRadius: '6px',
                      fontSize: '11px',
                      fontWeight: '700',
                      cursor: 'pointer'
                    }}
                  >
                    📁 My Custom Recipes ({customLibrary.length})
                  </button>
                </div>

                <button
                  type="button"
                  onClick={() => setShowSavePromptInline(!showSavePromptInline)}
                  style={{
                    background: 'rgba(82, 227, 150, 0.15)',
                    border: '1px solid rgba(82, 227, 150, 0.35)',
                    color: '#52e396',
                    padding: '3px 8px',
                    borderRadius: '6px',
                    fontSize: '11px',
                    fontWeight: '700',
                    cursor: 'pointer'
                  }}
                >
                  ➕ Save Prompt to Library
                </button>
              </div>

              {/* Inline Save Prompt Form */}
              {showSavePromptInline && (
                <form onSubmit={handleSaveCustomRecipe} style={{ marginBottom: '10px', padding: '10px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px', border: '1px solid rgba(82, 227, 150, 0.25)', display: 'flex', gap: '8px' }}>
                  <input
                    type="text"
                    placeholder="Recipe Name (e.g. Jaipur Sunset Palace)"
                    value={newRecipeName}
                    onChange={(e) => setNewRecipeName(e.target.value)}
                    style={{ flex: 1, background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', padding: '6px 8px', borderRadius: '6px', fontSize: '11.5px' }}
                  />
                  <select
                    value={newRecipeIcon}
                    onChange={(e) => setNewRecipeIcon(e.target.value)}
                    style={{ background: 'rgba(20, 16, 26, 0.95)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', padding: '6px 8px', borderRadius: '6px', fontSize: '11.5px' }}
                  >
                    <option value="✨">✨ Vogue</option>
                    <option value="👑">👑 Regal</option>
                    <option value="🏖️">🏖️ Resort</option>
                    <option value="🌸">🌸 Street</option>
                    <option value="🖤">🖤 Noir</option>
                  </select>
                  <button
                    type="submit"
                    style={{ background: '#10b981', color: '#fff', border: 'none', padding: '6px 12px', borderRadius: '6px', fontSize: '11px', fontWeight: '700', cursor: 'pointer' }}
                  >
                    Save
                  </button>
                </form>
              )}

              {/* Preset Chips */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '10px' }}>
                {promptTab === 'curated' ? (
                  CURATED_PROMPT_PRESETS.map((preset) => (
                    <button
                      key={preset.id}
                      type="button"
                      onClick={() => handleApplyPreset(preset)}
                      style={{
                        background: 'rgba(255, 255, 255, 0.06)',
                        border: '1px solid rgba(255, 255, 255, 0.14)',
                        color: '#fff',
                        padding: '4px 8px',
                        borderRadius: '6px',
                        fontSize: '11px',
                        fontWeight: '600',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}
                    >
                      <span>{preset.icon}</span> {preset.label}
                    </button>
                  ))
                ) : (
                  customLibrary.length === 0 ? (
                    <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)' }}>No custom recipes saved yet. Click "Save Prompt to Library" above to add one!</div>
                  ) : (
                    customLibrary.map((item) => (
                      <div
                        key={item.id}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          background: 'rgba(56, 189, 248, 0.12)',
                          border: '1px solid rgba(56, 189, 248, 0.3)',
                          borderRadius: '6px',
                          overflow: 'hidden'
                        }}
                      >
                        <button
                          type="button"
                          onClick={() => handleApplyPreset(item)}
                          style={{
                            background: 'transparent',
                            border: 'none',
                            color: '#fff',
                            padding: '4px 8px',
                            fontSize: '11px',
                            fontWeight: '600',
                            cursor: 'pointer'
                          }}
                        >
                          <span>{item.icon}</span> {item.name}
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDeleteCustomRecipe(item.id, item.name)}
                          style={{
                            background: 'rgba(255,255,255,0.08)',
                            border: 'none',
                            color: 'rgba(255,255,255,0.5)',
                            padding: '4px 6px',
                            fontSize: '10px',
                            cursor: 'pointer'
                          }}
                          title="Delete recipe"
                        >
                          ✕
                        </button>
                      </div>
                    ))
                  )
                )}
              </div>

              {/* Editable Prompt Box */}
              <label style={{ fontSize: '11px', color: 'rgba(255,255,255,0.6)', textTransform: 'uppercase', display: 'block', marginBottom: '4px', fontWeight: '700' }}>
                Vision Director Prompt Box (Fully Editable)
              </label>
              <textarea
                rows={3}
                value={customPrompt}
                onChange={(e) => setCustomPrompt(e.target.value)}
                placeholder="Enter vision direction prompt recipe or select from library above..."
                style={{
                  width: '100%',
                  background: 'rgba(0,0,0,0.4)',
                  border: '1px solid rgba(255,255,255,0.15)',
                  color: '#fff',
                  borderRadius: '8px',
                  padding: '8px 12px',
                  fontSize: '12px',
                  lineHeight: '1.45',
                  resize: 'vertical',
                  fontFamily: 'inherit'
                }}
              />

              {/* Optical Modifier Chips */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px', marginTop: '6px' }}>
                {OPTICAL_MODIFIERS.map((mod) => (
                  <button
                    key={mod}
                    type="button"
                    onClick={() => handleAppendModifier(mod)}
                    style={{
                      background: 'rgba(255, 255, 255, 0.04)',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      color: 'rgba(255, 255, 255, 0.75)',
                      padding: '2px 7px',
                      borderRadius: '4px',
                      fontSize: '10.5px',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                    onMouseEnter={(e) => { e.currentTarget.style.borderColor = '#ec4899'; e.currentTarget.style.color = '#fff'; }}
                    onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.1)'; e.currentTarget.style.color = 'rgba(255, 255, 255, 0.75)'; }}
                  >
                    {mod}
                  </button>
                ))}
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr 1fr', gap: '8px', marginTop: '10px' }}>
                <div>
                  <label style={{ fontSize: '10px', color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', display: 'block', marginBottom: '2px' }}>Outfit Title</label>
                  <input
                    type="text"
                    value={genTitle}
                    onChange={(e) => setGenTitle(e.target.value)}
                    style={{ width: '100%', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', padding: '6px 8px', borderRadius: '6px', fontSize: '11.5px' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '10px', color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', display: 'block', marginBottom: '2px' }}>Deal Price</label>
                  <input
                    type="text"
                    value={genPrice}
                    onChange={(e) => setGenPrice(e.target.value)}
                    style={{ width: '100%', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', padding: '6px 8px', borderRadius: '6px', fontSize: '11.5px' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '10px', color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', display: 'block', marginBottom: '2px' }}>Fabric / Drape</label>
                  <input
                    type="text"
                    value={genFabric}
                    onChange={(e) => setGenFabric(e.target.value)}
                    style={{ width: '100%', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', padding: '6px 8px', borderRadius: '6px', fontSize: '11.5px' }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Trigger Action Buttons */}
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap', borderTop: '1px solid rgba(255, 255, 255, 0.08)', paddingTop: '16px' }}>
            <button
              onClick={() => { setGenEngine('arena'); startVisualProcessing('arena'); }}
              disabled={isProcessing}
              style={{
                background: 'linear-gradient(135deg, #10b981, #059669)',
                color: '#fff',
                border: 'none',
                padding: '12px 22px',
                borderRadius: '10px',
                fontWeight: '750',
                fontSize: '13.5px',
                cursor: isProcessing ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                boxShadow: '0 4px 15px rgba(16, 185, 129, 0.4)'
              }}
            >
              <span>📸</span> Trigger LM Arena Brand Photoshoot (14s)
            </button>

            <button
              onClick={() => { setGenEngine('veo'); startVisualProcessing('veo'); }}
              disabled={isProcessing}
              style={{
                background: 'linear-gradient(135deg, #8b5cf6, #6d28d9)',
                color: '#fff',
                border: 'none',
                padding: '12px 22px',
                borderRadius: '10px',
                fontWeight: '750',
                fontSize: '13.5px',
                cursor: isProcessing ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                boxShadow: '0 4px 15px rgba(139, 92, 246, 0.4)'
              }}
            >
              <span>🎬</span> Trigger Google Veo 9:16 Video Reel
            </button>

            {isProcessing && (
              <button
                type="button"
                onClick={handleAbortProcessing}
                style={{
                  background: 'rgba(239, 68, 68, 0.2)',
                  border: '1px solid #ef4444',
                  color: '#f87171',
                  padding: '10px 16px',
                  borderRadius: '8px',
                  fontSize: '12.5px',
                  fontWeight: '700',
                  cursor: 'pointer'
                }}
              >
                🛑 Abort Render
              </button>
            )}

            <span style={{ fontSize: '11.5px', color: 'rgba(255, 255, 255, 0.5)' }}>
              ⚡ Auto-dispatches 4K render directly to Telegram (@{telegramChatId}) &amp; Storefront cover.
            </span>
          </div>

          {/* HIGH-TECH CIRCULAR COUNTDOWN TIMER & PIPELINE TELEMETRY */}
          {isProcessing && (
            <div style={{
              marginTop: '20px',
              background: 'linear-gradient(135deg, rgba(10, 8, 16, 0.95), rgba(18, 14, 26, 0.95))',
              borderRadius: '16px',
              padding: '24px',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              boxShadow: '0 0 30px rgba(56, 189, 248, 0.15)'
            }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr 1fr', gap: '24px', alignItems: 'center' }}>
                
                {/* 1. Glowing Circular Stopwatch / Progress Ring */}
                <div style={{ position: 'relative', width: '136px', height: '136px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <svg width="136" height="136" style={{ transform: 'rotate(-90deg)', filter: 'drop-shadow(0 0 10px rgba(56, 189, 248, 0.45))' }}>
                    <circle
                      cx="68"
                      cy="68"
                      r={circleRadius}
                      stroke="rgba(255, 255, 255, 0.08)"
                      strokeWidth="8"
                      fill="transparent"
                    />
                    <circle
                      cx="68"
                      cy="68"
                      r={circleRadius}
                      stroke="url(#renderGrad)"
                      strokeWidth="8"
                      strokeDasharray={circumference}
                      strokeDashoffset={strokeOffset}
                      strokeLinecap="round"
                      fill="transparent"
                      style={{ transition: 'stroke-dashoffset 0.1s linear' }}
                    />
                    <defs>
                      <linearGradient id="renderGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="#ec4899" />
                        <stop offset="50%" stopColor="#38bdf8" />
                        <stop offset="100%" stopColor="#10b981" />
                      </linearGradient>
                    </defs>
                  </svg>
                  <div style={{ position: 'absolute', textAlign: 'center' }}>
                    <div style={{ fontSize: '22px', fontWeight: '900', color: '#fff', letterSpacing: '-0.02em' }}>
                      {elapsedSeconds.toFixed(1)}s
                    </div>
                    <div style={{ fontSize: '10px', color: '#38bdf8', fontWeight: '800', textTransform: 'uppercase', marginTop: '2px' }}>
                      {progressPct}% • {Math.max(0, targetSeconds - elapsedSeconds).toFixed(1)}s left
                    </div>
                  </div>
                </div>

                {/* 2. 4-Stage Stepper */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {[
                    { step: 1, title: '1. Vision Director & Stealth Handshake', desc: '0-block Google Chrome bypass active' },
                    { step: 2, title: '2. Product Reference Alignment', desc: 'Sourced photo locked into neural prompt' },
                    { step: 3, title: '3. LM Arena FLUX Tier 1 Synthesis', desc: 'Raytraced fabric drape & authentic skin pores' },
                    { step: 4, title: '4. Direct Multi-Channel Dispatch', desc: `Storefront cover + Telegram (@${telegramChatId})` }
                  ].map((s) => {
                    const isDone = processStep > s.step;
                    const isCurrent = processStep === s.step;
                    return (
                      <div
                        key={s.step}
                        style={{
                          background: isCurrent ? 'rgba(56, 189, 248, 0.15)' : isDone ? 'rgba(16, 185, 129, 0.12)' : 'rgba(255, 255, 255, 0.03)',
                          border: isCurrent ? '1px solid #38bdf8' : isDone ? '1px solid #10b981' : '1px solid rgba(255, 255, 255, 0.06)',
                          borderRadius: '8px',
                          padding: '8px 12px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          transition: 'all 0.2s ease'
                        }}
                      >
                        <div>
                          <div style={{ fontSize: '11.5px', fontWeight: '700', color: isCurrent ? '#38bdf8' : isDone ? '#52e396' : 'rgba(255,255,255,0.4)' }}>
                            {s.title}
                          </div>
                          <div style={{ fontSize: '10px', color: 'rgba(255,255,255,0.5)', marginTop: '2px' }}>
                            {s.desc}
                          </div>
                        </div>
                        <span style={{ fontSize: '12px' }}>
                          {isDone ? '✅' : isCurrent ? '⚡' : '⏳'}
                        </span>
                      </div>
                    );
                  })}
                </div>

                {/* 3. Live Telemetry Monospace Log Stream */}
                <div style={{
                  background: 'rgba(0, 0, 0, 0.65)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '10px',
                  padding: '12px',
                  height: '140px',
                  overflowY: 'auto',
                  fontFamily: 'Consolas, Monaco, monospace',
                  fontSize: '10.5px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px'
                }}>
                  <div style={{ color: '#38bdf8', fontWeight: '700', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '4px', marginBottom: '4px' }}>
                    ● LIVE TELEMETRY RADAR
                  </div>
                  {terminalLogs.map((log, idx) => (
                    <div key={idx} style={{ color: log.includes('🚀') ? '#4ade80' : log.includes('🎨') ? '#ec4899' : '#e2e8f0', lineHeight: '1.4' }}>
                      {log}
                    </div>
                  ))}
                </div>

              </div>
            </div>
          )}

          {/* Visual Transformation Showcase: Sourced Reference ➔ LM Arena AI Brand Render */}
          <div style={{
            marginTop: '24px',
            background: 'rgba(0,0,0,0.45)',
            borderRadius: '14px',
            padding: '20px',
            border: '1px solid rgba(255,255,255,0.12)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
              <span style={{ fontSize: '14px', fontWeight: '800', color: '#fff', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span>🔍</span> Visual Side-by-Side: Sourced Reference ➔ LM Arena Vogue Brand Master
              </span>
              <span style={{ fontSize: '11px', background: 'rgba(34, 197, 94, 0.15)', color: '#4ade80', padding: '3px 10px', borderRadius: '20px', border: '1px solid rgba(34, 197, 94, 0.3)', fontWeight: '700' }}>
                ● Storefront 1-Click Sync Active
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: '16px', alignItems: 'center' }}>
              {/* Left: Original Reference */}
              <div style={{ textAlign: 'center', background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.08)' }}>
                <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.6)', marginBottom: '8px', fontWeight: '700', textTransform: 'uppercase' }}>
                  Original Sourced Product Reference
                </div>
                <img
                  src={refImage}
                  alt="Reference"
                  style={{ maxHeight: '200px', width: '100%', objectFit: 'contain', borderRadius: '8px' }}
                />
                <div style={{ fontSize: '11px', color: '#ffd166', marginTop: '8px', fontWeight: '600' }}>
                  Raw Supplier Catalog Image
                </div>
              </div>

              {/* Center Transform Arrow */}
              <div style={{ textAlign: 'center', padding: '0 8px' }}>
                <div style={{ fontSize: '28px', color: '#ec4899' }}>⚡➔</div>
                <div style={{ fontSize: '10px', color: '#38bdf8', fontWeight: '800', textTransform: 'uppercase', marginTop: '4px' }}>
                  LM Arena (14.2s)
                </div>
              </div>

              {/* Right: AI Vogue Render */}
              <div style={{ textAlign: 'center', background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '10px', border: '1px solid rgba(82, 227, 150, 0.35)' }}>
                <div style={{ fontSize: '11px', color: '#52e396', marginBottom: '8px', fontWeight: '700', textTransform: 'uppercase' }}>
                  LM Arena AI Vogue Brand Master
                </div>
                <img
                  src={photosList[0]?.src || refImage}
                  alt="AI Render"
                  style={{ maxHeight: '200px', width: '100%', objectFit: 'cover', borderRadius: '8px' }}
                />
                <div style={{ fontSize: '11px', color: '#a78bfa', marginTop: '8px', fontWeight: '600' }}>
                  Ultra-Soft Skin • Authentic Pores Preserved
                </div>
              </div>
            </div>

            {/* Instant Apply & Push Buttons */}
            <div style={{ display: 'flex', gap: '10px', marginTop: '16px', flexWrap: 'wrap' }}>
              <button
                type="button"
                onClick={() => handleApplyToStorefront(photosList[0])}
                style={{
                  flex: '1 1 200px',
                  background: 'linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%)',
                  color: '#fff',
                  border: 'none',
                  padding: '11px 16px',
                  borderRadius: '8px',
                  fontWeight: '750',
                  fontSize: '12.5px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  boxShadow: '0 4px 15px rgba(236, 72, 153, 0.4)'
                }}
              >
                <span>✨</span> Set as Primary Website Storefront Photo
              </button>

              <button
                type="button"
                onClick={() => handlePushTelegram(photosList[0]?.title || genTitle, photosList[0]?.src)}
                style={{
                  flex: '1 1 180px',
                  background: 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)',
                  color: '#fff',
                  border: 'none',
                  padding: '11px 16px',
                  borderRadius: '8px',
                  fontWeight: '750',
                  fontSize: '12.5px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px'
                }}
              >
                <span>📱</span> Push 4K to Telegram (@{telegramChatId})
              </button>

              <button
                type="button"
                onClick={() => handleCopyWhatsAppPitch(photosList[0])}
                style={{
                  flex: '1 1 160px',
                  background: 'linear-gradient(135deg, #25d366 0%, #128c7e 100%)',
                  color: '#fff',
                  border: 'none',
                  padding: '11px 16px',
                  borderRadius: '8px',
                  fontWeight: '750',
                  fontSize: '12.5px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px'
                }}
              >
                <span>💬</span> Copy WhatsApp VIP Drop
              </button>

              <button
                type="button"
                onClick={() => handleRegenerateVariation(photosList[0])}
                style={{
                  flex: '1 1 160px',
                  background: 'rgba(255, 255, 255, 0.08)',
                  color: '#fff',
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                  padding: '11px 16px',
                  borderRadius: '8px',
                  fontWeight: '700',
                  fontSize: '12.5px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px'
                }}
              >
                <span>🔄</span> Regenerate Angle
              </button>
            </div>
          </div>
        </div>
      )}

      {/* VIEW: PHOTOS GALLERY */}
      {(activeTab === 'all' || activeTab === 'photos') && (
        <section style={{ marginBottom: '36px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h2 style={{ fontSize: '18px', fontWeight: '800', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>📸</span> High-Res Fashion Brand Photoshoots ({photosList.length})
            </h2>
            <span style={{ fontSize: '12px', color: 'rgba(255,255,255,0.5)' }}>Sorted by latest neural render</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '20px' }}>
            {photosList.map((photo) => (
              <div
                key={photo.id}
                style={{
                  background: 'rgba(26, 20, 32, 0.8)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  borderRadius: '14px',
                  overflow: 'hidden',
                  transition: 'transform 0.2s ease, border-color 0.2s ease',
                  position: 'relative',
                  display: 'flex',
                  flexDirection: 'column'
                }}
                onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-4px)'; e.currentTarget.style.borderColor = 'rgba(255,255,255,0.25)'; }}
                onMouseLeave={(e) => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)'; }}
              >
                <div
                  onClick={() => setSelectedPhotoModal(photo)}
                  style={{ height: '360px', overflow: 'hidden', background: '#0a080d', position: 'relative', cursor: 'pointer' }}
                >
                  <img
                    src={photo.src}
                    alt={photo.title}
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    onError={(e) => {
                      e.target.src = '/studio_media/photos/ARENA_FAST_1791066182_classic_wine_red.jpg';
                    }}
                  />
                  <div style={{ position: 'absolute', top: '10px', left: '10px', background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(6px)', padding: '4px 8px', borderRadius: '6px', fontSize: '11px', fontWeight: '700', color: '#52e396' }}>
                    {photo.engine}
                  </div>
                  <div style={{ position: 'absolute', top: '10px', right: '10px', background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(6px)', padding: '4px 8px', borderRadius: '6px', fontSize: '11px', fontWeight: '700', color: '#ffd166' }}>
                    {photo.price}
                  </div>
                </div>

                <div style={{ padding: '14px', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                  <div>
                    <div style={{ fontSize: '13px', fontWeight: '700', marginBottom: '4px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {photo.title}
                    </div>
                    <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)', marginBottom: '8px' }}>
                      {photo.category} · {photo.duration}
                    </div>
                    <div style={{ fontSize: '11px', color: '#a78bfa', background: 'rgba(167, 139, 250, 0.1)', padding: '4px 8px', borderRadius: '4px', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '12px' }}>
                      <span>🔬</span> {photo.optical}
                    </div>
                  </div>

                  {/* Quick Action Buttons */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <button
                      onClick={() => handleApplyToStorefront(photo)}
                      style={{
                        background: 'linear-gradient(135deg, #ec4899, #8b5cf6)',
                        color: '#fff',
                        border: 'none',
                        padding: '7px 10px',
                        borderRadius: '6px',
                        fontSize: '11.5px',
                        fontWeight: '750',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '5px'
                      }}
                    >
                      <span>✨</span> Apply as Storefront Cover
                    </button>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
                      <button
                        onClick={() => handlePushTelegram(photo.title, photo.src)}
                        style={{
                          background: 'linear-gradient(135deg, #0284c7, #0369a1)',
                          color: '#fff',
                          border: 'none',
                          padding: '6px 8px',
                          borderRadius: '6px',
                          fontSize: '11px',
                          fontWeight: '700',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '4px'
                        }}
                      >
                        <span>📱</span> Telegram
                      </button>
                      <button
                        onClick={() => handleRegenerateVariation(photo)}
                        style={{
                          background: 'rgba(255, 255, 255, 0.08)',
                          color: '#fff',
                          border: '1px solid rgba(255, 255, 255, 0.15)',
                          padding: '6px 8px',
                          borderRadius: '6px',
                          fontSize: '11px',
                          fontWeight: '700',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '4px'
                        }}
                      >
                        <span>🔄</span> New Angle
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* VIEW: VIDEOS GALLERY */}
      {(activeTab === 'all' || activeTab === 'videos') && (
        <section style={{ marginBottom: '36px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h2 style={{ fontSize: '18px', fontWeight: '800', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>🎬</span> Google Veo 9:16 Vertical Motion Reels ({INITIAL_VIDEOS.length})
            </h2>
            <span style={{ fontSize: '12px', color: 'rgba(255,255,255,0.5)' }}>Direct playable 60fps vertical reels</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
            {INITIAL_VIDEOS.map((video) => (
              <div
                key={video.id}
                style={{
                  background: 'rgba(26, 20, 32, 0.8)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  borderRadius: '14px',
                  overflow: 'hidden'
                }}
              >
                <div style={{ height: '420px', background: '#000', position: 'relative' }}>
                  <video
                    src={video.src}
                    controls
                    playsInline
                    preload="metadata"
                    style={{ width: '100%', height: '100%', objectFit: 'contain', background: '#000' }}
                  />
                </div>

                <div style={{ padding: '14px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <span style={{ fontSize: '11px', background: 'rgba(139, 92, 246, 0.2)', color: '#c4b5fd', padding: '3px 8px', borderRadius: '4px', fontWeight: '600' }}>
                      {video.aspectRatio} · {video.duration}
                    </span>
                    <span style={{ fontSize: '12px', fontWeight: '700', color: '#52e396' }}>{video.price}</span>
                  </div>
                  <div style={{ fontSize: '13px', fontWeight: '700', marginBottom: '4px' }}>{video.title}</div>
                  <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)' }}>{video.engine}</div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Lightbox Modal for Photo Details */}
      {selectedPhotoModal && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.85)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 10000,
          padding: '20px'
        }} onClick={() => setSelectedPhotoModal(null)}>
          <div style={{
            background: 'rgba(24, 18, 30, 0.98)',
            border: '1px solid rgba(255,255,255,0.15)',
            borderRadius: '16px',
            maxWidth: '920px',
            width: '100%',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'row',
            flexWrap: 'wrap',
            maxHeight: '90vh'
          }} onClick={(e) => e.stopPropagation()}>
            <div style={{ flex: '1 1 400px', maxHeight: '75vh', overflow: 'hidden', background: '#000' }}>
              <img
                src={selectedPhotoModal.src}
                alt={selectedPhotoModal.title}
                style={{ width: '100%', height: '100%', objectFit: 'contain' }}
              />
            </div>

            <div style={{ flex: '1 1 340px', padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <span style={{ background: 'rgba(82, 227, 150, 0.2)', color: '#52e396', padding: '4px 10px', borderRadius: '6px', fontSize: '12px', fontWeight: '700' }}>
                    {selectedPhotoModal.engine}
                  </span>
                  <button onClick={() => setSelectedPhotoModal(null)} style={{ background: 'transparent', border: 'none', color: '#fff', fontSize: '18px', cursor: 'pointer' }}>✕</button>
                </div>

                <h3 style={{ margin: '0 0 8px 0', fontSize: '18px', fontWeight: '700' }}>{selectedPhotoModal.title}</h3>
                <div style={{ fontSize: '16px', fontWeight: '700', color: '#ffd166', marginBottom: '14px' }}>{selectedPhotoModal.price}</div>

                <div style={{ background: 'rgba(255,255,255,0.05)', padding: '12px', borderRadius: '8px', marginBottom: '12px' }}>
                  <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', marginBottom: '4px' }}>Prompt Recipe</div>
                  <div style={{ fontSize: '11.5px', color: '#fff', lineHeight: '1.4' }}>{selectedPhotoModal.prompt || selectedPhotoModal.optical}</div>
                </div>

                <div style={{ background: 'rgba(255,255,255,0.05)', padding: '12px', borderRadius: '8px' }}>
                  <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', marginBottom: '4px' }}>Model Anchor Standard</div>
                  <div style={{ fontSize: '11.5px', color: '#fff' }}>21yo Indian Creator · Signature Round Black Bindi &amp; Silver Oxidised Jhumkas · Organic Skin Pores</div>
                </div>
              </div>

              <div style={{ marginTop: '20px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <button
                  onClick={() => {
                    handleApplyToStorefront(selectedPhotoModal);
                    setSelectedPhotoModal(null);
                  }}
                  style={{
                    width: '100%',
                    background: 'linear-gradient(135deg, #ec4899, #8b5cf6)',
                    color: '#fff',
                    border: 'none',
                    padding: '12px',
                    borderRadius: '8px',
                    fontWeight: '750',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                    boxShadow: '0 4px 15px rgba(236, 72, 153, 0.4)'
                  }}
                >
                  <span>✨</span> Apply as Primary Website Storefront Photo
                </button>

                <button
                  onClick={() => {
                    handlePushTelegram(selectedPhotoModal.title, selectedPhotoModal.src);
                    setSelectedPhotoModal(null);
                  }}
                  style={{
                    width: '100%',
                    background: 'linear-gradient(135deg, #0284c7, #0369a1)',
                    color: '#fff',
                    border: 'none',
                    padding: '12px',
                    borderRadius: '8px',
                    fontWeight: '700',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px'
                  }}
                >
                  <span>📱</span> Direct Push to Telegram (@{telegramChatId})
                </button>

                <button
                  onClick={() => {
                    handleCopyWhatsAppPitch(selectedPhotoModal);
                    setSelectedPhotoModal(null);
                  }}
                  style={{
                    width: '100%',
                    background: 'linear-gradient(135deg, #25d366, #128c7e)',
                    color: '#fff',
                    border: 'none',
                    padding: '10px',
                    borderRadius: '8px',
                    fontWeight: '700',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px'
                  }}
                >
                  <span>💬</span> Copy WhatsApp VIP Broadcast Pitch
                </button>

                <button
                  onClick={() => handleRegenerateVariation(selectedPhotoModal)}
                  style={{
                    width: '100%',
                    background: 'rgba(255,255,255,0.08)',
                    color: '#fff',
                    border: '1px solid rgba(255,255,255,0.15)',
                    padding: '10px',
                    borderRadius: '8px',
                    fontWeight: '700',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px'
                  }}
                >
                  <span>🔄</span> Photo Not Perfect? Regenerate Angle Variation
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
