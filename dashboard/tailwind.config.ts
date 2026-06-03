import type { Config } from "tailwindcss";

/**
 * Ferryte — tokens
 *
 * Black canvas. Geist sans + Geist mono. Brand teal-steel gradient drawn
 * from the Ferryte mark itself: a deep cyan-slate, a calm steel-blue mid,
 * and a foggy near-white highlight.
 *
 * The semantic name `royal` is preserved across the codebase but now points
 * to the mid-tone of the brand gradient — every existing `bg-royal`,
 * `text-royal`, `dot-royal` instance picks up the new identity for free.
 */
const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        black: "#000000",
        canvas: "#000000",
        surface: "#0a0a0a",
        "surface-2": "#101010",
        "surface-3": "#161616",
        ink: "#fafafa",
        "ink-2": "#a0a0a0",
        "ink-3": "#666666",
        "ink-4": "#3d3d3d",
        rule: "#1a1a1a",
        "rule-2": "#262626",

        // Brand gradient stops sampled from the Ferryte mark.
        "brand-deep": "#0d3d4e",   // darkest cyan-slate
        "brand-mid": "#5a8a96",    // calm steel-blue (recognisable mid)
        "brand-light": "#9bb8b8",  // foggy upper highlight
        "brand-haze": "#bfd1ce",   // near-white tip

        // Semantic alias — `royal` keeps every existing class working.
        royal: "#5a8a96",
        "royal-2": "#7ea7b0",
        ok: "#10b981",
        pending: "#d97706",
        issue: "#dc2626",
      },
      fontFamily: {
        sans: ["var(--font-geist-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["var(--font-geist-mono)", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      fontSize: {
        // Apple-ish scale: huge display, generous body, tiny labels.
        "label": ["11px", { lineHeight: "1", letterSpacing: "0.06em" }],
        "caption": ["12px", { lineHeight: "1.4", letterSpacing: "-0.005em" }],
        "body": ["14.5px", { lineHeight: "1.55", letterSpacing: "-0.011em" }],
        "lede": ["17px", { lineHeight: "1.5", letterSpacing: "-0.014em" }],
        "h3": ["22px", { lineHeight: "1.2", letterSpacing: "-0.022em" }],
        "h2": ["32px", { lineHeight: "1.1", letterSpacing: "-0.028em" }],
        "h1": ["56px", { lineHeight: "1.02", letterSpacing: "-0.038em" }],
        "display": ["88px", { lineHeight: "0.96", letterSpacing: "-0.045em" }],
      },
      letterSpacing: {
        tightest: "-0.038em",
      },
      borderRadius: {
        sm: "6px",
        md: "10px",
        lg: "14px",
        xl: "20px",
      },
      transitionTimingFunction: {
        out: "cubic-bezier(0.22, 1, 0.36, 1)",
        precise: "cubic-bezier(0.2, 0, 0, 1)",
      },
      transitionDuration: {
        fast: "140ms",
        base: "220ms",
        slow: "420ms",
      },
    },
  },
  plugins: [],
};
export default config;
