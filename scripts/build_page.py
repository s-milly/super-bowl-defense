"""
Build the chart page from site/page.html and data/super_bowl_rankings.json.

Writes index.html (served by GitHub Pages). Run after build_dataset.py:
    python3 scripts/build_page.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
page = (ROOT / "site" / "page.html").read_text()
data = json.loads((ROOT / "data" / "super_bowl_rankings.json").read_text())
page = page.replace("/*DATA*/[]", json.dumps(data, separators=(",", ":")))

(ROOT / "index.html").write_text(
    '<!doctype html>\n<html lang="en">\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
    + page + "\n</html>\n"
)
print("index.html written")
