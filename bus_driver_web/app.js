/**
 * Bus Driver • NH 48 Interactive Web Experience
 * Core Engine: Canvas Rain, Web Audio Synthesizer (Horn, Engine, Rain), and Music Player.
 */

// ─── PLAYLIST DATABASE ──────────────────────────────────────────
const PLAYLIST = [
  {
    title: "Tumhein Dekhen Meri Aankhen",
    artist: "Kumar Sanu, Alka Yagnik • LoFi Rework",
    duration: 214,
    color: "#f59e0b",
    icon: "🚌"
  },
  {
    title: "Tere Liye (Slowed + Reverb)",
    artist: "Atif Aslam, Shreya Ghoshal • DK LOFI",
    duration: 270,
    color: "#ec4899",
    icon: "🌙"
  },
  {
    title: "Chura Ke Dil Mera (Midnight Drive)",
    artist: "Kumar Sanu • 90s Highway Tape",
    duration: 245,
    color: "#06b6d4",
    icon: "⭐"
  },
  {
    title: "Aankhon Mein Teri (Nostalgic Rain Mix)",
    artist: "KK • Monsoon Road Trip",
    duration: 258,
    color: "#10b981",
    icon: "🌧️"
  },
  {
    title: "Bairan Banjaare (Rural Junction)",
    artist: "Midnight Folk • LoFi Fusion",
    duration: 198,
    color: "#8b5cf6",
    icon: "🪔"
  }
];

let currentTrackIndex = 0;
let isPlaying = false;
let trackCurrentTime = 0;
let trackTimer = null;

// ─── WEB AUDIO API SYNTHESIZER ──────────────────────────────────
let audioCtx = null;
let engineGain = null;
let rainGain = null;
let isEngineSoundOn = true;
let isRainSoundOn = true;

function initAudioContext() {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    setupEngineRumble();
    setupRainNoise();
  }
  if (audioCtx.state === 'suspended') {
    audioCtx.resume();
  }
}

// 1. Synthesize Desi Bus Horn ("PO PO PO" Dual Horn)
function playDesiHorn() {
  initAudioContext();
  const now = audioCtx.currentTime;

  // Visual shake effect on the bus
  const bus = document.getElementById('busChassis');
  bus.classList.add('honking');
  setTimeout(() => bus.classList.remove('honking'), 650);

  // Two harmonic horn tones (430Hz + 540Hz)
  const osc1 = audioCtx.createOscillator();
  const osc2 = audioCtx.createOscillator();
  const hornGain = audioCtx.createGain();

  osc1.type = 'sawtooth';
  osc1.frequency.setValueAtTime(430, now);
  // Horn wobble/vibrato
  osc1.frequency.exponentialRampToValueAtTime(445, now + 0.3);

  osc2.type = 'triangle';
  osc2.frequency.setValueAtTime(542, now);
  osc2.frequency.exponentialRampToValueAtTime(555, now + 0.3);

  hornGain.gain.setValueAtTime(0, now);
  hornGain.gain.linearRampToValueAtTime(0.4, now + 0.05);
  hornGain.gain.setValueAtTime(0.35, now + 0.4);
  hornGain.gain.exponentialRampToValueAtTime(0.001, now + 0.65);

  osc1.connect(hornGain);
  osc2.connect(hornGain);
  hornGain.connect(audioCtx.destination);

  osc1.start(now);
  osc2.start(now);
  osc1.stop(now + 0.7);
  osc2.stop(now + 0.7);
}

// 2. Synthesize Deep Bus Engine Rumble (Low frequency brown noise oscillator)
function setupEngineRumble() {
  const bufferSize = audioCtx.sampleRate * 2;
  const buffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
  const data = buffer.getChannelData(0);
  let lastOut = 0.0;

  for (let i = 0; i < bufferSize; i++) {
    const white = Math.random() * 2 - 1;
    data[i] = (lastOut + (0.04 * white)) / 1.04;
    lastOut = data[i];
    data[i] *= 3.5;
  }

  const noise = audioCtx.createBufferSource();
  noise.buffer = buffer;
  noise.loop = true;

  const lowpass = audioCtx.createBiquadFilter();
  lowpass.type = 'lowpass';
  lowpass.frequency.value = 110; // Low chug-chug idle/cruise frequency

  engineGain = audioCtx.createGain();
  engineGain.gain.value = isEngineSoundOn ? 0.25 : 0;

  noise.connect(lowpass);
  lowpass.connect(engineGain);
  engineGain.connect(audioCtx.destination);
  noise.start();
}

