import logging
import os
import subprocess
import tempfile
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


def build_markdown_from_exam(exam: Dict) -> str:
    body: List[str] = []
    answers: List[str] = []
    body.append(f"# {exam['metadata'].get('title', 'Exam')}")

    # pandoc settings
    settings = [
        "mainfont: 'Times New Roman'",
    ]

    question_number = 1
    for el in exam.get("elements", []):
        t = el.get("type")
        if t == "text":
            body.append(el.get("content", ""))
        elif t == "multiple_choice":
            body.append(f"**Câu {question_number}:** {el['content']}")
            opts = el.get("data", {}).get("options", [])
            for i, o in enumerate(opts):
                body.append(f"{chr(65 + i)}. {o}")

            # collect answer/explanation to append later
            if el.get("answer"):
                ans = el["answer"]
                ans_lines: List[str] = []
                ans_lines.append(f"**Câu {question_number}:**")
                ans_lines.append(
                    f"**Đáp án:** {chr(65 + ans.get('correct_option', 0))}"
                )
                if ans.get("explanation"):
                    ans_lines.append("**Lời giải:**")
                    ans_lines.append(ans["explanation"])

                if ans.get("error_analysis"):
                    ans_lines.append("**Tại sao các đáp án khác sai:**")
                    correct_option = ans.get("correct_option", 0)
                    for i, err in enumerate(ans.get("error_analysis", [])):
                        if i != correct_option:
                            option_letter = chr(65 + i)
                            ans_lines.append(f"- **{option_letter}.** {err}")

                answers.append("\n\n".join(ans_lines))

            question_number += 1
        elif t == "true_false":
            body.append(f"**Câu {question_number}:** {el['content']}")
            clauses = el.get("data", {}).get("clauses", [])
            for i, c in enumerate(clauses, 1):
                body.append(f"{i}. {c}")

            if el.get("answer"):
                ans = el["answer"]
                ans_lines: List[str] = []
                tf = ["Đúng" if b else "Sai" for b in ans.get("clause_correctness", [])]
                ans_lines.append(f"**Câu {question_number}:**")
                ans_lines.append(f"**Đáp án:** " + ", ".join(tf))
                if ans.get("general_explanation"):
                    ans_lines.append("**Lời giải:**")
                    ans_lines.append(ans["general_explanation"])

                if ans.get("explanations"):
                    ans_lines.append("**Giải thích chi tiết:**")
                    for i, exp in enumerate(ans.get("explanations", [])):
                        ans_lines.append(f"- **Mệnh đề {i+1}**")
                        ans_lines.append(ans["explanations"][i])

                answers.append("\n\n".join(ans_lines))

            question_number += 1
        elif t == "short_answer":
            body.append(f"**Câu {question_number}:** {el['content']}")
            if el.get("answer"):
                ans = el["answer"]
                ans_lines: List[str] = []
                ans_lines.append(f"**Câu {question_number}:**")
                ans_lines.append(f"**Đáp án:** " + ans.get("answer_text", ""))
                if ans.get("explanation"):
                    ans_lines.append("**Lời giải:**")
                    ans_lines.append(ans["explanation"])
                answers.append("\n\n".join(ans_lines))

            question_number += 1
        else:
            # unknown element types: include content if present
            if el.get("content"):
                body.append(el.get("content", ""))

    # build postamble with all collected answers/explanations
    if answers:
        postamble_lines: List[str] = []
        postamble_lines.append("# Đáp án và lời giải")
        postamble_lines.extend(["", *answers])
        postamble = "\n\n\n".join(postamble_lines)

    # final assembly
    markdown = "\n".join([f"---\n{line}\n---" for line in settings]) + "\n\n"
    markdown = markdown + "\n\n\n".join(body)
    if answers:
        markdown += "\n\n" + "\\newpage" + "\n\n" + postamble
    return markdown


def compile_pdf(md_path: str) -> str:
    workdir = os.path.dirname(md_path)
    name = os.path.splitext(os.path.basename(md_path))[0]
    try:
        subprocess.run(
            ["pandoc", "-o", name + ".pdf", name + ".md", "--pdf-engine=xelatex"],
            cwd=workdir,
            check=True,
            capture_output=True,
            text=True,
        )
        return os.path.join(workdir, name + ".pdf")
    except FileNotFoundError:
        logger.error("pandoc not found. Please install Pandoc.")
        raise
    except subprocess.CalledProcessError as e:
        logger.error("pandoc failed: %s", e.stderr)
        raise


def compile_docx(md_path: str) -> str:
    workdir = os.path.dirname(md_path)
    name = os.path.splitext(os.path.basename(md_path))[0]
    try:
        subprocess.run(
            ["pandoc", "-o", name + ".docx", name + ".md"],
            cwd=workdir,
            check=True,
            capture_output=True,
            text=True,
        )
        return os.path.join(workdir, name + ".docx")
    except FileNotFoundError:
        logger.error("pandoc not found. Please install Pandoc.")
        raise
    except subprocess.CalledProcessError as e:
        logger.error("pandoc failed: %s", e.stderr)
        raise
