from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

from config.settings import settings
from loguru import logger
from config.constants import COMPANY_MAPPING


class PDFLoader:
    """
    Loads all PDF documents from the raw data directory.

    Responsibilities:
    - Discover PDFs
    - Load pages
    - Attach basic metadata

    Does NOT:
    - Clean text
    - Chunk documents
    - Create embeddings
    """

    def __init__(self):
        self.raw_data_path = Path(settings.RAW_DATA_PATH)

    def load_documents(self) -> list[Document]:
        documents = []

        pdf_files = list(self.raw_data_path.rglob("*.pdf"))

        if not pdf_files:
            logger.warning("No PDF files found.")
            return documents

        logger.info(f"Found {len(pdf_files)} PDF(s).")

        for pdf_path in pdf_files:

            company_key = pdf_path.parent.name.lower()

            company_name = COMPANY_MAPPING.get(company_key, company_key)

            logger.info(f"Loading: {pdf_path.name}")

            loader = PyPDFLoader(str(pdf_path))

            pages = loader.load()

            for page in pages:

                page.metadata.update(
                    {
                        "company": company_name,
                        "company_key": company_key,
                        "source_file": pdf_path.name,
                        "file_path": str(pdf_path),
                    }
                )

            documents.extend(pages)

        logger.success(f"Loaded {len(documents)} pages.")

        return documents