"use client";

/**
 * MemoryBloom — the centerpiece.
 *
 * A ferrite-core memory plane reimagined as a blossom: seven woven rings of
 * ~9,000 cross-stitch pixels in the brand palette, with a few rose "bad
 * memories" threaded through. The whole bloom breathes; the cursor warps it
 * like fabric (repulsion + spring, the classic dither-portrait interaction);
 * every few seconds a trace pulse rolls outward from the center core.
 *
 * Canvas 2D, zero dependencies. Adaptive particle count, DPR-aware, pauses
 * offscreen and on hidden tabs, static frame under reduced motion.
 */

import { useEffect, useRef } from "react";

interface P {
  hx: number; // home
  hy: number;
  x: number;
  y: number;
  vx: number;
  vy: number;
  s: number; // size
  ph: number; // breathing phase
  amp: number; // breathing amplitude
  c: number; // color group index
}

// brand palette, dark → bright, plus the accents that carry meaning
const COLORS = [
  "#123640", // deep shadow
  "#1d4a56", // deep
  "#35646f", // mid-deep
  "#5a8a96", // mid
  "#7ea7b0", // light-mid
  "#9bb8b8", // light
  "#cfdedb", // haze highlight
  "#b95c5c", // rose — the bad memories
  "#c98a3d", // amber — the stale one
];

function buildParticles(count: number, R: number): P[] {
  // seeded-ish randomness is unnecessary; organic variance is the point
  const ps: P[] = [];
  const rings: Array<{ cx: number; cy: number; r: number; w: number; share: number; bright: number }> = [
    { cx: 0, cy: 0, r: R * 0.3, w: R * 0.075, share: 0.2, bright: 1 }, // center core
  ];
  // six petal cores
  for (let i = 0; i < 6; i++) {
    const a = (i / 6) * Math.PI * 2 - Math.PI / 2;
    rings.push({
      cx: Math.cos(a) * R * 0.52,
      cy: Math.sin(a) * R * 0.52,
      r: R * 0.34,
      w: R * 0.085,
      share: 0.115,
      bright: 0.55 + 0.14 * ((i * 2.39) % 1),
    });
  }

  const gauss = () =>
    (Math.random() + Math.random() + Math.random() + Math.random() - 2) / 2;

  for (const ring of rings) {
    const n = Math.floor(count * ring.share);
    for (let i = 0; i < n; i++) {
      const th = Math.random() * Math.PI * 2;
      const rr = ring.r + gauss() * ring.w;
      const hx = ring.cx + Math.cos(th) * rr;
      const hy = ring.cy + Math.sin(th) * rr;
      // light falls from the top — shade by height and ring brightness
      const lightness =
        ring.bright * (0.62 + 0.38 * (0.5 - hy / (2.6 * R)) ) +
        (Math.random() * 0.22 - 0.11);
      let c = Math.max(0, Math.min(6, Math.round(lightness * 6)));
      const roll = Math.random();
      if (roll > 0.986) c = 7; // a rose bad-memory stitch
      else if (roll > 0.982) c = 8; // rarer amber stale stitch
      ps.push({
        hx,
        hy,
        x: hx + (Math.random() - 0.5) * R * 2.4,
        y: hy + (Math.random() - 0.5) * R * 2.4,
        vx: 0,
        vy: 0,
        s: 1 + Math.random() * 1.7,
        ph: Math.random() * Math.PI * 2,
        amp: 0.6 + Math.random() * 1.6,
        c,
      });
    }
  }
  // halo dust
  const dust = Math.floor(count * 0.07);
  for (let i = 0; i < dust; i++) {
    const th = Math.random() * Math.PI * 2;
    const rr = R * (0.95 + Math.random() * 0.45);
    ps.push({
      hx: Math.cos(th) * rr,
      hy: Math.sin(th) * rr * 0.92,
      x: Math.cos(th) * rr * 1.6,
      y: Math.sin(th) * rr * 1.6,
      vx: 0,
      vy: 0,
      s: 0.8 + Math.random(),
      ph: Math.random() * Math.PI * 2,
      amp: 1 + Math.random() * 2,
      c: Math.random() > 0.5 ? 1 : 0,
    });
  }
  // draw order: dark first, bright and accents on top
  ps.sort((a, b) => a.c - b.c);
  return ps;
}

