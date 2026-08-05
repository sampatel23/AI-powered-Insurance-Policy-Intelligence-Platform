from ingestion.pdf_loader import PDFLoader
from ingestion.section_parser import SectionParser

loader = PDFLoader()
documents = loader.load_documents()

parser = SectionParser()

documents = parser.parse(documents)

for doc in documents[:20]:

    print("=" * 60)

    print(doc.metadata["page"])

    print(doc.metadata["section"])