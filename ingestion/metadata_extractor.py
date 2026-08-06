"""
Metadata Extractor

Adds normalized document and section metadata to built sections.

Responsibilities
----------------
- Extract stable document metadata
- Extract policy identifiers such as UIN
- Infer policy name and policy type
- Attach section metadata needed by chunking, indexing, filtering, and citations

Does NOT
---------
- Read PDFs directly
- Build sections
- Chunk documents
- Create embeddings
"""

import hashlib
import re
from pathlib import Path
from typing import Any

from loguru import logger

from utils.document_line import DocumentLine
from utils.document_section import DocumentSection


class MetadataExtractor:
    def enrich_sections(
        self,
        sections: list[DocumentSection],
        lines: list[DocumentLine] | None = None,
    ) -> list[DocumentSection]:
        """
        Enrich sections in place and return the same list for pipeline chaining.
        """
        logger.info("Extracting section metadata...")

        document_metadata = self._build_document_metadata(sections, lines)
        section_counters: dict[str, int] = {}

        for section in sections:
            document_id = section.document_id or self._fallback_document_id(section)
            section_counters[document_id] = section_counters.get(document_id, 0) + 1
            section_index = section_counters[document_id]

            metadata = {
                **document_metadata.get(document_id, {}),
                "section_id": self._section_id(document_id, section_index, section.title),
                "section_index": section_index,
                "section_title": self._clean_text(section.title),
                "section_type": section.section_type,
                "start_page": section.start_page,
                "end_page": section.end_page,
                "page_range": f"{section.start_page}-{section.end_page}",
                "line_count": len(section.lines),
                "section_text_hash": self._text_hash(self._section_text(section)),
            }

            section.metadata = metadata

        logger.success(f"Metadata extracted for {len(sections)} section(s).")

        return sections

    def to_metadata_dicts(
        self,
        sections: list[DocumentSection],
    ) -> list[dict[str, Any]]:
        """
        Return serializable metadata dictionaries for downstream inspection/tests.
        """
        return [section.metadata for section in sections]

    def _build_document_metadata(
        self,
        sections: list[DocumentSection],
        lines: list[DocumentLine] | None = None,
    ) -> dict[str, dict[str, Any]]:
        lines_by_document: dict[str, list[DocumentLine]] = {}
        section_by_document: dict[str, DocumentSection] = {}

        for section in sections:
            document_id = section.document_id or self._fallback_document_id(section)
            section_by_document.setdefault(document_id, section)
            lines_by_document.setdefault(document_id, []).extend(section.lines)

        if lines is not None:
            for line in lines:
                document_id = line.document_id or line.source_key
                lines_by_document[document_id] = []

            for line in lines:
                document_id = line.document_id or line.source_key
                lines_by_document.setdefault(document_id, []).append(line)

        metadata_by_document = {}

        for document_id, lines in lines_by_document.items():
            section = section_by_document[document_id]
            source_file = section.source_file or self._first_value(lines, "source_file")
            file_path = section.file_path or self._first_value(lines, "file_path")
            company = section.company or self._first_value(lines, "company") or "Unknown"
            company_key = section.company_key or self._first_value(lines, "company_key")
            policy_name = self._policy_name(lines, source_file)

            metadata_by_document[document_id] = {
                "document_id": document_id,
                "company": company,
                "company_key": company_key,
                "source_file": source_file,
                "file_path": file_path,
                "policy_name": policy_name,
                "policy_type": self._policy_type(policy_name, lines),
                "uin": self._uin(lines),
                "total_pages": self._total_pages(lines),
            }

        return metadata_by_document

    def _fallback_document_id(self, section: DocumentSection) -> str:
        if section.file_path:
            return str(Path(section.file_path))

        if section.source_file:
            return section.source_file

        return "unknown-document"

    def _section_id(
        self,
        document_id: str,
        section_index: int,
        section_title: str,
    ) -> str:
        digest = hashlib.sha1(
            f"{document_id}:{section_index}:{section_title}".encode("utf-8")
        ).hexdigest()[:12]

        return f"{document_id}:section:{section_index:03d}:{digest}"

    def _policy_name(
        self,
        lines: list[DocumentLine],
        source_file: str,
    ) -> str:
        title = self._best_title_candidate(lines)

        if title:
            return self._clean_text(title)

        if source_file:
            return Path(source_file).stem.replace("_", " ").replace("-", " ").title()

        return "Unknown Policy"

    def _best_title_candidate(
        self,
        lines: list[DocumentLine],
    ) -> str:
        candidates = []

        for line in lines:
            text = self._clean_text(line.text)

            if not text or len(text) > 140:
                continue

            if self._is_noise_title(text):
                continue

            if line.role in {"DOCUMENT_TITLE", "DOCUMENT_SUBTITLE"}:
                candidates.append(
                    (0, self._title_case_rank(text), -line.font_size, line.page, line.bbox[1], text)
                )
                continue

            if line.is_bold and line.font_size >= 9.5:
                candidates.append(
                    (1, self._title_case_rank(text), -line.font_size, line.page, line.bbox[1], text)
                )
                continue

            if line.font_size >= 14:
                candidates.append(
                    (2, self._title_case_rank(text), -line.font_size, line.page, line.bbox[1], text)
                )

        if not candidates:
            return ""

        candidates.sort()

        return candidates[0][-1]

    def _title_case_rank(self, text: str) -> int:
        if text.isupper() and len(text.split()) <= 8:
            return 0

        return 1

    def _is_noise_title(self, text: str) -> bool:
        lowered = text.lower()

        if lowered.startswith(("section ", "uin", "cin", "page ")):
            return True

        if re.match(r"^[a-z]\.\s+", lowered):
            return True

        if re.match(r"^\d+(\.\d+)*[.)]?\s+", lowered):
            return True

        noisy_phrases = {
            "policy wording",
            "office details",
            "jurisdiction of office",
            "annexure a",
            "preamble",
        }

        if lowered in noisy_phrases:
            return True

        if "claim related queries" in lowered:
            return True

        return False

    def _policy_type(
        self,
        policy_name: str,
        lines: list[DocumentLine],
    ) -> str:
        sample_text = " ".join(
            [policy_name] + [line.text for line in lines[:100]]
        ).lower()

        if "add on" in sample_text or "rider" in sample_text:
            return "Rider"

        if "travel" in sample_text:
            return "Travel Insurance"

        if "health" in sample_text or "hospital" in sample_text or "medical" in sample_text:
            return "Health Insurance"

        return "Unknown"

    def _uin(self, lines: list[DocumentLine]) -> str:
        for line in lines:
            match = re.search(r"\bUIN\s*[:\-]\s*([A-Z0-9]+)", line.text, re.IGNORECASE)

            if match:
                return match.group(1)

        return ""

    def _total_pages(self, lines: list[DocumentLine]) -> int:
        if not lines:
            return 0

        return max(line.page for line in lines) + 1

    def _first_value(
        self,
        lines: list[DocumentLine],
        attribute: str,
    ) -> str:
        for line in lines:
            value = getattr(line, attribute, "")

            if value:
                return value

        return ""

    def _first_line_text(
        self,
        lines: list[DocumentLine],
        roles: set[str],
    ) -> str:
        for line in lines:
            if line.role in roles and line.text.strip():
                return line.text

        return ""

    def _section_text(self, section: DocumentSection) -> str:
        return "\n".join(line.text for line in section.lines)

    def _text_hash(self, text: str) -> str:
        return hashlib.sha1(text.encode("utf-8")).hexdigest()

    def _clean_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()