export function MemoryBloom({ className = "" }: { className?: string }) {
  const hostRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const host = hostRef.current;
    const canvas = canvasRef.current;
    if (!host || !canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const fine = window.matchMedia("(pointer: fine)").matches;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);

    let W = 0;
    let H = 0;
    let R = 0;
    let ps: P[] = [];
    let raf = 0;
    let visible = true;
    // pointer in canvas space; far away = inert
    const mouse = { x: -9999, y: -9999 };

    const build = () => {
      const rect = host.getBoundingClientRect();
      W = rect.width;
      H = rect.height;
      canvas.width = Math.floor(W * dpr);
      canvas.height = Math.floor(H * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      R = Math.min(W, H) * 0.31;
      const mem = (navigator as unknown as { deviceMemory?: number }).deviceMemory ?? 4;
      const base = W < 640 ? 3800 : mem >= 6 ? 9500 : 6500;
      ps = buildParticles(reduced ? Math.min(base, 6000) : base, R);
      if (reduced) {
        for (const p of ps) {
          p.x = p.hx;
          p.y = p.hy;
        }
        draw(0);
      }
    };

    const draw = (time: number) => {
      ctx.clearRect(0, 0, W, H);
      const cx = W / 2;
      const cy = H / 2;

      // trace pulse: a ring of light rolling outward every 6s
      const cycle = (time % 6000) / 6000;
      const pulseR = cycle * R * 1.7;
      const pulseOn = !reduced && cycle < 0.62;

      let last = -1;
      for (const p of ps) {
        if (p.c !== last) {
          ctx.fillStyle = COLORS[p.c];
          last = p.c;
        }
        const px = p.x;
        const py = p.y;
        if (pulseOn) {
          const d = Math.abs(Math.hypot(p.hx, p.hy) - pulseR);
          if (d < R * 0.09) {
            // lift stitches on the wavefront
            const boost = 1 - d / (R * 0.09);
            ctx.fillStyle = p.c >= 7 ? COLORS[p.c] : "#e8f1ef";
            ctx.globalAlpha = 0.5 + 0.5 * boost;
            ctx.fillRect(cx + px - p.s / 2, cy + py - p.s / 2, p.s + boost, p.s + boost);
            ctx.globalAlpha = 1;
            ctx.fillStyle = COLORS[p.c];
            continue;
          }
        }
        ctx.fillRect(cx + px - p.s / 2, cy + py - p.s / 2, p.s, p.s);
      }
    };

    const step = (time: number) => {
      const breathe = time * 0.0012;
      for (const p of ps) {
        // breathing home
        const bx = p.hx + Math.sin(breathe + p.ph) * p.amp;
        const by = p.hy + Math.cos(breathe * 0.9 + p.ph) * p.amp;
        // spring home
        p.vx += (bx - p.x) * 0.02;
        p.vy += (by - p.y) * 0.02;
        // cursor warp
        const dx = p.x - mouse.x;
        const dy = p.y - mouse.y;
        const d2 = dx * dx + dy * dy;
        const RR = R * 0.62;
        if (d2 < RR * RR && d2 > 0.01) {
          const d = Math.sqrt(d2);
          const f = ((RR - d) / RR) * 1.9;
          p.vx += (dx / d) * f;
          p.vy += (dy / d) * f;
        }
        p.vx *= 0.86;
        p.vy *= 0.86;
        p.x += p.vx;
        p.y += p.vy;
      }
      draw(time);
      if (visible) raf = requestAnimationFrame(step);
    };

    const onMove = (e: PointerEvent) => {
      const r = canvas.getBoundingClientRect();
      mouse.x = e.clientX - r.left - r.width / 2;
      mouse.y = e.clientY - r.top - r.height / 2;
    };
    const onLeave = () => {
      mouse.x = -9999;
      mouse.y = -9999;
    };

    build();

    if (!reduced) {
      raf = requestAnimationFrame(step);
      if (fine) {
        window.addEventListener("pointermove", onMove, { passive: true });
        document.addEventListener("pointerleave", onLeave);
      }
    }

    const io = new IntersectionObserver(
      ([entry]) => {
        const wasVisible = visible;
        visible = entry.isIntersecting && !document.hidden;
        if (visible && !wasVisible && !reduced) raf = requestAnimationFrame(step);
        if (!visible) cancelAnimationFrame(raf);
      },
      { threshold: 0.05 },
    );
    io.observe(host);

    const onVis = () => {
      const wasVisible = visible;
      visible = !document.hidden;
      if (visible && !wasVisible && !reduced) raf = requestAnimationFrame(step);
      if (!visible) cancelAnimationFrame(raf);
    };
    document.addEventListener("visibilitychange", onVis);

    let resizeT = 0;
    const onResize = () => {
      window.clearTimeout(resizeT);
      resizeT = window.setTimeout(build, 180);
    };
    window.addEventListener("resize", onResize);

    return () => {
      cancelAnimationFrame(raf);
      io.disconnect();
      window.removeEventListener("pointermove", onMove);
      document.removeEventListener("pointerleave", onLeave);
      document.removeEventListener("visibilitychange", onVis);
      window.removeEventListener("resize", onResize);
      window.clearTimeout(resizeT);
    };
  }, []);

  return (
    <div ref={hostRef} className={`pointer-events-none ${className}`} aria-hidden>
      <canvas ref={canvasRef} className="h-full w-full" />
    </div>
  );
}
