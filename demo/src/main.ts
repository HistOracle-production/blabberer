/**
 * Blabberer Demo — Interactive lip sync sprite player.
 *
 * Load mouth shape sprites + an audio file + optional transcript text
 * to see real-time lip sync animation in the browser.
 */

import { AudioAnalyser } from './audioAnalyser';
import { LipSyncEngine, type MouthShape } from './lipSync';
import { MouthRenderer } from './mouthRenderer';

// --- DOM Elements ---
const spriteInput = document.getElementById('sprite-input') as HTMLInputElement;
const audioInput = document.getElementById('audio-input') as HTMLInputElement;
const transcriptInput = document.getElementById('transcript-input') as HTMLTextAreaElement;
const playBtn = document.getElementById('play-btn') as HTMLButtonElement;
const stopBtn = document.getElementById('stop-btn') as HTMLButtonElement;
const statusEl = document.getElementById('status') as HTMLElement;
const shapeDisplay = document.getElementById('shape-display') as HTMLElement;
const energyBar = document.getElementById('energy-bar') as HTMLElement;
const spriteContainer = document.getElementById('sprite-container') as HTMLElement;
const audioEl = document.getElementById('audio-player') as HTMLAudioElement;
const sampleBtn = document.getElementById('sample-btn') as HTMLButtonElement;
const dropZone = document.getElementById('drop-zone') as HTMLElement;

// --- State ---
let audioAnalyser: AudioAnalyser | null = null;
let lipSyncEngine: LipSyncEngine | null = null;
let mouthRenderer: MouthRenderer | null = null;
let sprites: Record<string, string> = {};
let hasAudio = false;
let hasSprites = false;
let monitorRaf = 0;

const SHAPE_NAMES = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'X'];

// --- Sprite loading ---
function loadSpritesFromFiles(files: FileList): void {
  sprites = {};
  let loaded = 0;
  const total = Array.from(files).filter(f =>
    f.name.match(/shape_[A-HX]\.(webp|png|jpg)$/i)
  ).length;

  if (total === 0) {
    setStatus('No valid sprite files found. Expected: shape_A.webp, shape_B.webp, ..., shape_X.webp');
    return;
  }

  for (const file of files) {
    const match = file.name.match(/shape_([A-HX])\.(webp|png|jpg)$/i);
    if (!match) continue;

    const shapeName = match[1].toUpperCase();
    const url = URL.createObjectURL(file);
    sprites[shapeName] = url;
    loaded++;

    if (loaded === total) {
      hasSprites = true;
      initRenderer();
      setStatus(`Loaded ${total} sprites. ${hasAudio ? 'Ready to play!' : 'Now load an audio file.'}`);
      updatePlayButton();
    }
  }
}

function loadSpritesFromPath(basePath: string): void {
  sprites = {};
  let loaded = 0;

  for (const name of SHAPE_NAMES) {
    const url = `${basePath}/shape_${name}.webp`;
    const img = new Image();
    img.onload = () => {
      sprites[name] = url;
      loaded++;
      if (loaded === SHAPE_NAMES.length) {
        hasSprites = true;
        initRenderer();
        setStatus(`Loaded ${SHAPE_NAMES.length} sample sprites. ${hasAudio ? 'Ready to play!' : 'Now load an audio file.'}`);
        updatePlayButton();
      }
    };
    img.onerror = () => {
      loaded++;
      console.warn(`Failed to load: ${url}`);
    };
    img.src = url;
  }
}

// --- Audio loading ---
function loadAudioFile(file: File): void {
  const url = URL.createObjectURL(file);
  audioEl.src = url;
  hasAudio = true;
  setStatus(`Audio loaded: ${file.name}. ${hasSprites ? 'Ready to play!' : 'Now load sprite files.'}`);
  updatePlayButton();
}

function loadAudioFromPath(path: string): void {
  audioEl.src = path;
  hasAudio = true;
  setStatus(`Sample audio loaded. ${hasSprites ? 'Ready to play!' : 'Now load sprite files.'}`);
  updatePlayButton();
}

// --- Renderer ---
function initRenderer(): void {
  if (mouthRenderer) {
    mouthRenderer.destroy();
  }
  mouthRenderer = new MouthRenderer(spriteContainer);
  mouthRenderer.loadSprites(sprites);
}

