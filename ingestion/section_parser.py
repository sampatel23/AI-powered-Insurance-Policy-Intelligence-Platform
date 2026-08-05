"""
Section Parser

Identifies logical section headings in insurance policy documents.

Responsibilities:
- Detect section headings
- Assign section names to pages

Does NOT:
- Chunk documents
- Clean text
- Generate embeddings
"""

import re

from langchain_core.documents import Document
from loguru import logger


class SectionParser:

    def __init__(self):

        self.heading_patterns = [

            # SECTION A
            r"^SECTION\s+[A-Z]+",

            # CHAPTER 1
            r"^CHAPTER\s+\d+",

            # 1.
            r"^\d+\.\s+[A-Z].+",

            # 1
            r"^\d+\s+[A-Z].+",

            # I.
            r"^[IVXLCDM]+\.\s+[A-Z].+",

            # BENEFITS
            r"^[A-Z][A-Z\s]{3,}$",
        ]

    def is_heading(self, line: str) -> bool:

        line = line.strip()

        if len(line) < 3:
            return False

        for pattern in self.heading_patterns:

            if re.match(pattern, line):
                return True

        return False

    def parse(self, documents: list[Document]) -> list[Document]:

        logger.info("Parsing document sections...")

        current_section = "Unknown"

        for doc in documents:

            lines = doc.page_content.splitlines()

            for line in lines:

                if self.is_heading(line):

                    current_section = line.strip()

                    break

            doc.metadata["section"] = current_section

        logger.success("Section parsing completed.")

        return documents