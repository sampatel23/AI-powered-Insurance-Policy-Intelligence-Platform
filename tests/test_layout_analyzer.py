from ingestion.layout_analyzer import LayoutAnalyzer

analyzer = LayoutAnalyzer()

lines = analyzer.analyze()

print(f"\nTotal Lines : {len(lines)}\n")

for line in lines[:50]:
    print("-" * 80)
    print(line)