// 3. Synthesize Rain Ambience Noise
function setupRainNoise() {
  const bufferSize = audioCtx.sampleRate * 2;
  const buffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
  const data = buffer.getChannelData(0);

  for (let i = 0; i < bufferSize; i++) {
    data[i] = Math.random() * 2 - 1;
  }

  const noise = audioCtx.createBufferSource();
  noise.buffer = buffer;
  noise.loop = true;

  const bandpass = audioCtx.createBiquadFilter();
  bandpass.type = 'bandpass';
  bandpass.frequency.value = 1200;
  bandpass.Q.value = 0.6;

  rainGain = audioCtx.createGain();
  rainGain.gain.value = isRainSoundOn ? 0.08 : 0;

  noise.connect(bandpass);
  bandpass.connect(rainGain);
  rainGain.connect(audioCtx.destination);
  noise.start();
}

// ─── REALISTIC CANVAS RAIN ANIMATION ────────────────────────────
const canvas = document.getElementById('rainCanvas');
const ctx = canvas.getContext('2d');
let drops = [];
const DROP_COUNT = 180;

function resizeCanvas() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}
window.addEventListener('resize', resizeCanvas);
resizeCanvas();

class RainDrop {
  constructor() {
    this.reset(true);
  }

  reset(initial = false) {
    this.x = Math.random() * (canvas.width + 200);
    this.y = initial ? Math.random() * canvas.height : -30;
    this.length = Math.random() * 28 + 15;
    this.speed = Math.random() * 12 + 18;
    this.wind = -4.5; // Wind angle from right to left (highway speed)
    this.opacity = Math.random() * 0.45 + 0.2;
    this.width = Math.random() * 1.5 + 0.8;
  }

  update() {
    this.x += this.wind;
    this.y += this.speed;

    if (this.y > canvas.height + 20 || this.x < -40) {
      this.reset();
    }
  }

  draw() {
    ctx.beginPath();
    ctx.strokeStyle = `rgba(186, 230, 253, ${this.opacity})`;
    ctx.lineWidth = this.width;
    ctx.moveTo(this.x, this.y);
    ctx.lineTo(this.x + this.wind * 2, this.y + this.length);
    ctx.stroke();
  }
}

for (let i = 0; i < DROP_COUNT; i++) {
  drops.push(new RainDrop());
}

function renderRain() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  drops.forEach(drop => {
    drop.update();
    drop.draw();
  });
  requestAnimationFrame(renderRain);
}
renderRain();

// ─── PLAYER LOGIC & UI ──────────────────────────────────────────
const trackTitleEl = document.getElementById('trackTitle');
const trackArtistEl = document.getElementById('trackArtist');
const trackThumbEl = document.getElementById('trackThumb');
const playPauseBtn = document.getElementById('playPauseBtn');
const playIcon = document.getElementById('playIcon');
const pauseIcon = document.getElementById('pauseIcon');
const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');
const currentTimeEl = document.getElementById('currentTime');
const durationTimeEl = document.getElementById('durationTime');
const progressFill = document.getElementById('progressFill');
const progressBarBg = document.getElementById('progressBarBg');
const engineSoundBtn = document.getElementById('engineSoundBtn');
const rainSoundBtn = document.getElementById('rainSoundBtn');
const volumeSlider = document.getElementById('volumeSlider');
const hornBtnTop = document.getElementById('hornBtnTop');

function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
}

function loadTrack(index) {
  const track = PLAYLIST[index];
  trackTitleEl.textContent = track.title;
  trackArtistEl.textContent = track.artist;
  trackThumbEl.style.background = `linear-gradient(135deg, ${track.color}, #dc2626)`;
  durationTimeEl.textContent = formatTime(track.duration);
  trackCurrentTime = 0;
  updateProgressUI();
}

function updateProgressUI() {
  const track = PLAYLIST[currentTrackIndex];
  currentTimeEl.textContent = formatTime(trackCurrentTime);
  const percent = (trackCurrentTime / track.duration) * 100;
  progressFill.style.width = `${percent}%`;
}

