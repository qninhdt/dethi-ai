"use client";

import "katex/dist/katex.min.css";
import LibLaTeX from "react-latex-next";

export function LaTeX({ children }: { children: string }) {
  if (!children) return null;
  return <LibLaTeX>{children}</LibLaTeX>;
}
