from ingestion.layout_analyzer import LayoutAnalyzer
from ingestion.structure_classifier import StructureClassifier

layout = LayoutAnalyzer()

lines = layout.analyze()

classifier = StructureClassifier()

lines = classifier.classify(lines)

for line in lines[:80]:
    print(
        f"{line.role:20} | "
        f"{line.font_size:5.1f} | "
        f"{line.text}"
    )