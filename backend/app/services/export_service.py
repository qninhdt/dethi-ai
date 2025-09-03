import logging
import os
import subprocess
import tempfile
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


def build_latex_from_exam(exam: Dict) -> str:
    preamble = r"""\documentclass{article}
\usepackage[utf8]{inputenc}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{graphicx}
\usepackage[utf8]{vietnam}
\begin{document}
"""
    postamble = "\n\\end{document}\n"

    body: List[str] = []
    body.append(f"\\section*{{{exam['metadata'].get('title', 'Exam')}}}")

    question_number = 1
    for el in exam["elements"]:
        if el.get("type") == "text":
            body.append(el.get("content", ""))
        elif el.get("type") == "multiple_choice":
            body.append(f"\\paragraph{{Question {question_number}}} {el['content']}")
            opts = el.get("data", {}).get("options", [])
            body.append("\\begin{enumerate}")
            for o in opts:
                body.append(f"  \\item {o}")
            body.append("\\end{enumerate}")
            if "answer" in el and el["answer"]:
                ans = el["answer"]
                body.append("\\textbf{Answer:} ")
                body.append(f"Option: {ans.get('selected_options', 0) + 1}")
                if ans.get("explanation"):
                    body.append("\\paragraph{Explanation} " + ans["explanation"])
            question_number += 1
        elif el.get("type") == "true_false":
            body.append(f"\\paragraph{{Question {question_number}}} {el['content']}")
            clauses = el.get("data", {}).get("clauses", [])
            body.append("\\begin{enumerate}")
            for c in clauses:
                body.append(f"  \\item {c}")
            body.append("\\end{enumerate}")
            if "answer" in el and el["answer"]:
                ans = el["answer"]
                tf = [
                    "True" if b else "False" for b in ans.get("clause_correctness", [])
                ]
                body.append("\\textbf{Answers:} " + ", ".join(tf))
                if ans.get("general_explanation"):
                    body.append(
                        "\\paragraph{Explanation} " + ans["general_explanation"]
                    )
            question_number += 1
        elif el.get("type") == "short_answer":
            body.append(f"\\paragraph{{Question {question_number}}} {el['content']}")
            if "answer" in el and el["answer"]:
                ans = el["answer"]
                body.append("\\textbf{Answer:} " + ans.get("answer_text", ""))
                if ans.get("explanation"):
                    body.append("\\paragraph{Explanation} " + ans["explanation"])
            question_number += 1

    return preamble + "\n\n".join(body) + postamble


def compile_pdf(tex_path: str) -> str:
    workdir = os.path.dirname(tex_path)
    name = os.path.splitext(os.path.basename(tex_path))[0]
    try:
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", name + ".tex"],
            cwd=workdir,
            check=True,
            capture_output=True,
            text=True,
        )
        return os.path.join(workdir, name + ".pdf")
    except FileNotFoundError:
        logger.error("pdflatex not found. Please install TeX Live.")
        raise
    except subprocess.CalledProcessError as e:
        logger.error("pdflatex failed: %s", e.stderr)
        raise
