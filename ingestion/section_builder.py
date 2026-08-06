"""
Section Builder

Groups classified document lines into logical sections.
"""

from loguru import logger

from utils.document_line import DocumentLine
from utils.document_section import DocumentSection


class SectionBuilder:
    def _next_heading_continuation(
        self,
        lines: list[DocumentLine],
        index: int,
    ) -> DocumentLine | None:
        if index + 1 >= len(lines):
            return None

        line = lines[index]
        next_line = lines[index + 1]

        if line.source_key != next_line.source_key:
            return None

        if line.page != next_line.page:
            return None

        if abs(line.bbox[1] - next_line.bbox[1]) > 2:
            return None

        if not line.is_bold or not next_line.is_bold:
            return None

        if line.text.strip().lower() not in {"e.", "f."}:
            return None

        return next_line

    def _build_fallback_section(
        self,
        lines: list[DocumentLine],
        company: str,
    ) -> DocumentSection | None:
        if not lines:
            return None

        first_line = lines[0]

        title = next(
            (
                line.text
                for line in lines
                if line.role in {"DOCUMENT_TITLE", "DOCUMENT_SUBTITLE"}
            ),
            "Document Body",
        )

        return DocumentSection(
            title=title,
            company=first_line.company if first_line.company != "Unknown" else company,
            start_page=lines[0].page,
            end_page=lines[-1].page,
            section_type="DOCUMENT",
            lines=lines,
            document_id=first_line.document_id,
            company_key=first_line.company_key,
            source_file=first_line.source_file,
            file_path=first_line.file_path,
        )

    def build(
        self,
        lines: list[DocumentLine],
        company: str = "Unknown"
    ) -> list[DocumentSection]:

        logger.info("Building document sections...")

        sections = []

        current_section = None

        current_document_key = None

        pending_document_lines = []

        skip_next_line = False

        for index, line in enumerate(lines):
            if skip_next_line:
                skip_next_line = False
                continue

            line_document_key = line.source_key

            if (
                current_section is not None
                and current_document_key != line_document_key
            ):
                sections.append(current_section)
                current_section = None

            if current_document_key != line_document_key:
                fallback_section = self._build_fallback_section(
                    pending_document_lines,
                    company,
                )

                if fallback_section is not None:
                    sections.append(fallback_section)

                pending_document_lines = []

                current_document_key = line_document_key

            # Start a new SECTION
            if line.role == "SECTION":
                continuation = self._next_heading_continuation(lines, index)
                section_title = line.text

                if continuation is not None:
                    section_title = f"{line.text} {continuation.text}"
                    skip_next_line = True

                section_lines = [line]

                if continuation is not None:
                    section_lines.append(continuation)

                # Save previous section
                if current_section is not None:
                    sections.append(current_section)

                current_section = DocumentSection(
                    title=section_title,
                    company=line.company if line.company != "Unknown" else company,
                    start_page=line.page,
                    end_page=line.page,
                    section_type="SECTION",
                    lines=section_lines,
                    document_id=line.document_id,
                    company_key=line.company_key,
                    source_file=line.source_file,
                    file_path=line.file_path,
                )

                pending_document_lines = []

                continue

            # Ignore everything before first section
            if current_section is None:
                pending_document_lines.append(line)
                continue

            # Add line
            current_section.lines.append(line)

            current_section.end_page = line.page

        # Save last section
        if current_section is not None:
            sections.append(current_section)
        else:
            fallback_section = self._build_fallback_section(
                pending_document_lines,
                company,
            )

            if fallback_section is not None:
                sections.append(fallback_section)

        logger.success(f"Built {len(sections)} sections.")

        return sections
