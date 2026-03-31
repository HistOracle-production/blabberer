/**
 * Hybrid audio-rhythm + text-shape lip sync engine.
 *
 * AUDIO drives the rhythm — amplitude controls how open the mouth is.
 * TEXT informs the shape — which specific shape to use at each openness level.
 *
 * Ported from Historacle's useTextLipSync React hook to vanilla TypeScript.
 *
 * Preston Blair 9-shape system:
 *   A = M,B,P (closed)  B = consonants (teeth)  C = A,I (open vowel)
 *   D = E (wide stretch) E = O (round)  F = U,W,Q (pucker)
 *   G = F,V (teeth on lip)  H = L (tongue)  X = rest/idle
 */

export type MouthShape = 'X' | 'A' | 'B' | 'C' | 'D' | 'E' | 'F' | 'G' | 'H';

// --- Audio constants ---
const NOISE_FLOOR = 10;
const RISE_FACTOR = 0.28;    // snappy rise
const DECAY_FACTOR = 0.18;   // moderate decay

const SILENCE_GRACE_MS = 200;
const SILENCE_DONE_MS = 800;

// --- Hysteresis thresholds ---
const THRESH_LOW_TO_MID = 0.08;
const THRESH_LOW_TO_HIGH = 0.30;
const THRESH_MID_TO_LOW = 0.05;
const THRESH_MID_TO_HIGH = 0.30;
const THRESH_HIGH_TO_MID = 0.20;
const THRESH_HIGH_TO_LOW = 0.06;

const MIN_SHAPE_HOLD_MS = 100;
const ADVANCE_RATE_MS = 180;

// --- Shape preference types ---
interface ShapePreference {
  low: MouthShape;
  mid: MouthShape;
  high: MouthShape;
}

const DEFAULT_PREF: ShapePreference = { low: 'B', mid: 'C', high: 'D' };

// --- Digraph preferences (checked first) ---
const DIGRAPH_PREFS: [string, ShapePreference][] = [
  ['th', { low: 'B', mid: 'B', high: 'B' }],
  ['sh', { low: 'B', mid: 'B', high: 'B' }],
  ['ch', { low: 'B', mid: 'B', high: 'C' }],
  ['ph', { low: 'G', mid: 'G', high: 'G' }],
  ['wh', { low: 'F', mid: 'F', high: 'F' }],
  ['ng', { low: 'B', mid: 'B', high: 'B' }],
  ['oo', { low: 'F', mid: 'F', high: 'E' }],
  ['ee', { low: 'D', mid: 'D', high: 'D' }],
  ['ou', { low: 'E', mid: 'C', high: 'C' }],
  ['ow', { low: 'F', mid: 'E', high: 'E' }],
  ['ai', { low: 'C', mid: 'C', high: 'C' }],
  ['ay', { low: 'C', mid: 'C', high: 'C' }],
];

// --- Letter preferences ---
const LETTER_PREFS: Record<string, ShapePreference> = {
  // Vowels
  'a': { low: 'B', mid: 'C', high: 'C' },
  'e': { low: 'B', mid: 'D', high: 'D' },
  'i': { low: 'B', mid: 'C', high: 'C' },
  'o': { low: 'E', mid: 'E', high: 'E' },
  'u': { low: 'F', mid: 'F', high: 'F' },
  'y': { low: 'B', mid: 'D', high: 'D' },
  // Bilabials
  'p': { low: 'A', mid: 'A', high: 'A' },
  'b': { low: 'A', mid: 'A', high: 'A' },
  'm': { low: 'A', mid: 'A', high: 'A' },
  // Labiodentals
  'f': { low: 'G', mid: 'G', high: 'G' },
  'v': { low: 'G', mid: 'G', high: 'G' },
  // Puckered
  'w': { low: 'F', mid: 'F', high: 'F' },
  // Sibilants
  's': { low: 'B', mid: 'B', high: 'B' },
  'z': { low: 'B', mid: 'B', high: 'B' },
  // Stops
  't': { low: 'B', mid: 'B', high: 'B' },
  'd': { low: 'B', mid: 'B', high: 'B' },
  'k': { low: 'B', mid: 'B', high: 'B' },
  'g': { low: 'B', mid: 'B', high: 'B' },
  'c': { low: 'B', mid: 'B', high: 'B' },
  // Nasals
  'n': { low: 'B', mid: 'B', high: 'B' },
  // Liquids
  'l': { low: 'H', mid: 'H', high: 'H' },
  'r': { low: 'B', mid: 'B', high: 'C' },
  // Other
  'h': { low: 'B', mid: 'C', high: 'C' },
  'j': { low: 'B', mid: 'B', high: 'B' },
  'x': { low: 'B', mid: 'B', high: 'B' },
  'q': { low: 'F', mid: 'F', high: 'F' },
};

function textToPreferences(text: string): ShapePreference[] {
  const lower = text.toLowerCase();
  const prefs: ShapePreference[] = [];
  let i = 0;

  while (i < lower.length) {
    const char = lower[i];

    if (!/[a-z]/.test(char)) {
      i++;
      continue;
    }

    let matched = false;
    if (i + 1 < lower.length) {
      const di = lower.slice(i, i + 2);
      for (const [pattern, pref] of DIGRAPH_PREFS) {
        if (di === pattern) {
          prefs.push(pref);
          i += 2;
          matched = true;
          break;
        }
      }
    }

    if (!matched) {
      prefs.push(LETTER_PREFS[char] ?? DEFAULT_PREF);
      i++;
    }
  }

  return prefs;
}

