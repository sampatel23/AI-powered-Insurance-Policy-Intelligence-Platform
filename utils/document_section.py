from dataclasses import dataclass, field

from utils.document_line import DocumentLine


@dataclass
class DocumentSection:
    """
    Represents one logical section of a policy.
    """

    title: str

    company: str

    start_page: int

    end_page: int

    section_type: str

    lines: list[DocumentLine] = field(default_factory=list)

    document_id: str = ""

    company_key: str = ""

    source_file: str = ""

    file_path: str = ""
