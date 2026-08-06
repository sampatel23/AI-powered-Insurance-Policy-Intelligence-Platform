"""
Section-Aware Chunker

Builds retrieval-ready chunks from enriched document sections.

Responsibilities
----------------
- Split sections without crossing document or section boundaries
- Prefer subsection boundaries before character-based splitting
- Preserve metadata needed for retrieval, filtering, and citations

Does NOT
---------
- Create embeddings
- Write indexes
- Call LLMs
"""

import hashlib
import re

from loguru import logger

from config.settings import settings
from utils.document_chunk import DocumentChunk
from utils.document_line import DocumentLine
from utils.document_section import DocumentSection


class SectionAwareChunker:
    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    def chunk(
        self,
        sections: list[DocumentSection],
    ) -> list[DocumentChunk]:
        logger.info("Building section-aware chunks...")

        chunks = []

        for section in sections:
            section_chunks = self._chunk_section(section)
            chunks.extend(section_chunks)

        logger.success(f"Built {len(chunks)} chunk(s).")

        return chunks

    def _chunk_section(
        self,
        section: DocumentSection,
    ) -> list[DocumentChunk]:
        if not section.lines:
            return []

        line_groups = []
        current_lines: list[DocumentLine] = []

        for unit in self._subsection_units(section):
            unit_text = self._lines_text(unit)

            if not unit_text:
                continue

            if len(unit_text) > self.chunk_size:
                if current_lines:
                    line_groups.append(current_lines)
                    current_lines = []

                line_groups.extend(
                    self._split_large_unit_lines(
                        unit,
                    )
                )
                continue

            candidate_lines = current_lines + unit
            candidate_text = self._lines_text(candidate_lines)

            if current_lines and len(candidate_text) > self.chunk_size:
                line_groups.append(current_lines)
                current_lines = unit
                continue

            current_lines = candidate_lines

        if current_lines:
            line_groups.append(current_lines)

        line_groups = self._merge_small_groups(line_groups)

        return [
            self._build_chunk(section, lines, index)
            for index, lines in enumerate(line_groups, start=1)
        ]

    def _subsection_units(
        self,
        section: DocumentSection,
    ) -> list[list[DocumentLine]]:
        units = []
        current_unit: list[DocumentLine] = []

        for line in self._content_lines(section.lines):
            if line.role == "SUBSECTION" and current_unit:
                units.append(current_unit)
                current_unit = [line]
                continue

            current_unit.append(line)

        if current_unit:
            units.append(current_unit)

        return units

    def _split_large_unit_lines(
        self,
        lines: list[DocumentLine],
    ) -> list[list[DocumentLine]]:
        line_groups = []
        current_lines: list[DocumentLine] = []

        for line in lines:
            candidate_lines = current_lines + [line]

            if current_lines and len(self._lines_text(candidate_lines)) > self.chunk_size:
                line_groups.append(current_lines)
                current_lines = self._overlap_lines(current_lines) + [line]
                continue

            current_lines = candidate_lines

        if current_lines:
            line_groups.append(current_lines)

        return line_groups

    def _merge_small_groups(
        self,
        line_groups: list[list[DocumentLine]],
    ) -> list[list[DocumentLine]]:
        min_chunk_size = min(300, max(150, int(self.chunk_size * 0.3)))
        merged_groups: list[list[DocumentLine]] = []

        for group in line_groups:
            group_text = self._lines_text(group)

            if (
                merged_groups
                and len(group_text) < min_chunk_size
                and len(self._lines_text(merged_groups[-1] + group)) <= self.chunk_size
            ):
                merged_groups[-1].extend(group)
                continue

            merged_groups.append(group)

        return merged_groups

    def _content_lines(
        self,
        lines: list[DocumentLine],
    ) -> list[DocumentLine]:
        return [
            line
            for line in lines
            if line.role not in {"HEADER", "FOOTER"} and line.text.strip()
        ]

    def _overlap_lines(
        self,
        lines: list[DocumentLine],
    ) -> list[DocumentLine]:
        if self.chunk_overlap <= 0:
            return []

        overlap = []
        char_count = 0

        for line in reversed(lines):
            line_length = len(line.text)

            if overlap and char_count + line_length > self.chunk_overlap:
                break

            overlap.insert(0, line)
            char_count += line_length

        return overlap

    def _build_chunk(
        self,
        section: DocumentSection,
        lines: list[DocumentLine],
        chunk_index: int,
    ) -> DocumentChunk:
        text = self._chunk_text(section, lines)
        metadata = section.metadata

        return DocumentChunk(
            chunk_id=self._chunk_id(metadata.get("section_id", section.title), chunk_index, text),
            document_id=metadata.get("document_id", section.document_id),
            section_id=metadata.get("section_id", ""),
            chunk_index=chunk_index,
            company=metadata.get("company", section.company),
            policy_name=metadata.get("policy_name", "Unknown Policy"),
            policy_type=metadata.get("policy_type", "Unknown"),
            section_title=metadata.get("section_title", section.title),
            section_type=metadata.get("section_type", section.section_type),
            page_start=min(line.page for line in lines),
            page_end=max(line.page for line in lines),
            text=text,
            char_count=len(text),
            token_count=self._token_count(text),
            source_file=metadata.get("source_file", section.source_file),
            file_path=metadata.get("file_path", section.file_path),
        )

    def _chunk_id(
        self,
        section_id: str,
        chunk_index: int,
        text: str,
    ) -> str:
        digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]

        return f"{section_id}:chunk:{chunk_index:03d}:{digest}"

    def _chunk_text(
        self,
        section: DocumentSection,
        lines: list[DocumentLine],
    ) -> str:
        metadata = section.metadata
        section_title = metadata.get("section_title", section.title)
        policy_name = metadata.get("policy_name", "Unknown Policy")
        body = self._lines_text(lines)

        prefix = f"Policy: {policy_name}\nSection: {section_title}"

        if body.startswith(section_title):
            return self._clean_text(f"{prefix}\n\n{body}")

        return self._clean_text(f"{prefix}\n\n{body}")

    def _lines_text(
        self,
        lines: list[DocumentLine],
    ) -> str:
        return self._clean_text("\n".join(line.text for line in lines))

    def _token_count(
        self,
        text: str,
    ) -> int:
        return len(re.findall(r"\w+|[^\w\s]", text))

    def _clean_text(
        self,
        text: str,
    ) -> str:
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
        lines = [line for line in lines if line]

        return "\n".join(lines)
