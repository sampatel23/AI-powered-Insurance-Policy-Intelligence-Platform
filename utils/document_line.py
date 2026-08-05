from dataclasses import dataclass
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