from dataclasses import dataclass


@dataclass
class DocumentChunk:
    """
    Represents one retrieval-ready chunk derived from a document section.
    """

    chunk_id: str

    document_id: str

    section_id: str

    chunk_index: int

    company: str

    policy_name: str

    policy_type: str

    section_title: str

    section_type: str

    page_start: int

    page_end: int

    text: str

    char_count: int

    token_count: int

    source_file: str

    file_path: str

    embedding: list[float] | None = None
