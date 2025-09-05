"use client";

import LibMarkdown from "react-markdown";
import rehypeKatex from "rehype-katex";
import remarkMath from "remark-math";
import "katex/dist/katex.min.css";

export function Markdown({ children }: { children: string }) {
  if (!children) return null;
  return (
    <LibMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
      {children}
    </LibMarkdown>
  );
}
