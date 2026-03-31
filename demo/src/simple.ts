/**
 * Blabberer Demo — premium lip sync experience.
 *
 * Shows full scene image with mouth sprites overlaid at the face position,
 * driven by real-time audio analysis + text phoneme mapping.
 * Includes a waveform visualizer in the controls bar.
 */

import { AudioAnalyser } from './audioAnalyser';
import { LipSyncEngine, type MouthShape } from './lipSync';
import { MouthRenderer } from './mouthRenderer';

// --- DOM ---
const sceneCard = document.getElementById('scene-card') as HTMLElement;
const spriteContainer = document.getElementById('sprite-container') as HTMLElement;
const playBtn = document.getElementById('play-btn') as HTMLButtonElement;
const playIcon = document.getElementById('play-icon') as HTMLElement;
const stopIcon = document.getElementById('stop-icon') as HTMLElement;
const statusEl = document.getElementById('status') as HTMLElement;
const statusDot = document.getElementById('status-dot') as HTMLElement;
const shapeDisplay = document.getElementById('shape-display') as HTMLElement;
const timeDisplay = document.getElementById('time-display') as HTMLElement;
const waveformCanvas = document.getElementById('waveform-canvas') as HTMLCanvasElement;
const audioEl = document.getElementById('audio-player') as HTMLAudioElement;

const waveCtx = waveformCanvas.getContext('2d')!;

// --- Face region config ---
let FACE_REGION = {
  x: 0.4071,
  y: 0.1580,
  width: 0.2188,
  height: 0.3905,
};

// --- State ---
let audioAnalyser: AudioAnalyser | null = null;
let lipSyncEngine: LipSyncEngine | null = null;
let mouthRenderer: MouthRenderer | null = null;
let monitorRaf = 0;
let isPlaying = false;

const TRANSCRIPT =
  'Hello, I am demonstrating the blabberer lip sync system. Watch how my mouth moves naturally as I speak these words.';

const SHAPE_NAMES: MouthShape[] = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'X'];

// --- Waveform colors ---
const ACCENT = '#7c5cfc';
const ACCENT_DIM = 'rgba(124,92,252,0.15)';

// --- Position the sprite container over the face region ---
function positionSpriteOverlay(): void {
  spriteContainer.style.left = `${FACE_REGION.x * 100}%`;
  spriteContainer.style.top = `${FACE_REGION.y * 100}%`;
  spriteContainer.style.width = `${FACE_REGION.width * 100}%`;
  spriteContainer.style.height = `${FACE_REGION.height * 100}%`;
}

// --- Resize waveform canvas for crisp rendering ---
function resizeWaveform(): void {
  const rect = waveformCanvas.getBoundingClientRect();
  waveformCanvas.width = rect.width * devicePixelRatio;
  waveformCanvas.height = rect.height * devicePixelRatio;
}

// --- Draw waveform visualization ---
function drawWaveform(analyser: AnalyserNode, dataArray: Uint8Array): void {
  analyser.getByteFrequencyData(dataArray);

  const w = waveformCanvas.width;
  const h = waveformCanvas.height;
  const barCount = 48;
  const gap = 2 * devicePixelRatio;
  const barWidth = (w - gap * (barCount - 1)) / barCount;
  const maxBarHeight = h * 0.85;
  const radius = Math.min(barWidth / 2, 3 * devicePixelRatio);

  waveCtx.clearRect(0, 0, w, h);

  const step = Math.floor(dataArray.length / barCount);

  for (let i = 0; i < barCount; i++) {
    // Average a few bins per bar for smoother visualization
    let sum = 0;
    for (let j = 0; j < step; j++) {
      sum += dataArray[i * step + j];
    }
    const val = sum / step / 255;
    const barH = Math.max(3 * devicePixelRatio, val * maxBarHeight);
    const x = i * (barWidth + gap);
    const y = (h - barH) / 2;

    // Gradient bar color based on intensity
    const alpha = 0.3 + val * 0.7;
    waveCtx.fillStyle = `rgba(124,92,252,${alpha})`;

    // Rounded rect
    waveCtx.beginPath();
    waveCtx.roundRect(x, y, barWidth, barH, radius);
    waveCtx.fill();
  }
}

// --- Draw idle waveform (static bars) ---
function drawIdleWaveform(): void {
  const w = waveformCanvas.width;
  const h = waveformCanvas.height;
  const barCount = 48;
  const gap = 2 * devicePixelRatio;
  const barWidth = (w - gap * (barCount - 1)) / barCount;
  const radius = Math.min(barWidth / 2, 3 * devicePixelRatio);

  waveCtx.clearRect(0, 0, w, h);

  for (let i = 0; i < barCount; i++) {
    const barH = 3 * devicePixelRatio;
    const x = i * (barWidth + gap);
    const y = (h - barH) / 2;
    waveCtx.fillStyle = ACCENT_DIM;
    waveCtx.beginPath();
    waveCtx.roundRect(x, y, barWidth, barH, radius);
    waveCtx.fill();
  }
}

