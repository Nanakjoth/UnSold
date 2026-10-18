import { useEffect, useRef } from "react";
import { buildGraph, depthOf, mulberry32, projectPoints } from "../lib/neuralGraph";
import type { Graph } from "../lib/neuralGraph";

/**
 * NeuralBackdrop: a slowly rotating 3D network of nodes and links drawn on a
 * 2D canvas with real perspective projection. No dependencies.
 *
 * Purely decorative — the nodes are not live data, real mentors or real
 * connections. Never caption or describe it as anything else.
 *
 * Behaviour: reads --color-accent / --color-accent-2 / --color-clay from CSS
 * (re-read on theme change); pointer parallax; prefers-reduced-motion draws a
 * single static frame; pauses when hidden or off screen; caps DPR at 2; halves
 * the node count once if frames get expensive, then falls back to a still.
 */

export type NeuralBackdropProps = {
  className?: string;
  /** Node indices (1..N-1) to light up as "matches". Node 0 is the "you" node. */
  highlight?: number[];
  /** Override the default node count (60 desktop, 30 small screens). */
  nodeCount?: number;
  /** Phase 2: tint a node and fade its links when a message is blocked. */
  flash?: { node: number; kind: "blocked"; key: number };
};

type Pulse = { a: number; b: number; t: number; speed: number };

const SEED = 20261018; // fixed: the layout must not change on reload
const FOCAL = 2.6;
const SPIN = 0.08; // rad/s
const TILT = 0.35; // fixed X tilt (rad)
const FRAME_BUDGET_MS = 8; // degrade above this average draw cost
const MEASURE_MS = 1000;
const FLASH_OUT_MS = 600; // links fade to 0
const FLASH_BACK_MS = 1200; // then restore
const FLASH_TINT_MS = 600; // reduced-motion tint duration

