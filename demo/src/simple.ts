/**
 * Simple lip sync demo — renders a face image with a canvas-drawn
 * animated mouth overlay driven by audio analysis.
 */

import { AudioAnalyser } from './audioAnalyser';
import { LipSyncEngine, type MouthShape } from './lipSync';

// --- DOM ---
const portrait = document.getElementById('portrait') as HTMLImageElement;
const canvas = document.getElementById('mouth-canvas') as HTMLCanvasElement;
const ctx = canvas.getContext('2d')!;
const playBtn = document.getElementById('play-btn') as HTMLButtonElement;
const stopBtn = document.getElementById('stop-btn') as HTMLButtonElement;
const statusEl = document.getElementById('status') as HTMLElement;
const shapeDisplay = document.getElementById('shape-display') as HTMLElement;
const energyBar = document.getElementById('energy-bar') as HTMLElement;
const audioEl = document.getElementById('audio-player') as HTMLAudioElement;

// --- State ---
let audioAnalyser: AudioAnalyser | null = null;
let lipSyncEngine: LipSyncEngine | null = null;
let rafId = 0;

// Default transcript — replace with actual transcript for better results
const TRANSCRIPT =
  'Hello, I am demonstrating the blabber lip sync system. Watch how my mouth moves naturally as I speak these words.';

// --- Mouth position config (fraction of image dimensions) ---
// Adjust these to position the mouth overlay on your face image
const MOUTH_CENTER_X = 0.50; // horizontal center of mouth
const MOUTH_CENTER_Y = 0.62; // vertical position of mouth
const MOUTH_WIDTH = 0.18;    // mouth width as fraction of image width
const MOUTH_HEIGHT = 0.08;   // mouth height as fraction of image height

// --- Resize canvas to match image ---
function resizeCanvas(): void {
  const rect = portrait.getBoundingClientRect();
  canvas.width = rect.width * devicePixelRatio;
  canvas.height = rect.height * devicePixelRatio;
  ctx.scale(devicePixelRatio, devicePixelRatio);
}

portrait.addEventListener('load', resizeCanvas);
window.addEventListener('resize', resizeCanvas);

// --- Draw mouth shape on canvas ---
function drawMouth(shape: MouthShape, energy: number): void {
  const w = canvas.width / devicePixelRatio;
  const h = canvas.height / devicePixelRatio;

  ctx.clearRect(0, 0, w, h);

  if (shape === 'X') return; // rest — no overlay

  const cx = w * MOUTH_CENTER_X;
  const cy = h * MOUTH_CENTER_Y;
  const mw = w * MOUTH_WIDTH;
  const mh = h * MOUTH_HEIGHT;

  // Scale openness by energy
  const openness = Math.min(1, energy * 2.5);

  ctx.save();
  ctx.globalAlpha = 0.7;

  switch (shape) {
    case 'A': // M,B,P — closed lips
      drawClosedMouth(cx, cy, mw);
      break;
    case 'B': // consonants — slight part
      drawPartedMouth(cx, cy, mw, mh * 0.25 * openness);
      break;
    case 'C': // A,I — open vowel
      drawOpenMouth(cx, cy, mw * 0.85, mh * 0.8 * Math.max(0.4, openness));
      break;
    case 'D': // E — wide stretch
      drawWideMouth(cx, cy, mw * 1.1, mh * 0.5 * Math.max(0.3, openness));
      break;
    case 'E': // O — round
      drawRoundMouth(cx, cy, mw * 0.5, mh * 0.7 * Math.max(0.4, openness));
      break;
    case 'F': // U,W,Q — pucker
      drawRoundMouth(cx, cy, mw * 0.35, mh * 0.5 * Math.max(0.3, openness));
      break;
    case 'G': // F,V — teeth on lip
      drawTeethMouth(cx, cy, mw * 0.8, mh * 0.4);
      break;
    case 'H': // L — tongue
      drawOpenMouth(cx, cy, mw * 0.7, mh * 0.6 * Math.max(0.4, openness), true);
      break;
  }

  ctx.restore();
}

function drawClosedMouth(cx: number, cy: number, w: number): void {
  ctx.beginPath();
  ctx.moveTo(cx - w / 2, cy);
  ctx.quadraticCurveTo(cx, cy - 2, cx + w / 2, cy);
  ctx.strokeStyle = '#1a0a0a';
  ctx.lineWidth = 2.5;
  ctx.stroke();
}

function drawPartedMouth(cx: number, cy: number, w: number, openH: number): void {
  const halfW = w / 2;
  ctx.beginPath();
  // Upper lip
  ctx.moveTo(cx - halfW, cy);
  ctx.quadraticCurveTo(cx, cy - openH * 0.5, cx + halfW, cy);
  // Lower lip
  ctx.quadraticCurveTo(cx, cy + openH * 1.5, cx - halfW, cy);
  ctx.fillStyle = '#2a0808';
  ctx.fill();
  ctx.strokeStyle = '#1a0505';
  ctx.lineWidth = 1.5;
  ctx.stroke();
}

