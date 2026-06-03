import { type HTMLAttributes, type ReactNode } from "react";

interface SurfaceProps extends HTMLAttributes<HTMLDivElement> {
  inset?: boolean;
  bordered?: boolean;
  children?: ReactNode;
}

/**
 * A single, restrained surface. Pure black with the tiniest hairline border.
 * Use it sparingly — most of the UI is just type on the canvas.
 */
export function Surface({
  inset = false,
  bordered = true,
  className = "",
  children,
  ...rest
}: SurfaceProps) {
  return (
    <div
      className={[
        "rounded-lg",
        bordered ? "border border-rule" : "",
        inset ? "bg-surface" : "bg-black",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      {...rest}
    >
      {children}
    </div>
  );
}
