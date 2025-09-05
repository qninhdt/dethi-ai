import base64
import glob
import logging
import os
import subprocess
import tempfile
from typing import List, Optional

import requests

logger = logging.getLogger(__name__)


def convert_to_pdf(input_file: str, output_dir: str) -> Optional[str]:
    logger.info("Converting %s to PDF", input_file)
    try:
        subprocess.run(
            [
                "soffice",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                output_dir,
                input_file,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        pdf_filename = os.path.splitext(os.path.basename(input_file))[0] + ".pdf"
        return os.path.join(output_dir, pdf_filename)
    except FileNotFoundError:
        logger.error("'soffice' command not found. Is LibreOffice installed?")
        return None
    except subprocess.CalledProcessError as e:
        logger.error("Error during PDF conversion: %s", e.stderr)
        return None


def pdf_to_images(pdf_path: str, output_prefix: str) -> List[str]:
    if not pdf_path:
        return []
    logger.info("Converting PDF pages to images: %s", pdf_path)
    try:
        subprocess.run(
            [
                "pdftoppm",
                "-png",
                "-r",
                "300",
                pdf_path,
                output_prefix,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        image_files = sorted(glob.glob(f"{output_prefix}*.png"))
        return image_files
    except FileNotFoundError:
        logger.error("'pdftoppm' not found. Is poppler-utils installed?")
        return []
    except subprocess.CalledProcessError as e:
        logger.error("Error during image conversion: %s", e.stderr)
        return []


def image_to_markdown(image_path: str, api_key: str, model_name: str) -> Optional[str]:
    if not api_key:
        logger.error("OPENROUTER_API_KEY not set")
        return None
    logger.info("Converting image to Markdown: %s", os.path.basename(image_path))
    with open(image_path, "rb") as f:
        base64_image = base64.b64encode(f.read()).decode("utf-8")
    prompt = (
        "Convert a math exam to markdown code. If there is a figure, image, graph, chart or table, just ignore it, do not try to recreate it in Markdown."
        "Math equations must be formatted in valid Markdown, with inline equations enclosed in single dollar signs `$...$` and displayed equations enclosed in double dollar signs `$$...$$`."
        "Output ONLY raw Markdown for this page, no preamble or document wrappers."
    )
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                },
                            },
                        ],
                    }
                ],
            },
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:  # noqa: BLE001
        logger.exception("OCR API request failed: %s", e)
        return None


def ocr_document_to_markdown(
    local_doc_path: str, api_key: str, ocr_model: str
) -> List[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        if local_doc_path.lower().endswith(".pdf"):
            pdf_path = local_doc_path
        else:
            pdf_path = convert_to_pdf(local_doc_path, tmpdir)
        if not pdf_path:
            return []
        prefix = os.path.join(tmpdir, os.path.splitext(os.path.basename(pdf_path))[0])
        images = pdf_to_images(pdf_path, prefix)
        pages: List[str] = []
        for img in images:
            markdown = image_to_markdown(img, api_key, ocr_model)
            if markdown:
                pages.append(markdown)
            else:
                pages.append("% ERROR: OCR failed on page")
        return pages
