from collections import Counter

from ingestion.chunker import SectionAwareChunker
from ingestion.layout_analyzer import LayoutAnalyzer
from ingestion.metadata_extractor import MetadataExtractor
from ingestion.section_builder import SectionBuilder
from ingestion.structure_classifier import StructureClassifier


layout = LayoutAnalyzer()

lines = layout.analyze()

classifier = StructureClassifier()

lines = classifier.classify(lines)

builder = SectionBuilder()

sections = builder.build(lines)

extractor = MetadataExtractor()

sections = extractor.enrich_sections(sections, lines)

chunker = SectionAwareChunker()

chunks = chunker.chunk(sections)

print()
print(f"Total Sections: {len(sections)}")
print(f"Total Chunks  : {len(chunks)}")
print()

print("Chunks by source file:")
for source_file, count in Counter(chunk.source_file for chunk in chunks).items():
    print(f"- {source_file}: {count}")

print()
print("Sample chunks:")

for chunk in chunks[:10]:
    print("=" * 80)
    print(f"Chunk ID    : {chunk.chunk_id}")
    print(f"Document ID : {chunk.document_id}")
    print(f"Section ID  : {chunk.section_id}")
    print(f"Company     : {chunk.company}")
    print(f"Policy      : {chunk.policy_name}")
    print(f"Section     : {chunk.section_title}")
    print(f"Pages       : {chunk.page_start}-{chunk.page_end}")
    print(f"Chars       : {chunk.char_count}")
    print(f"Tokens      : {chunk.token_count}")
    print("Text Preview:")
    print(chunk.text[:500])
    print()
