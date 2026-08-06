from ingestion.layout_analyzer import LayoutAnalyzer
from ingestion.structure_classifier import StructureClassifier
from ingestion.section_builder import SectionBuilder

layout = LayoutAnalyzer()

lines = layout.analyze()

classifier = StructureClassifier()

lines = classifier.classify(lines)

builder = SectionBuilder()

sections = builder.build(lines, company="Bajaj Allianz")

print()

for section in sections:

    print("=" * 80)

    print(f"Title      : {section.title}")

    print(f"Pages      : {section.start_page} - {section.end_page}")

    print(f"Lines      : {len(section.lines)}")

    print()