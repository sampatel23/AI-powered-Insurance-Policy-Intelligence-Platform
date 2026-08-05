"""
Structure Classifier

Classifies every text span into one of the following:

- DOCUMENT_TITLE
- DOCUMENT_SUBTITLE
- SECTION
- SUBSECTION
- BODY
- HEADER
- FOOTER
"""

import re

from loguru import logger

from utils.document_line import DocumentLine

class StructureClassifier:

    def classify(self, lines: list[DocumentLine]) -> list[DocumentLine]:

        logger.info("Classifying document structure...")

        for line in lines:

            text = line.text.strip()

            # -------------------------
            # Header / Footer
            # -------------------------
            if (
                "Page" in text
                or text.startswith("UIN")
                or "Policy Wordings/Page" in text
            ):
                line.role = "HEADER"
                continue

            # -------------------------
            # Main Document Title
            # -------------------------
            if (
                line.font_size >= 13
                and line.is_bold
                and text.isupper()
            ):
                line.role = "DOCUMENT_TITLE"
                continue

            # -------------------------
            # Subtitle
            # -------------------------
            if (
                line.font_size >= 13
                and line.is_bold
            ):
                line.role = "DOCUMENT_SUBTITLE"
                continue

            # -------------------------
            # Section
            # -------------------------
            if re.match(r"^SECTION\s+[A-Z]", text):

                line.role = "SECTION"

                continue

            # -------------------------
            # Numbered subsection
            # -------------------------
            if re.match(r"^\d+(\.\d+)*", text):

                line.role = "SUBSECTION"

                continue

            # -------------------------
            # Bold short sentence
            # -------------------------
            if (
                line.is_bold
                and len(text) < 80
            ):

                line.role = "SUBSECTION"

                continue

            # -------------------------
            # Default
            # -------------------------
            line.role = "BODY"

        logger.success("Structure classification completed.")

        return lines