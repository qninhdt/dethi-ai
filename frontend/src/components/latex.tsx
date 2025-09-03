"use client";

import "katex/dist/katex.min.css";
import LibLaTeX from "react-latex-next";

export function LaTeX({ children }: { children: string }) {
  return <LibLaTeX>{children}</LibLaTeX>;
}
