"use client";

import { AnimatePresence, LayoutGroup, motion } from "framer-motion";
import {
  type CSSProperties,
  type RefObject,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

type EvidenceId = "aws" | "owasp" | "google" | "langgraph" | "zep" | "letta";

type EvidenceSource = {
  id: EvidenceId;
  name: string;
  issue: string;
  headline: string;
  proof: string;
  sourceLabel: string;
  sourceUrl: string;
  accent: string;
  position: string;
  side: "left" | "right";
  curve: number;
};

type Point = { x: number; y: number };

type OrbitGeometry = {
  width: number;
  height: number;
  target: Point;
  nodes: Partial<Record<EvidenceId, Point>>;
};

const SOURCES: EvidenceSource[] = [
  {
    id: "aws",
    name: "AWS AgentCore",
    issue: "derived deletion",
    headline: "The event is deleted. Its derived memory can remain.",
    proof:
      "AWS says deleting an event “doesn’t remove the structured information derived out of it from the long term memory.”",
    sourceLabel: "Read the AWS documentation",
    sourceUrl:
      "https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/short-term-delete-event.html",
    accent: "#ff9900",
    position: "left-[9%] top-[32%] sm:left-[7%] sm:top-[35%]",
    side: "left",
    curve: -66,
  },
  {
    id: "google",
    name: "Google Memory Bank",
    issue: "memory poisoning",
    headline: "False memory can steer future sessions.",
    proof:
      "Google warns that poisoned information stored in Memory Bank may guide an agent in future sessions.",
    sourceLabel: "Read the Google Cloud documentation",
    sourceUrl:
      "https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/memory-bank",
    accent: "#4285f4",
    position: "left-[91%] top-[31%] sm:left-[93%] sm:top-[34%]",
    side: "right",
    curve: 66,
  },
  {
    id: "owasp",
    name: "OWASP ASI06",
    issue: "persistent compromise",
    headline: "One poisoned write can influence future reasoning.",
    proof:
      "OWASP documents corrupted context that persists and shapes future planning, tool use, and behavior.",
    sourceLabel: "Read the OWASP analysis",
    sourceUrl:
      "https://genai.owasp.org/2026/05/13/memory-is-a-feature-it-is-also-an-attack-surface/",
    accent: "#e5ecea",
    position: "left-[11%] top-[56%] sm:left-[12%] sm:top-[61%]",
    side: "left",
    curve: 52,
  },
  {
    id: "zep",
    name: "Zep",
    issue: "changing facts",
    headline: "A fact can be true—and later become wrong.",
    proof:
      "Zep tracks valid_at and invalid_at because new information can invalidate an existing fact while history remains.",
    sourceLabel: "Read the Zep documentation",
    sourceUrl: "https://help.getzep.com/facts",
    accent: "#9b87f5",
    position: "left-[89%] top-[56%] sm:left-[88%] sm:top-[61%]",
    side: "right",
    curve: -52,
  },
  {
    id: "langgraph",
    name: "LangGraph",
    issue: "update ambiguity",
    headline: "Models over-insert, over-update, and retain stale context.",
    proof:
      "LangGraph says deleting or updating memory items can be tricky, while long histories distract models with stale content.",
    sourceLabel: "Read the LangGraph documentation",
    sourceUrl: "https://docs.langchain.com/oss/python/concepts/memory",
    accent: "#63d4bd",
    position: "left-[24%] top-[75%] sm:left-[25%] sm:top-[72%]",
    side: "left",
    curve: -38,
  },
  {
    id: "letta",
    name: "Letta",
    issue: "shared overwrite",
    headline: "Persistent shared memory can be overwritten.",
    proof:
      "Letta warns that concurrent shared-block updates are last-write-wins and can overwrite every earlier change.",
    sourceLabel: "Read the Letta documentation",
    sourceUrl:
      "https://docs.letta.com/guides/core-concepts/memory/memory-blocks/",
    accent: "#ed6a8a",
    position: "left-[76%] top-[75%] sm:left-[75%] sm:top-[72%]",
    side: "right",
    curve: 38,
  },
];

function SourceMark({ id }: { id: EvidenceId }) {
  if (id === "aws") {
    return (
      <span className="relative pb-1 font-sans text-[16px] font-semibold tracking-[-0.05em] text-white">
        aws
        <svg
          aria-hidden
          viewBox="0 0 38 10"
          className="absolute -bottom-0.5 left-0 h-2 w-full"
        >
          <path
            d="M4 2.5c8.5 5 19.5 5.5 29.5.3"
            fill="none"
            stroke="#ff9900"
            strokeWidth="1.7"
            strokeLinecap="round"
          />
        </svg>
      </span>
    );
  }

  if (id === "google") {
    return (
      <span className="bg-[conic-gradient(from_-35deg,#4285f4_0_25%,#34a853_0_43%,#fbbc05_0_67%,#ea4335_0_83%,#4285f4_0)] bg-clip-text font-sans text-[22px] font-bold text-transparent">
        G
      </span>
    );
  }

  if (id === "owasp") {
    return (
      <span className="grid size-7 place-items-center rounded-full border border-white/60 font-sans text-[12px] font-bold text-white">
        O
      </span>
    );
  }

  if (id === "langgraph") {
    return (
      <svg aria-hidden viewBox="0 0 40 40" className="size-8">
        <g fill="none" stroke="#8de9d5" strokeWidth="1.6">
          <path d="M7 10 20 6l13 10-6 17-18-2Z" />
          <path d="m7 10 20 23m6-17L9 31M20 6v19" opacity=".7" />
        </g>
        <g fill="#c9fff2">
          <circle cx="7" cy="10" r="2.4" />
          <circle cx="20" cy="6" r="2.4" />
          <circle cx="33" cy="16" r="2.4" />
          <circle cx="27" cy="33" r="2.4" />
          <circle cx="9" cy="31" r="2.4" />
          <circle cx="20" cy="25" r="2.4" />
        </g>
      </svg>
    );
  }

  if (id === "zep") {
    return (
      <span className="font-sans text-[16px] font-black uppercase tracking-[-0.08em] text-[#b8aaff]">
        zep
      </span>
    );
  }

  return (
    <span className="font-sans text-[16px] font-semibold tracking-[-0.05em] text-[#f5a2b6]">
      letta
    </span>
  );
}

function clamp(value: number, minimum: number, maximum: number) {
  return Math.min(Math.max(value, minimum), maximum);
}

function buildPath(
  source: EvidenceSource,
  start: Point,
  target: Point,
  width: number,
) {
  const dx = target.x - start.x;
  const dy = target.y - start.y;
  const distance = Math.max(Math.hypot(dx, dy), 1);
  const normalX = -dy / distance;
  const normalY = dx / distance;
  const scale = clamp(width / 1000, 0.52, 1.2);
  const bend = source.curve * scale;
  const controlOne = {
    x: start.x + dx * 0.3 + normalX * bend,
    y: start.y + dy * 0.3 + normalY * bend,
  };
  const controlTwo = {
    x: start.x + dx * 0.72 - normalX * bend * 0.32,
    y: start.y + dy * 0.72 - normalY * bend * 0.32,
  };

  return [
    `M ${start.x.toFixed(2)} ${start.y.toFixed(2)}`,
    `C ${controlOne.x.toFixed(2)} ${controlOne.y.toFixed(2)},`,
    `${controlTwo.x.toFixed(2)} ${controlTwo.y.toFixed(2)},`,
    `${target.x.toFixed(2)} ${target.y.toFixed(2)}`,
  ].join(" ");
}

export function EvidenceOrbit({
  targetRef,
}: {
  targetRef: RefObject<HTMLElement | null>;
}) {
  const [activeId, setActiveId] = useState<EvidenceId | null>(null);
  const [geometry, setGeometry] = useState<OrbitGeometry | null>(null);
  const rootRef = useRef<HTMLDivElement>(null);
  const nodeRefs = useRef<Partial<Record<EvidenceId, HTMLSpanElement | null>>>(
    {},
  );
  const active = SOURCES.find((source) => source.id === activeId) ?? null;

  const measureGeometry = useCallback(() => {
    const root = rootRef.current;
    const target = targetRef.current;
    if (!root || !target) return;

    const rootRect = root.getBoundingClientRect();
    const targetRect = target.getBoundingClientRect();
    const nodes: Partial<Record<EvidenceId, Point>> = {};

    for (const source of SOURCES) {
      const marker = nodeRefs.current[source.id];
      if (!marker) continue;
      const markerRect = marker.getBoundingClientRect();
      nodes[source.id] = {
        x: markerRect.left + markerRect.width / 2 - rootRect.left,
        y: markerRect.top + markerRect.height / 2 - rootRect.top,
      };
    }

    setGeometry({
      width: rootRect.width,
      height: rootRect.height,
      target: {
        x: targetRect.left + targetRect.width / 2 - rootRect.left,
        y: targetRect.top + targetRect.height / 2 - rootRect.top,
      },
      nodes,
    });
  }, [targetRef]);

  useEffect(() => {
    const frame = window.requestAnimationFrame(measureGeometry);
    const timers = [120, 480, 1000, 1650].map((delay) =>
      window.setTimeout(measureGeometry, delay),
    );
    const observer = new ResizeObserver(measureGeometry);

    if (rootRef.current) observer.observe(rootRef.current);
    if (targetRef.current) observer.observe(targetRef.current);
    window.addEventListener("resize", measureGeometry);

    return () => {
      window.cancelAnimationFrame(frame);
      timers.forEach((timer) => window.clearTimeout(timer));
      observer.disconnect();
      window.removeEventListener("resize", measureGeometry);
    };
  }, [measureGeometry, targetRef]);

  useEffect(() => {
    if (!activeId) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setActiveId(null);
    };
    const onPointerDown = (event: PointerEvent) => {
      const target = event.target as HTMLElement;
      if (
        !target.closest("[data-evidence-surface]") &&
        !target.closest("[data-evidence-trigger]")
      ) {
        setActiveId(null);
      }
    };

    document.addEventListener("keydown", onKeyDown);
    document.addEventListener("pointerdown", onPointerDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.removeEventListener("pointerdown", onPointerDown);
    };
  }, [activeId]);

  const activePoint = active ? geometry?.nodes[active.id] : null;
  const cardWidth = geometry ? Math.min(330, geometry.width - 24) : 330;
  const cardPosition =
    active && activePoint && geometry
      ? {
          left: clamp(
            active.side === "left"
              ? activePoint.x - 37
              : activePoint.x - cardWidth + 37,
            12,
            Math.max(12, geometry.width - cardWidth - 12),
          ),
          top: Math.max(12, activePoint.y - 37),
          width: cardWidth,
        }
      : null;

  return (
    <div
      ref={rootRef}
      className="pointer-events-none absolute inset-0 z-[15]"
      aria-label="Documented memory problems"
    >
      {geometry ? (
        <svg
          aria-hidden
          viewBox={`0 0 ${geometry.width} ${geometry.height}`}
          preserveAspectRatio="none"
          className="absolute inset-0 size-full"
        >
          <defs>
            {SOURCES.map((source) => {
              const start = geometry.nodes[source.id];
              if (!start) return null;
              return (
                <linearGradient
                  key={source.id}
                  id={`trace-${source.id}`}
                  gradientUnits="userSpaceOnUse"
                  x1={start.x}
                  y1={start.y}
                  x2={geometry.target.x}
                  y2={geometry.target.y}
                >
                  <stop offset="0" stopColor={source.accent} stopOpacity="0" />
                  <stop
                    offset=".16"
                    stopColor={source.accent}
                    stopOpacity=".35"
                  />
                  <stop
                    offset=".7"
                    stopColor="#6faaa8"
                    stopOpacity=".42"
                  />
                  <stop
                    offset="1"
                    stopColor="#d6e8e4"
                    stopOpacity=".72"
                  />
                </linearGradient>
              );
            })}
            <filter
              id="trace-glow"
              x="-20%"
              y="-20%"
              width="140%"
              height="140%"
            >
              <feGaussianBlur stdDeviation="2.2" />
            </filter>
          </defs>

          {SOURCES.map((source, index) => {
            const start = geometry.nodes[source.id];
            if (!start) return null;
            const selected = source.id === activeId;
            const path = buildPath(
              source,
              start,
              geometry.target,
              geometry.width,
            );
            return (
              <g key={source.id}>
                <path
                  d={path}
                  fill="none"
                  stroke={source.accent}
                  strokeWidth={selected ? 4 : 2}
                  opacity={selected ? 0.1 : 0.018}
                  filter="url(#trace-glow)"
                  vectorEffect="non-scaling-stroke"
                  className="transition-all duration-500"
                />
                <motion.path
                  d={path}
                  fill="none"
                  stroke={`url(#trace-${source.id})`}
                  strokeWidth={selected ? 1.15 : 0.58}
                  strokeDasharray={selected ? "4 7" : "2 11"}
                  strokeLinecap="round"
                  vectorEffect="non-scaling-stroke"
                  initial={{ opacity: 0, pathLength: 0 }}
                  animate={{
                    opacity: selected ? 0.74 : 0.2,
                    pathLength: 1,
                    strokeDashoffset: -52,
                  }}
                  transition={{
                    opacity: { duration: 0.4 },
                    pathLength: {
                      duration: 1.15,
                      delay: 0.07 * index,
                      ease: [0.22, 1, 0.36, 1],
                    },
                    strokeDashoffset: {
                      duration: 7 + index * 0.65,
                      repeat: Number.POSITIVE_INFINITY,
                      ease: "linear",
                    },
                  }}
                />
              </g>
            );
          })}
        </svg>
      ) : null}

      <LayoutGroup id="evidence-orbit">
        {SOURCES.map((source) => {
          return (
            <div
              key={source.id}
              className={`pointer-events-none absolute z-20 w-40 -translate-x-1/2 ${source.position}`}
            >
              <span
                ref={(element) => {
                  nodeRefs.current[source.id] = element;
                }}
                aria-hidden
                className="absolute left-1/2 top-[22px] size-px -translate-x-1/2 opacity-0 sm:top-[24px]"
              />
              {source.id !== activeId ? (
                <motion.button
                  layoutId={`evidence-surface-${source.id}`}
                  data-evidence-trigger
                  type="button"
                  onClick={() => setActiveId(source.id)}
                  aria-label={`Show ${source.name} evidence`}
                  whileHover={{
                    rotateX: 5,
                    rotateY: source.side === "left" ? 5 : -5,
                    scale: 1.04,
                  }}
                  transition={{
                    type: "spring",
                    stiffness: 420,
                    damping: 32,
                    mass: 0.7,
                  }}
                  className="group pointer-events-auto mx-auto flex flex-col items-center gap-1.5 rounded-2xl opacity-[0.3] outline-none transition-opacity duration-500 [transform-style:preserve-3d] hover:opacity-90 focus-visible:opacity-100"
                >
                  <motion.span
                    layoutId={`evidence-mark-${source.id}`}
                    className="relative grid size-11 place-items-center rounded-2xl border border-white/[0.08] bg-[#070a0b]/90 backdrop-blur-sm transition duration-500 [transform:translateZ(16px)] group-hover:border-white/25 group-hover:shadow-[0_15px_35px_-18px_var(--orbit-accent)] sm:size-12"
                    style={
                      {
                        "--orbit-accent": source.accent,
                      } as CSSProperties
                    }
                  >
                    <SourceMark id={source.id} />
                  </motion.span>
                  <span className="hidden whitespace-nowrap text-[10px] font-semibold tracking-[0.025em] text-ink-2 sm:block">
                    {source.name}
                  </span>
                  <span className="hidden whitespace-nowrap text-[7px] uppercase tracking-[0.15em] text-ink-4 md:block">
                    {source.issue}
                  </span>
                </motion.button>
              ) : null}
            </div>
          );
        })}

        <AnimatePresence mode="popLayout">
          {active && cardPosition ? (
            <motion.aside
              layoutId={`evidence-surface-${active.id}`}
              data-evidence-surface
              key={active.id}
              initial={{ opacity: 0.82 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0.78 }}
              transition={{
                type: "spring",
                stiffness: 420,
                damping: 34,
                mass: 0.76,
              }}
              className="pointer-events-auto absolute z-40 overflow-hidden rounded-[22px] border border-white/[0.13] bg-[#080b0d]/95 p-5 text-left shadow-[0_30px_90px_-38px_rgba(0,0,0,1)] backdrop-blur-xl"
              style={cardPosition}
              role="dialog"
              aria-label={`${active.name} documented evidence`}
            >
              <div
                aria-hidden
                className="absolute inset-x-8 top-0 h-px"
                style={{
                  background: `linear-gradient(90deg, transparent, ${active.accent}, transparent)`,
                }}
              />
              <button
                type="button"
                onClick={() => setActiveId(null)}
                aria-label="Close evidence"
                className={`absolute top-3 text-[17px] text-ink-4 transition hover:text-white ${
                  active.side === "left" ? "right-4" : "left-4"
                }`}
              >
                ×
              </button>
              <div
                className={`flex items-center gap-2.5 ${
                  active.side === "left"
                    ? "pr-7"
                    : "flex-row-reverse justify-start pl-7 text-right"
                }`}
              >
                <motion.span
                  layoutId={`evidence-mark-${active.id}`}
                  className="grid size-8 shrink-0 place-items-center rounded-xl border border-white/10 bg-black/25"
                >
                  <SourceMark id={active.id} />
                </motion.span>
                <p className="text-[9px] font-semibold uppercase tracking-[0.16em] text-ink-4">
                  {active.name} · documented
                </p>
              </div>
              <h3 className="mt-3 text-[22px] font-medium leading-[1.04] tracking-[-0.03em] text-white">
                {active.headline}
              </h3>
              <p
                className="mt-4 border-l pl-3 text-[11.5px] italic leading-[1.55] text-ink-2"
                style={{ borderColor: active.accent }}
              >
                {active.proof}
              </p>
              <a
                href={active.sourceUrl}
                target="_blank"
                rel="noreferrer"
                className="group mt-5 inline-flex items-center gap-2 text-[10.5px] font-semibold text-white underline decoration-white/20 underline-offset-4 transition hover:decoration-white/70"
              >
                {active.sourceLabel}
                <span className="transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5">
                  ↗
                </span>
              </a>
            </motion.aside>
          ) : null}
        </AnimatePresence>
      </LayoutGroup>
    </div>
  );
}
