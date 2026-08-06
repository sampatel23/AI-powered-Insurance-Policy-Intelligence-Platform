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
            if re.match(r"^SECTION\s+[A-Z](?:(?:[).](?:\s|$))|\s|$)", text, re.IGNORECASE):

                line.role = "SECTION"

                continue

            if (
                line.is_bold
                and re.match(r"^\d+\.\s+[A-Z][A-Z\s&()/,-]+$", text)
            ):

                line.role = "SECTION"

                continue

            if (
                line.company_key == "icici"
                and line.is_bold
                and re.match(
                    r"^[b-f]\.\s+(?:Preamble|Definitions|Benefits covered under the policy|Exclusions)$",
                    text,
                    re.IGNORECASE,
                )
            ):

                line.role = "SECTION"

                continue

            if (
                line.company_key == "icici"
                and line.is_bold
                and text.lower() in {"e.", "f."}
            ):

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