function getAudioEnergy(analyser: AnalyserNode, dataArray: Uint8Array): number {
  analyser.getByteFrequencyData(dataArray);
  let sum = 0;
  const end = Math.min(30, dataArray.length);
  for (let i = 1; i < end; i++) {
    sum += (dataArray[i] < NOISE_FLOOR ? 0 : dataArray[i]);
  }
  return sum / (end - 1) / 255;
}

export class LipSyncEngine {
  private analyser: AnalyserNode;
  private dataArray: Uint8Array;
  private prefs: ShapePreference[] = [];
  private prefIndex = 0;
  private smoothEnergy = 0;
  private silenceStart = 0;
  private speechAccumulator = 0;
  private lastFrameTime = 0;
  private currentLevel: 'LOW' | 'MID' | 'HIGH' = 'LOW';
  private lastShapeChangeTime = 0;
  private _currentShape: MouthShape = 'X';
  private _isPlaying = false;

  constructor(analyser: AnalyserNode) {
    this.analyser = analyser;
    this.dataArray = new Uint8Array(analyser.frequencyBinCount);
  }

  get currentShape(): MouthShape {
    return this._currentShape;
  }

  get isPlaying(): boolean {
    return this._isPlaying;
  }

  loadText(text: string): void {
    const prefs = textToPreferences(text);
    if (prefs.length === 0) {
      this.stop();
      return;
    }
    this.prefs = prefs;
    this.prefIndex = 0;
    this.speechAccumulator = 0;
    this._currentShape = 'X';
    this._isPlaying = true;
  }

  stop(): void {
    this._currentShape = 'X';
    this._isPlaying = false;
    this.prefs = [];
    this.prefIndex = 0;
    this.smoothEnergy = 0;
    this.silenceStart = 0;
    this.speechAccumulator = 0;
    this.lastFrameTime = 0;
    this.currentLevel = 'LOW';
    this.lastShapeChangeTime = 0;
  }

  /**
   * Call every animation frame. Returns the current mouth shape.
   */
  update(now: number): MouthShape {
    if (this.prefs.length === 0) {
      if (this._currentShape !== 'X') {
        this._currentShape = 'X';
        this._isPlaying = false;
      }
      this.lastFrameTime = 0;
      return this._currentShape;
    }

    const dt = this.lastFrameTime ? now - this.lastFrameTime : 0;
    this.lastFrameTime = now;

    // Auto-resume suspended AudioContext
    if (this.analyser.context.state === 'suspended' && 'resume' in this.analyser.context) {
      (this.analyser.context as AudioContext).resume().catch(() => {});
      return this._currentShape;
    }

    // Audio energy with smoothing
    const rawEnergy = getAudioEnergy(this.analyser, this.dataArray);
    const prev = this.smoothEnergy;
    this.smoothEnergy = prev + (rawEnergy > prev ? RISE_FACTOR : DECAY_FACTOR) * (rawEnergy - prev);
    const energy = this.smoothEnergy;

    const isSpeechActive = energy > 0.03;

    if (isSpeechActive) {
      this.silenceStart = 0;

      // Advance text cursor
      this.speechAccumulator += dt;
      if (this.speechAccumulator >= ADVANCE_RATE_MS) {
        this.speechAccumulator -= ADVANCE_RATE_MS;
        this.prefIndex = (this.prefIndex + 1) % this.prefs.length;
      }

      const pref = this.prefs[this.prefIndex] ?? DEFAULT_PREF;

      // Hysteresis state machine
      const prevLevel = this.currentLevel;
      let newLevel: 'LOW' | 'MID' | 'HIGH';

      if (prevLevel === 'LOW') {
        newLevel = energy > THRESH_LOW_TO_HIGH ? 'HIGH' : energy > THRESH_LOW_TO_MID ? 'MID' : 'LOW';
      } else if (prevLevel === 'MID') {
        newLevel = energy > THRESH_MID_TO_HIGH ? 'HIGH' : energy < THRESH_MID_TO_LOW ? 'LOW' : 'MID';
      } else {
        newLevel = energy < THRESH_HIGH_TO_LOW ? 'LOW' : energy < THRESH_HIGH_TO_MID ? 'MID' : 'HIGH';
      }
      this.currentLevel = newLevel;

      let shape: MouthShape;
      if (newLevel === 'HIGH') shape = pref.high;
      else if (newLevel === 'MID') shape = pref.mid;
      else shape = pref.low;

      // Enforce minimum hold time
      if (shape !== this._currentShape && (now - this.lastShapeChangeTime) < MIN_SHAPE_HOLD_MS) {
        return this._currentShape;
      }

      if (shape !== this._currentShape) {
        this.lastShapeChangeTime = now;
      }

      this._currentShape = shape;
      this._isPlaying = true;
    } else {
      // Silence
      if (!this.silenceStart) this.silenceStart = now;

      if (now - this.silenceStart > SILENCE_GRACE_MS) {
        this._currentShape = 'X';
      }
      if (now - this.silenceStart > SILENCE_DONE_MS) {
        this._isPlaying = false;
      }
    }

    return this._currentShape;
  }
}
