import logging
import os
import subprocess
import tempfile
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


def build_latex_from_exam(exam: Dict) -> str:
    preamble = r"""\documentclass{article}
\usepackage[utf8]{inputenc}
\usepackage[margin=2cm]{geometry}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{graphicx}
\usepackage{enumitem}
\usepackage[utf8]{vietnam}
\setlist[itemize]{leftmargin=*, itemindent=0pt, labelsep=0.5em}
\setlist[enumerate]{leftmargin=*, itemindent=0pt, labelsep=0.5em}
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
            body.append(f"\\paragraph{{Câu {question_number}:}} {el['content']}")
            opts = el.get("data", {}).get("options", [])
            body.append("\\begin{enumerate}[label=\\Alph*.]")
            for o in opts:
                body.append(f"  \\item {o}")
            body.append("\\end{enumerate}")
            if "answer" in el and el["answer"]:
                ans = el["answer"]
                body.append(
                    f"\\paragraph{{Đáp án:}} {chr(65 + ans.get('correct_option', 0))}"
                )
                if ans.get("explanation"):
                    body.append("\\paragraph{Lời giải:} " + ans["explanation"])

                if ans.get("error_analysis"):
                    body.append("\\paragraph{Tại sao các đáp án khác sai:}")
                    body.append("\\begin{itemize}")
                    correct_option = ans.get("correct_option", 0)
                    for i, err in enumerate(ans["error_analysis"]):
                        # Skip the correct option
                        if i != correct_option:
                            option_letter = chr(65 + i)  # A, B, C, D
                            body.append(f"\\item \\textbf{{{option_letter}.}} {err}")
                    body.append("\\end{itemize}")
            question_number += 1
        elif el.get("type") == "true_false":
            body.append(f"\\paragraph{{Câu {question_number}:}} {el['content']}")
            clauses = el.get("data", {}).get("clauses", [])
            body.append("\\begin{enumerate}")
            for c in clauses:
                body.append(f"  \\item {c}")
            body.append("\\end{enumerate}")
            if "answer" in el and el["answer"]:
                ans = el["answer"]
                tf = ["Đúng" if b else "Sai" for b in ans.get("clause_correctness", [])]
                body.append("\\textbf{Đáp án:} " + ", ".join(tf))
                if ans.get("general_explanation"):
                    body.append("\\textbf{Lời giải:} " + ans["general_explanation"])
                # Detailed explanations per clause
                if ans.get("explanations"):
                    body.append("\\textbf{Giải thích chi tiết:}")
                    body.append("\\begin{itemize}")
                    for i, exp in enumerate(ans["explanations"]):
                        body.append(f"\\item {clauses[i]}: {exp}")
                    body.append("\\end{itemize}")
            question_number += 1
        elif el.get("type") == "short_answer":
            body.append(f"\\paragraph{{Câu {question_number}:}} {el['content']}")
            if "answer" in el and el["answer"]:
                ans = el["answer"]
                body.append("\\textbf{Answer:} " + ans.get("answer_text", ""))
                if ans.get("explanation"):
                    body.append("\\textbf{Lời giải:} " + ans["explanation"])
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