function drawOpenMouth(cx: number, cy: number, w: number, openH: number, tongue = false): void {
  const halfW = w / 2;
  ctx.beginPath();
  ctx.ellipse(cx, cy, halfW, openH / 2, 0, 0, Math.PI * 2);
  ctx.fillStyle = '#1a0505';
  ctx.fill();

  if (tongue) {
    ctx.beginPath();
    ctx.ellipse(cx, cy + openH * 0.2, halfW * 0.5, openH * 0.2, 0, 0, Math.PI);
    ctx.fillStyle = '#cc4444';
    ctx.fill();
  }

  // Teeth hint
  ctx.beginPath();
  ctx.rect(cx - halfW * 0.6, cy - openH / 2, halfW * 1.2, openH * 0.15);
  ctx.fillStyle = 'rgba(255,255,255,0.3)';
  ctx.fill();
}

function drawWideMouth(cx: number, cy: number, w: number, openH: number): void {
  const halfW = w / 2;
  ctx.beginPath();
  // Wider ellipse
  ctx.ellipse(cx, cy, halfW, openH / 2, 0, 0, Math.PI * 2);
  ctx.fillStyle = '#1a0505';
  ctx.fill();

  // Teeth
  ctx.beginPath();
  ctx.rect(cx - halfW * 0.7, cy - openH / 2, halfW * 1.4, openH * 0.12);
  ctx.fillStyle = 'rgba(255,255,255,0.3)';
  ctx.fill();
}

function drawRoundMouth(cx: number, cy: number, rw: number, rh: number): void {
  ctx.beginPath();
  ctx.ellipse(cx, cy, rw, rh / 2, 0, 0, Math.PI * 2);
  ctx.fillStyle = '#1a0505';
  ctx.fill();
  ctx.strokeStyle = '#330808';
  ctx.lineWidth = 1.5;
  ctx.stroke();
}

function drawTeethMouth(cx: number, cy: number, w: number, openH: number): void {
  const halfW = w / 2;
  ctx.beginPath();
  ctx.ellipse(cx, cy, halfW, openH / 2, 0, 0, Math.PI * 2);
  ctx.fillStyle = '#1a0505';
  ctx.fill();

  // Upper teeth prominent
  ctx.beginPath();
  ctx.rect(cx - halfW * 0.6, cy - openH / 2, halfW * 1.2, openH * 0.25);
  ctx.fillStyle = 'rgba(255,255,255,0.45)';
  ctx.fill();
}

// --- Playback ---
function startPlayback(): void {
  resizeCanvas();

  if (!audioAnalyser) {
    audioAnalyser = new AudioAnalyser();
  }
  const analyserNode = audioAnalyser.connect(audioEl);
  if (!analyserNode) {
    statusEl.textContent = 'Failed to connect audio analyser';
    return;
  }

  lipSyncEngine = new LipSyncEngine(analyserNode);
  lipSyncEngine.loadText(TRANSCRIPT);

  const dataArray = new Uint8Array(analyserNode.frequencyBinCount);

  const animate = () => {
    rafId = requestAnimationFrame(animate);
    if (!lipSyncEngine) return;

    const shape = lipSyncEngine.update(performance.now());

    // Compute energy for mouth openness
    analyserNode.getByteFrequencyData(dataArray);
    let sum = 0;
    const end = Math.min(30, dataArray.length);
    for (let i = 1; i < end; i++) sum += dataArray[i];
    const energy = sum / (end - 1) / 255;

    drawMouth(shape, energy);
    shapeDisplay.textContent = shape;
    energyBar.style.width = `${Math.min(100, energy * 300)}%`;
  };

  audioEl.play().catch(err => {
    statusEl.textContent = `Playback failed: ${err.message}`;
  });

  rafId = requestAnimationFrame(animate);
  statusEl.textContent = 'Playing...';
  playBtn.style.display = 'none';
  stopBtn.style.display = 'inline-flex';
}

function stopPlayback(): void {
  audioEl.pause();
  audioEl.currentTime = 0;

  if (rafId) {
    cancelAnimationFrame(rafId);
    rafId = 0;
  }

  if (lipSyncEngine) lipSyncEngine.stop();

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  shapeDisplay.textContent = 'X';
  energyBar.style.width = '0%';
  statusEl.textContent = 'Stopped. Click Play to restart.';
  playBtn.style.display = 'inline-flex';
  stopBtn.style.display = 'none';
}

// --- Events ---
playBtn.addEventListener('click', startPlayback);
stopBtn.addEventListener('click', stopPlayback);
audioEl.addEventListener('ended', () => {
  stopPlayback();
  statusEl.textContent = 'Playback finished.';
});
