/**
 * Web Audio API bridge — connects an <audio> element to an AnalyserNode
 * for real-time frequency analysis.
 *
 * Ported from Historacle's useAudioAnalyser React hook to vanilla TypeScript.
 */

const connectedElements = new WeakMap<HTMLAudioElement, {
  source: MediaElementAudioSourceNode;
  analyser: AnalyserNode;
  context: AudioContext;
}>();

export class AudioAnalyser {
  private context: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private source: MediaElementAudioSourceNode | null = null;

  /**
   * Connect an <audio> element to the Web Audio API.
   * Safe to call multiple times with the same element.
   */
  connect(audioElement: HTMLAudioElement): AnalyserNode | null {
    // Check if already connected
    const existing = connectedElements.get(audioElement);
    if (existing) {
      this.context = existing.context;
      this.analyser = existing.analyser;
      this.source = existing.source;
      return this.analyser;
    }

    try {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      if (!AudioCtx) {
        console.warn('[AudioAnalyser] AudioContext not supported');
        return null;
      }

      const ctx = this.context ?? new AudioCtx();
      this.context = ctx;

      // Resume if suspended (browser autoplay policy)
      if (ctx.state === 'suspended') {
        ctx.resume().catch(() => {});
      }

      // Connect: <audio> → MediaElementSource → AnalyserNode → destination
      const source = ctx.createMediaElementSource(audioElement);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.4;
      analyser.minDecibels = -90;
      analyser.maxDecibels = -10;

      source.connect(analyser);
      analyser.connect(ctx.destination);

      // Cache to prevent double-connect
      connectedElements.set(audioElement, { source, analyser, context: ctx });

      this.analyser = analyser;
      this.source = source;

      console.log('[Blabberer] AudioAnalyser connected');
      return analyser;
    } catch (err) {
      console.warn('[AudioAnalyser] Failed to connect:', err);
      return null;
    }
  }

  getAnalyserNode(): AnalyserNode | null {
    return this.analyser;
  }

  destroy(): void {
    if (this.context && this.context.state !== 'closed') {
      this.context.close().catch(() => {});
    }
    this.context = null;
    this.analyser = null;
    this.source = null;
  }
}
