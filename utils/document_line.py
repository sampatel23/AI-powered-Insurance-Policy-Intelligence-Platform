from dataclasses import dataclass
from pathlib import Path
from typing import Tuple


@dataclass
class DocumentLine:
    """
    Represents one logical line extracted from a PDF.
    """

    text: str

    page: int

    bbox: Tuple[float, float, float, float]

    font_size: float

    font_name: str

    is_bold: bool

    block_no: int

    line_no: int

    role: str = "UNKNOWN"

    document_id: str = ""

    company: str = "Unknown"

    company_key: str = ""

    source_file: str = ""

    file_path: str = ""

    @property
    def source_key(self) -> str:
        """
        Stable fallback document key for older lines without document_id.
        """
        if self.document_id:
            return self.document_id

        if self.file_path:
            return str(Path(self.file_path))

        return self.source_file