function togglePlay() {
  initAudioContext();
  isPlaying = !isPlaying;

  if (isPlaying) {
    playIcon.classList.add('hidden');
    pauseIcon.classList.remove('hidden');
    trackTimer = setInterval(() => {
      trackCurrentTime++;
      if (trackCurrentTime >= PLAYLIST[currentTrackIndex].duration) {
        nextTrack();
      } else {
        updateProgressUI();
      }
    }, 1000);
  } else {
    playIcon.classList.remove('hidden');
    pauseIcon.classList.add('hidden');
    clearInterval(trackTimer);
  }
}

function nextTrack() {
  currentTrackIndex = (currentTrackIndex + 1) % PLAYLIST.length;
  loadTrack(currentTrackIndex);
  if (isPlaying) {
    clearInterval(trackTimer);
    trackTimer = setInterval(() => {
      trackCurrentTime++;
      if (trackCurrentTime >= PLAYLIST[currentTrackIndex].duration) {
        nextTrack();
      } else {
        updateProgressUI();
      }
    }, 1000);
  }
}

function prevTrack() {
  currentTrackIndex = (currentTrackIndex - 1 + PLAYLIST.length) % PLAYLIST.length;
  loadTrack(currentTrackIndex);
}

// Click on progress bar to seek
progressBarBg.addEventListener('click', (e) => {
  const rect = progressBarBg.getBoundingClientRect();
  const clickX = e.clientX - rect.left;
  const ratio = Math.max(0, Math.min(1, clickX / rect.width));
  trackCurrentTime = Math.floor(ratio * PLAYLIST[currentTrackIndex].duration);
  updateProgressUI();
});

// Event Listeners
playPauseBtn.addEventListener('click', togglePlay);
nextBtn.addEventListener('click', nextTrack);
prevBtn.addEventListener('click', prevTrack);
hornBtnTop.addEventListener('click', playDesiHorn);

// Engine toggle
engineSoundBtn.addEventListener('click', () => {
  initAudioContext();
  isEngineSoundOn = !isEngineSoundOn;
  engineGain.gain.setValueAtTime(isEngineSoundOn ? 0.25 : 0, audioCtx.currentTime);
  engineSoundBtn.classList.toggle('active', isEngineSoundOn);
});

// Rain sound toggle
rainSoundBtn.addEventListener('click', () => {
  initAudioContext();
  isRainSoundOn = !isRainSoundOn;
  rainGain.gain.setValueAtTime(isRainSoundOn ? 0.08 : 0, audioCtx.currentTime);
  rainSoundBtn.classList.toggle('active', isRainSoundOn);
});

// Real-time Clock
function updateClock() {
  const now = new Date();
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  document.getElementById('clockDisplay').textContent = `${hours}:${minutes}`;
}
setInterval(updateClock, 1000);
updateClock();

// Natural Passenger Fluctuation
const passengerEl = document.getElementById('passengerCount');
let passengers = 107;
setInterval(() => {
  const delta = Math.floor(Math.random() * 5) - 2; // -2 to +2
  passengers = Math.max(85, Math.min(135, passengers + delta));
  passengerEl.textContent = passengers;
}, 8000);

// Keyboard Shortcuts
window.addEventListener('keydown', (e) => {
  if (e.target.tagName === 'INPUT') return;

  switch (e.code) {
    case 'Space':
      e.preventDefault();
      togglePlay();
      break;
    case 'KeyH':
      playDesiHorn();
      break;
    case 'KeyN':
      nextTrack();
      break;
    case 'KeyP':
      prevTrack();
      break;
    case 'KeyM':
      if (volumeSlider.value > 0) {
        volumeSlider.dataset.prev = volumeSlider.value;
        volumeSlider.value = 0;
      } else {
        volumeSlider.value = volumeSlider.dataset.prev || 0.8;
      }
      break;
    case 'KeyR':
      rainSoundBtn.click();
      break;
    case 'ArrowRight':
      trackCurrentTime = Math.min(PLAYLIST[currentTrackIndex].duration, trackCurrentTime + 10);
      updateProgressUI();
      break;
    case 'ArrowLeft':
      trackCurrentTime = Math.max(0, trackCurrentTime - 10);
      updateProgressUI();
      break;
  }
});

// Initialize first track
loadTrack(currentTrackIndex);
console.log("🚌 Bus Driver Web App Initialized Successfully.");
