"""
Layout Analyzer

Extracts logical text lines from PDF documents using PyMuPDF.

Responsibilities
----------------
- Read PDFs
- Extract text lines
- Preserve font information
- Preserve layout information

Does NOT
---------
- Detect headings
- Build sections
- Chunk documents
"""

from pathlib import Path

import fitz
from loguru import logger

from config.constants import COMPANY_MAPPING
from config.settings import settings
from utils.document_line import DocumentLine


class LayoutAnalyzer:
    def __init__(self):
        self.raw_path = Path(settings.RAW_DATA_PATH)

    def analyze(self) -> list[DocumentLine]:
        lines = []

        pdf_files = list(self.raw_path.rglob("*.pdf"))

        logger.info(f"Analyzing {len(pdf_files)} PDF(s)...")

        for pdf_path in pdf_files:
            lines.extend(self.analyze_document(pdf_path))

        logger.success(f"Extracted {len(lines)} document lines.")

        return lines

    def analyze_document(self, pdf_path: str | Path) -> list[DocumentLine]:
        pdf_path = Path(pdf_path)

        company_key = pdf_path.parent.name.lower()

        company_name = COMPANY_MAPPING.get(company_key, company_key)

        document_id = f"{company_key}:{pdf_path.stem}"

        lines = []

        logger.info(f"Reading {pdf_path.name}")

        pdf = fitz.open(pdf_path)

        for page_number in range(len(pdf)):

            page = pdf[page_number]

            page_dict = page.get_text("dict")

            for block_no, block in enumerate(page_dict["blocks"]):

                if "lines" not in block:
                    continue

                for line_no, line in enumerate(block["lines"]):

                    line_text = ""

                    font_size = 0

                    font_name = ""

                    is_bold = False

                    x0 = y0 = x1 = y1 = None

                    for span in line["spans"]:

                        text = span["text"].strip()

                        if not text:
                            continue

                        if line_text:
                            line_text += " "

                        line_text += text

                        font_size = max(font_size, span["size"])

                        font_name = span["font"]

                        if "Bold" in span["font"]:
                            is_bold = True

                        sx0, sy0, sx1, sy1 = span["bbox"]

                        if x0 is None:
                            x0, y0, x1, y1 = sx0, sy0, sx1, sy1
                        else:
                            x0 = min(x0, sx0)
                            y0 = min(y0, sy0)
                            x1 = max(x1, sx1)
                            y1 = max(y1, sy1)

                    if not line_text:
                        continue

                    lines.append(
                        DocumentLine(
                            text=line_text,
                            page=page_number,
                            bbox=(x0, y0, x1, y1),
                            font_size=font_size,
                            font_name=font_name,
                            is_bold=is_bold,
                            block_no=block_no,
                            line_no=line_no,
                            document_id=document_id,
                            company=company_name,
                            company_key=company_key,
                            source_file=pdf_path.name,
                            file_path=str(pdf_path),
                        )
                    )

        pdf.close()

        return lines
