from ingestion.pdf_loader import PDFLoader

loader = PDFLoader()

documents = loader.load_documents()

print(f"\nTotal Pages Loaded: {len(documents)}")

print("\nMetadata:")
print(documents[0].metadata)

print("\nFirst 500 Characters:\n")
print(documents[0].page_content[:500])