// --- Playback ---
function startPlayback(): void {
  if (!hasSprites || !hasAudio) return;

  // Connect audio analyser
  if (!audioAnalyser) {
    audioAnalyser = new AudioAnalyser();
  }
  const analyserNode = audioAnalyser.connect(audioEl);
  if (!analyserNode) {
    setStatus('Failed to connect audio analyser');
    return;
  }

  // Create lip sync engine
  lipSyncEngine = new LipSyncEngine(analyserNode);

  // Load transcript if provided
  const transcript = transcriptInput.value.trim();
  if (transcript) {
    lipSyncEngine.loadText(transcript);
  } else {
    // Without transcript, use a generic repeating pattern
    lipSyncEngine.loadText('the quick brown fox jumps over the lazy dog');
  }

  // Start rendering
  if (mouthRenderer && lipSyncEngine) {
    mouthRenderer.startLoop(lipSyncEngine);
  }

  // Start audio
  audioEl.play().catch(err => {
    setStatus(`Playback failed: ${err.message}. Click play again.`);
  });

  // Start monitoring
  startMonitor(analyserNode);

  setStatus('Playing...');
  playBtn.style.display = 'none';
  stopBtn.style.display = 'inline-flex';
}

function stopPlayback(): void {
  audioEl.pause();
  audioEl.currentTime = 0;

  if (mouthRenderer) mouthRenderer.stopLoop();
  if (lipSyncEngine) lipSyncEngine.stop();

  stopMonitor();

  setStatus('Stopped. Press play to start again.');
  playBtn.style.display = 'inline-flex';
  stopBtn.style.display = 'none';
  shapeDisplay.textContent = 'X';
  energyBar.style.width = '0%';
}

// --- Monitor (shape + energy display) ---
function startMonitor(analyser: AnalyserNode): void {
  const dataArray = new Uint8Array(analyser.frequencyBinCount);

  const monitor = () => {
    monitorRaf = requestAnimationFrame(monitor);

    if (lipSyncEngine) {
      shapeDisplay.textContent = lipSyncEngine.currentShape;

      // Show energy
      analyser.getByteFrequencyData(dataArray);
      let sum = 0;
      const end = Math.min(30, dataArray.length);
      for (let i = 1; i < end; i++) sum += dataArray[i];
      const energy = sum / (end - 1) / 255;
      energyBar.style.width = `${Math.min(100, energy * 300)}%`;
    }
  };

  monitorRaf = requestAnimationFrame(monitor);
}

function stopMonitor(): void {
  if (monitorRaf) {
    cancelAnimationFrame(monitorRaf);
    monitorRaf = 0;
  }
}

// --- Audio ended ---
audioEl.addEventListener('ended', () => {
  stopPlayback();
  setStatus('Playback finished.');
});

// --- UI helpers ---
function setStatus(msg: string): void {
  statusEl.textContent = msg;
}

function updatePlayButton(): void {
  playBtn.disabled = !(hasSprites && hasAudio);
}

// --- Event handlers ---
spriteInput.addEventListener('change', (e) => {
  const files = (e.target as HTMLInputElement).files;
  if (files && files.length > 0) {
    loadSpritesFromFiles(files);
  }
});

audioInput.addEventListener('change', (e) => {
  const files = (e.target as HTMLInputElement).files;
  if (files && files.length > 0) {
    loadAudioFile(files[0]);
  }
});

playBtn.addEventListener('click', startPlayback);
stopBtn.addEventListener('click', stopPlayback);

// Transcript changes during playback
transcriptInput.addEventListener('input', () => {
  if (lipSyncEngine && lipSyncEngine.isPlaying) {
    const text = transcriptInput.value.trim();
    if (text) lipSyncEngine.loadText(text);
  }
});

// Sample button
sampleBtn.addEventListener('click', () => {
  loadSpritesFromPath('./sample');
  loadAudioFromPath('./sample/sample.mp3');
  transcriptInput.value = 'Hello, I am demonstrating the blabberer lip sync system. Watch how my mouth moves naturally as I speak these words.';
  setStatus('Loading sample assets...');
});

// Drag and drop
dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => {
  dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  const files = e.dataTransfer?.files;
  if (!files) return;

  const audioFiles: File[] = [];
  const spriteFiles: File[] = [];

  for (const file of files) {
    if (file.type.startsWith('audio/') || file.name.endsWith('.mp3') || file.name.endsWith('.wav')) {
      audioFiles.push(file);
    } else if (file.name.match(/shape_[A-HX]\.(webp|png|jpg)$/i)) {
      spriteFiles.push(file);
    }
  }

  if (spriteFiles.length > 0) {
    const dt = new DataTransfer();
    spriteFiles.forEach(f => dt.items.add(f));
    loadSpritesFromFiles(dt.files);
  }

  if (audioFiles.length > 0) {
    loadAudioFile(audioFiles[0]);
  }
});

// Init
setStatus('Load sprite images and an audio file to get started, or click "Use Sample" for a demo.');
updatePlayButton();
