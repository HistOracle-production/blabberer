/**
 * Dual-layer crossfade sprite renderer.
 *
 * Uses two stacked <img> elements that alternate opacity
 * for smooth 60ms transitions between mouth shapes.
 *
 * Ported from Historacle's MouthOverlay React component to vanilla TypeScript.
 */

import type { MouthShape } from './lipSync';
import { LipSyncEngine } from './lipSync';

const CROSSFADE_MS = 60;

export class MouthRenderer {
  private container: HTMLElement;
  private imgA: HTMLImageElement;
  private imgB: HTMLImageElement;
  private activeLayer: 'A' | 'B' = 'A';
  private currentSrc = '';
  private sprites: Record<string, string> = {};
  private loadedUrls = new Set<string>();
  private rafId = 0;
  private prevShape: MouthShape = 'X';

  constructor(container: HTMLElement) {
    this.container = container;
    container.style.position = 'relative';
    container.style.overflow = 'hidden';

    const imgStyle = `
      position: absolute;
      top: 0; left: 0;
      width: 100%; height: 100%;
      object-fit: contain;
      pointer-events: none;
      transition: opacity ${CROSSFADE_MS}ms ease-in-out;
      will-change: opacity;
      backface-visibility: hidden;
    `;

    this.imgA = document.createElement('img');
    this.imgA.style.cssText = imgStyle + 'opacity: 1; z-index: 1;';
    this.imgA.alt = '';
    this.imgA.draggable = false;

    this.imgB = document.createElement('img');
    this.imgB.style.cssText = imgStyle + 'opacity: 0; z-index: 2;';
    this.imgB.alt = '';
    this.imgB.draggable = false;

    container.appendChild(this.imgA);
    container.appendChild(this.imgB);
  }

  /**
   * Load sprite URLs. Keys should be shape names (A, B, C, ... H, X).
   */
  loadSprites(sprites: Record<string, string>): void {
    this.sprites = sprites;
    this.loadedUrls.clear();

    // Preload all sprites
    for (const [name, url] of Object.entries(sprites)) {
      const img = new Image();
      img.onload = () => this.loadedUrls.add(url);
      img.src = url;
    }

    // Show idle sprite
    const idleUrl = sprites['X'] || Object.values(sprites)[0];
    if (idleUrl) {
      this.imgA.src = idleUrl;
      this.imgB.src = idleUrl;
      this.currentSrc = idleUrl;
      this.loadedUrls.add(idleUrl);
    }
  }

  /**
   * Crossfade to a specific mouth shape.
   */
  setShape(shape: MouthShape): void {
    const url = this.sprites[shape];
    if (!url || url === this.currentSrc) return;
    this.currentSrc = url;

    const incoming = this.activeLayer === 'A' ? this.imgB : this.imgA;
    const outgoing = this.activeLayer === 'A' ? this.imgA : this.imgB;
    const nextLayer: 'A' | 'B' = this.activeLayer === 'A' ? 'B' : 'A';

    if (this.loadedUrls.has(url)) {
      incoming.src = url;
      incoming.style.opacity = '1';
      outgoing.style.opacity = '0';
      this.activeLayer = nextLayer;
    } else {
      incoming.src = url;
      incoming.onload = () => {
        this.loadedUrls.add(url);
        incoming.onload = null;
        if (this.currentSrc === url) {
          incoming.style.opacity = '1';
          outgoing.style.opacity = '0';
        }
      };
      this.activeLayer = nextLayer;
    }
  }

  /**
   * Start the animation loop driven by a LipSyncEngine.
   */
  startLoop(engine: LipSyncEngine): void {
    this.stopLoop();

    const animate = () => {
      this.rafId = requestAnimationFrame(animate);
      const shape = engine.update(performance.now());

      if (shape !== this.prevShape) {
        this.prevShape = shape;
        this.setShape(shape);
      }
    };

    this.rafId = requestAnimationFrame(animate);
  }

  /**
   * Stop the animation loop and show idle shape.
   */
  stopLoop(): void {
    if (this.rafId) {
      cancelAnimationFrame(this.rafId);
      this.rafId = 0;
    }
    this.setShape('X');
    this.prevShape = 'X';
  }

  destroy(): void {
    this.stopLoop();
    this.container.removeChild(this.imgA);
    this.container.removeChild(this.imgB);
  }
}
