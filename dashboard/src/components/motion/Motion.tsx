"use client";

import { motion, useInView, type Variants } from "framer-motion";
import { type ReactNode, useRef } from "react";

const EASE = [0.22, 1, 0.36, 1] as const;

/**
 * Reveal — fades + translates upward on first paint.
 * For above-the-fold content (hero).
 */
export function Reveal({
  children,
  delay = 0,
  duration = 0.7,
  className,
}: {
  children: ReactNode;
  delay?: number;
  duration?: number;
  className?: string;
}) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 18, filter: "blur(8px)" }}
      animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
      transition={{ duration, delay, ease: EASE }}
    >
      {children}
    </motion.div>
  );
}

/**
 * RevealOnScroll — same animation, but triggered when the element enters the viewport.
 * For below-the-fold content.
 */
export function RevealOnScroll({
  children,
  delay = 0,
  duration = 0.8,
  className,
  once = true,
  amount = 0.25,
}: {
  children: ReactNode;
  delay?: number;
  duration?: number;
  className?: string;
  once?: boolean;
  amount?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once, amount });

  return (
    <motion.div
      ref={ref}
      className={className}
      initial={{ opacity: 0, y: 28, filter: "blur(8px)" }}
      animate={
        inView
          ? { opacity: 1, y: 0, filter: "blur(0px)" }
          : { opacity: 0, y: 28, filter: "blur(8px)" }
      }
      transition={{ duration, delay, ease: EASE }}
    >
      {children}
    </motion.div>
  );
}

/**
 * Stagger — animates children with a delay between each.
 * Children should be wrapped in <StaggerItem> for the effect to apply.
 */
export function Stagger({
  children,
  className,
  delay = 0,
  staggerDelay = 0.08,
  once = true,
  amount = 0.25,
}: {
  children: ReactNode;
  className?: string;
  delay?: number;
  staggerDelay?: number;
  once?: boolean;
  amount?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once, amount });

  const containerVariants: Variants = {
    hidden: {},
    visible: {
      transition: {
        delayChildren: delay,
        staggerChildren: staggerDelay,
      },
    },
  };

  return (
    <motion.div
      ref={ref}
      className={className}
      variants={containerVariants}
      initial="hidden"
      animate={inView ? "visible" : "hidden"}
    >
      {children}
    </motion.div>
  );
}

export function StaggerItem({
  children,
  className,
  yOffset = 18,
}: {
  children: ReactNode;
  className?: string;
  yOffset?: number;
}) {
  const itemVariants: Variants = {
    hidden: { opacity: 0, y: yOffset, filter: "blur(6px)" },
    visible: {
      opacity: 1,
      y: 0,
      filter: "blur(0px)",
      transition: { duration: 0.7, ease: EASE },
    },
  };

  return (
    <motion.div className={className} variants={itemVariants}>
      {children}
    </motion.div>
  );
}

/**
 * WordReveal — splits text into words, animates each in sequence.
 * Pure brand drama; use sparingly (hero headlines only).
 */
export function WordReveal({
  text,
  className,
  delay = 0,
  staggerDelay = 0.05,
  as: Tag = "span",
}: {
  text: string;
  className?: string;
  delay?: number;
  staggerDelay?: number;
  as?: "span" | "h1" | "h2" | "h3" | "p" | "div";
}) {
  const words = text.split(" ");

  const containerVariants: Variants = {
    hidden: {},
    visible: {
      transition: {
        delayChildren: delay,
        staggerChildren: staggerDelay,
      },
    },
  };

  const wordVariants: Variants = {
    hidden: { opacity: 0, y: "0.4em", filter: "blur(6px)" },
    visible: {
      opacity: 1,
      y: 0,
      filter: "blur(0px)",
      transition: { duration: 0.65, ease: EASE },
    },
  };

  const MotionTag = motion[Tag] as typeof motion.span;

  return (
    <MotionTag
      className={className}
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      aria-label={text}
    >
      {words.map((word, i) => (
        <motion.span
          key={i}
          variants={wordVariants}
          aria-hidden="true"
          style={{ display: "inline-block", marginRight: "0.25em" }}
        >
          {word}
        </motion.span>
      ))}
    </MotionTag>
  );
}

/**
 * Magnetic — subtle scale + lift on hover. For primary CTAs only.
 */
export function Magnetic({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <motion.div
      className={className}
      whileHover={{ scale: 1.02, y: -1 }}
      whileTap={{ scale: 0.985 }}
      transition={{ duration: 0.22, ease: EASE }}
    >
      {children}
    </motion.div>
  );
}