export default function NeuralBackdrop({
  className = "",
  highlight = [],
  nodeCount,
  flash,
}: NeuralBackdropProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const highlightRef = useRef(highlight);
  highlightRef.current = highlight;
  const flashRef = useRef(flash);
  flashRef.current = flash;
  const drawRef = useRef<(() => void) | null>(null);
  const staticModeRef = useRef(false);

  // Static mode (reduced motion or degraded): redraw when the props change.
  const highlightKey = highlight.join(",");
  const flashKey = flash ? `${flash.node}:${flash.key}` : "";
  useEffect(() => {
    if (staticModeRef.current) drawRef.current?.();
  }, [highlightKey, flashKey]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const reduceQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    const initialN = nodeCount ?? (window.innerWidth < 640 ? 30 : 60);

    const small = window.innerWidth < 640;
    const pulseCount = small ? 3 : 6;
    const newPulse = (g: Graph): Pulse => {
      const e = g.edges[Math.floor(Math.random() * g.edges.length)];
      if (!e) return { a: 0, b: 0, t: 0, speed: 0.2 };
      return { a: e[0], b: e[1], t: 0, speed: 0.2 + Math.random() * 0.3 };
    };
    let graph = buildGraph(initialN, mulberry32(SEED));
    let pulses: Pulse[] = Array.from({ length: pulseCount }, () => newPulse(graph));
    const rebuild = (n: number): Graph => {
      const next = buildGraph(n, mulberry32(SEED));
      pulses = Array.from({ length: pulseCount }, () => newPulse(next));
      return next;
    };

    // --- Colours from CSS (FR8) -------------------------------------------
    let accent = "#35E0A1";
    let line = "#4DA3FF";
    let dim = "#9AA7B8";
    let danger = "#F0725A";
    const readColors = () => {
      const cs = getComputedStyle(document.documentElement);
      accent = cs.getPropertyValue("--color-accent").trim() || accent;
      line = cs.getPropertyValue("--color-accent-2").trim() || line;
      const light =
        document.documentElement.getAttribute("data-theme") === "light" ||
        document.documentElement.classList.contains("light");
      dim = cs.getPropertyValue("--color-text-dim").trim() || (light ? "#5A6B7A" : "#9AA7B8");
      danger = cs.getPropertyValue("--color-danger").trim() || cs.getPropertyValue("--color-clay").trim() || danger;
    };
    readColors();
    const themeObserver = new MutationObserver(readColors);
    themeObserver.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-theme", "class"],
    });

    // --- Sizing (FR9) ------------------------------------------------------
    let w = 0;
    let h = 0;
    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const r = canvas.getBoundingClientRect();
      w = r.width;
      h = r.height;
      canvas.width = w > 0 && h > 0 ? Math.max(1, Math.round(w * dpr)) : 1;
      canvas.height = w > 0 && h > 0 ? Math.max(1, Math.round(h * dpr)) : 1;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      if (staticModeRef.current) drawRef.current?.();
    };

    // --- Animation state ---------------------------------------------------
    let angle = 0;
    let px = 0; // smoothed pointer offset
    let py = 0;
    let tx = 0; // target pointer offset
    let ty = 0;
    let last = performance.now();
    let raf = 0;
    let running = false;
    let flashNode = -1;
    let flashStart = 0;
    let flashKeySeen = flash ? flash.key : 0;
    let flashTimer = 0;
    let measureOn = true;
    let measureStart = 0;
    let measureCost = 0;
    let measureFrames = 0;
    let passes = 0;

    const onPointer = (e: PointerEvent) => {
      tx = Math.max(-0.5, Math.min(0.5, e.clientX / window.innerWidth - 0.5));
      ty = Math.max(-0.5, Math.min(0.5, e.clientY / window.innerHeight - 0.5));
    };

    const validIndex = (i: number) => Number.isInteger(i) && i >= 1 && i <= graph.points.length - 1;

    // --- Render (FR4, FR5, FR7, FR11, Phase 2) ----------------------------
    const render = (now: number) => {
      if (w < 1 || h < 1) return; // zero-size guard
      const reduce = reduceQuery.matches || staticModeRef.current;
      const dt = reduce ? 0 : Math.min((now - last) / 1000, 0.05);
      last = now;
      if (!reduce) {
        angle += dt * SPIN;
        px += (tx - px) * 0.05;
        py += (ty - py) * 0.05;
      }

      // Phase 2 flash bookkeeping.
      const f = flashRef.current;
      if (f && f.kind === "blocked" && f.key !== flashKeySeen) {
        flashKeySeen = f.key;
        flashNode = validIndex(f.node) ? f.node : -1;
        flashStart = now;
        if (flashNode >= 0 && reduce) {
          window.clearTimeout(flashTimer);
          flashTimer = window.setTimeout(() => {
            flashNode = -1;
            drawRef.current?.();
          }, FLASH_TINT_MS);
        }
      }
      let fade = 1;
      if (flashNode >= 0 && !reduce) {
        const e = now - flashStart;
        if (e < FLASH_OUT_MS) fade = 1 - e / FLASH_OUT_MS;
        else if (e < FLASH_OUT_MS + FLASH_BACK_MS) fade = (e - FLASH_OUT_MS) / FLASH_BACK_MS;
        else flashNode = -1;
      }

      const proj = projectPoints(graph.points, {
        angleY: angle + px * 0.6,
        tiltX: TILT + py * 0.4,
        focal: FOCAL,
        radius: Math.min(w, h) * 0.46,
        originX: w * 0.5,
        originY: h * 0.5,
      });
      const hl = new Set(highlightRef.current.filter(validIndex));

      ctx.clearRect(0, 0, w, h);

      for (const [a, b] of graph.edges) {
        const A = proj[a];
        const B = proj[b];
        const lit = (a === 0 && hl.has(b)) || (b === 0 && hl.has(a));
        const cut = a === flashNode || b === flashNode ? fade : 1;
        ctx.globalAlpha = (lit ? 0.9 : 0.08 + 0.22 * depthOf((A.z + B.z) / 2)) * cut;
        ctx.strokeStyle = lit ? accent : line;
        ctx.lineWidth = lit ? 1.6 : 1;
        ctx.beginPath();
        ctx.moveTo(A.x, A.y);
        ctx.lineTo(B.x, B.y);
        ctx.stroke();
      }

      const order = proj.map((_, i) => i).sort((i, j) => proj[j].z - proj[i].z); // far first
      for (const i of order) {
        const P = proj[i];
        const d = depthOf(P.z);
        const isYou = i === 0;
        const isHl = hl.has(i);
        const isFlash = i === flashNode;
        const r = (isYou ? 5 : isHl ? 4.5 : 1.4 + 1.6 * d) * P.s;
        if (isYou || isHl || isFlash) {
          ctx.globalAlpha = 0.14; // soft halo, no shadowBlur (FR13)
          ctx.fillStyle = isFlash ? danger : isYou ? line : accent;
          ctx.beginPath();
          ctx.arc(P.x, P.y, r * 3, 0, Math.PI * 2);
          ctx.fill();
        }
        ctx.globalAlpha = isYou || isHl ? 1 : 0.25 + 0.6 * d;
        ctx.fillStyle = isFlash ? danger : isYou ? line : isHl ? accent : dim;
        ctx.beginPath();
        ctx.arc(P.x, P.y, r, 0, Math.PI * 2);
        ctx.fill();
      }

      if (!reduce) {
        for (let k = 0; k < pulses.length; k++) {
          const p = pulses[k];
          p.t += p.speed * dt;
          if (p.t >= 1) {
            pulses[k] = newPulse(graph);
            continue;
          }
          const A = proj[p.a];
          const B = proj[p.b];
          if (!A || !B) continue;
          ctx.globalAlpha = 0.95;
          ctx.fillStyle = accent;
          ctx.beginPath();
          ctx.arc(A.x + (B.x - A.x) * p.t, A.y + (B.y - A.y) * p.t, 2, 0, Math.PI * 2);
          ctx.fill();
        }
      }
      ctx.globalAlpha = 1;
    };
    drawRef.current = () => render(performance.now());

    // --- Loop, pause, adaptive quality (FR10, NFR) ------------------------
    const loop = (now: number) => {
      raf = requestAnimationFrame(loop);
      const t0 = performance.now();
      render(now);
      if (measureOn) {
        measureCost += performance.now() - t0;
        measureFrames += 1;
        if (now - measureStart >= MEASURE_MS && measureFrames > 0) {
          const avg = measureCost / measureFrames;
          measureCost = 0;
          measureFrames = 0;
          measureStart = now;
          passes += 1;
          if (avg > FRAME_BUDGET_MS) {
            if (passes === 1) {
              // Halve the node count once, keep animating.
              graph = rebuild(Math.max(12, Math.floor(graph.points.length / 2)));
            } else {
              // Still expensive: settle on a single static frame.
              staticModeRef.current = true;
              stop();
              render(now);
            }
          }
          if (passes >= 2) measureOn = false; // never degrade repeatedly
        }
      }
    };
    const start = () => {
      if (reduceQuery.matches || running || staticModeRef.current) return;
      running = true;
      last = performance.now();
      measureStart = last;
      raf = requestAnimationFrame(loop);
    };
    const stop = () => {
      running = false;
      cancelAnimationFrame(raf);
    };

    // --- Observers, listeners, first draw ---------------------------------
    const onVisibility = () => (document.hidden ? stop() : start());
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);
    window.addEventListener("resize", resize); // DPR can change without a box change
    const io = new IntersectionObserver(([entry]) => (entry.isIntersecting ? start() : stop()));
    io.observe(canvas);
    document.addEventListener("visibilitychange", onVisibility);
    if (!reduceQuery.matches) window.addEventListener("pointermove", onPointer, { passive: true });
    staticModeRef.current = reduceQuery.matches;
    if (staticModeRef.current) drawRef.current();
    else start();

    return () => {
      stop();
      window.clearTimeout(flashTimer);
      ro.disconnect();
      io.disconnect();
      themeObserver.disconnect();
      window.removeEventListener("resize", resize);
      window.removeEventListener("pointermove", onPointer);
      document.removeEventListener("visibilitychange", onVisibility);
      drawRef.current = null;
      staticModeRef.current = false;
    };
  }, [nodeCount]);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className={`pointer-events-none absolute inset-0 h-full w-full ${className}`}
    />
  );
}
