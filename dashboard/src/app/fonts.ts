import { GeistMono } from "geist/font/mono";
import { GeistSans } from "geist/font/sans";
import { Fraunces, Instrument_Serif } from "next/font/google";

export const sans = GeistSans;
export const mono = GeistMono;

/**
 * The landing-page voice: a high-character variable serif with optical sizing
 * and soft/wonk axes. The product interface remains in Geist.
 */
export const fraunces = Fraunces({
  subsets: ["latin"],
  style: ["normal", "italic"],
  variable: "--font-fraunces",
  display: "swap",
  axes: ["opsz", "SOFT", "WONK"],
});

/**
 * The story voice. Used ONLY for narrative moments — incident quotes, the
 * villain statement's key phrases, bestiary stings. Facts stay in mono,
 * interface stays in Geist. One weight, both styles, latin subset — ~28KB.
 */
export const serif = Instrument_Serif({
  weight: "400",
  style: ["normal", "italic"],
  subsets: ["latin"],
  variable: "--font-serif",
  display: "swap",
});