// --- Format time ---
function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

// --- Status helpers ---
function setStatus(text: string, state: 'idle' | 'ready' | 'playing' | 'error' = 'idle'): void {
  statusEl.textContent = text;
  statusDot.className = 'status-dot';
  if (state !== 'idle') statusDot.classList.add(state);
}

// --- Sprite loading ---
const SPRITE_PATHS = [
  (name: string) => `./sample/soft/shape_${name}.webp`,
  (name: string) => `./sample/shape_${name}.webp`,
  (name: string) => `./sample/shape_${name}.png`,
];

function tryLoadImage(urls: string[]): Promise<string | null> {
  return new Promise(resolve => {
    function attempt(i: number) {
      if (i >= urls.length) { resolve(null); return; }
      const img = new Image();
      img.onload = () => resolve(urls[i]);
      img.onerror = () => attempt(i + 1);
      img.src = urls[i];
    }
    attempt(0);
  });
}

async function loadSprites(): Promise<void> {
  const sprites: Record<string, string> = {};

  const promises = SHAPE_NAMES.map(async (name) => {
    const urls = SPRITE_PATHS.map(fn => fn(name));
    const found = await tryLoadImage(urls);
    if (found) sprites[name] = found;
  });

  await Promise.all(promises);

  const count = Object.keys(sprites).length;
  if (count > 0) {
    positionSpriteOverlay();
    mouthRenderer = new MouthRenderer(spriteContainer);
    mouthRenderer.loadSprites(sprites);
    playBtn.disabled = false;
    setStatus(`Ready - ${count} shapes loaded`, 'ready');
  } else {
    setStatus('No sprites found. Generate with: blabberer generate <image>', 'error');
  }
}

// --- Playback ---
function startPlayback(): void {
  if (!mouthRenderer) return;

  if (!audioAnalyser) {
    audioAnalyser = new AudioAnalyser();
  }
  const analyserNode = audioAnalyser.connect(audioEl);
  if (!analyserNode) {
    setStatus('Failed to connect audio analyser', 'error');
    return;
  }

  lipSyncEngine = new LipSyncEngine(analyserNode);
  lipSyncEngine.loadText(TRANSCRIPT);
  mouthRenderer.startLoop(lipSyncEngine);

  audioEl.play().catch(err => {
    setStatus(`Playback failed: ${err.message}`, 'error');
  });

  startMonitor(analyserNode);

  isPlaying = true;
  playIcon.style.display = 'none';
  stopIcon.style.display = 'block';
  sceneCard.classList.add('playing');
  setStatus('Speaking...', 'playing');
}

function stopPlayback(): void {
  audioEl.pause();
  audioEl.currentTime = 0;

  if (mouthRenderer) mouthRenderer.stopLoop();
  if (lipSyncEngine) lipSyncEngine.stop();
  stopMonitor();

  isPlaying = false;
  playIcon.style.display = 'block';
  stopIcon.style.display = 'none';
  sceneCard.classList.remove('playing');
  shapeDisplay.textContent = 'X';
  shapeDisplay.classList.remove('active');
  timeDisplay.textContent = '0:00';
  drawIdleWaveform();
  setStatus('Ready', 'ready');
}

// --- Monitor loop ---
function startMonitor(analyser: AnalyserNode): void {
  const dataArray = new Uint8Array(analyser.frequencyBinCount);

  const monitor = () => {
    monitorRaf = requestAnimationFrame(monitor);
    if (!lipSyncEngine) return;

    const shape = lipSyncEngine.currentShape;
    shapeDisplay.textContent = shape;

    if (shape !== 'X') {
      shapeDisplay.classList.add('active');
    } else {
      shapeDisplay.classList.remove('active');
    }

    // Update waveform
    drawWaveform(analyser, dataArray);

    // Update time
    timeDisplay.textContent = formatTime(audioEl.currentTime);
  };
  monitorRaf = requestAnimationFrame(monitor);
}

function stopMonitor(): void {
  if (monitorRaf) {
    cancelAnimationFrame(monitorRaf);
    monitorRaf = 0;
  }
}

// --- Events ---
playBtn.addEventListener('click', () => {
  if (isPlaying) {
    stopPlayback();
  } else {
    startPlayback();
  }
});

audioEl.addEventListener('ended', () => {
  stopPlayback();
  setStatus('Finished', 'ready');
});

window.addEventListener('resize', () => {
  positionSpriteOverlay();
  resizeWaveform();
  if (!isPlaying) drawIdleWaveform();
});

// --- Init ---
async function init() {
  setStatus('Loading...', 'idle');
  playBtn.disabled = true;

  resizeWaveform();
  drawIdleWaveform();

  // Load face region config
  try {
    const resp = await fetch('./sample/blabberer_config.json');
    if (resp.ok) {
      const config = await resp.json();
      if (config?.face_region) {
        FACE_REGION = config.face_region;
      }
    }
  } catch { /* use defaults */ }

  await loadSprites();
}

init();
