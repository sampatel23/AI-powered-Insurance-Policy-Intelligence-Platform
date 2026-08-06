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

print()
print(f"Total Sections: {len(sections)}")
print()

for section in sections:
    metadata = section.metadata

    print("=" * 80)
    print(f"Section ID  : {metadata['section_id']}")
    print(f"Document ID : {metadata['document_id']}")
    print(f"Company     : {metadata['company']}")
    print(f"Policy Name : {metadata['policy_name']}")
    print(f"Policy Type : {metadata['policy_type']}")
    print(f"UIN         : {metadata['uin']}")
    print(f"Source File : {metadata['source_file']}")
    print(f"Title       : {metadata['section_title']}")
    print(f"Pages       : {metadata['page_range']}")
    print(f"Lines       : {metadata['line_count']}")
    print()
