#!/usr/bin/env python3
"""
make_parts_index.py — emit /parts-index.json for the AI Worker.

Reads the English (and, if present, Portuguese) catalogue pages, and writes a
compact JSON array the Worker fetches and caches:

  [{ "brand":"man", "pn":"81.08405-0028", "d":"Filter element",
     "dpt":"Elemento filtrante", "c":"Filters" }, ...]

Run from the repo root, then commit parts-index.json so it is served at
https://oetrucksurplus.parts/parts-index.json

Re-run whenever the inventory changes (same source of truth as build.py).
"""
import re, json
from pathlib import Path

REPO = Path(__file__).resolve().parent
EN = REPO / "catalog-en"
PT = REPO / "catalog-pt"
BRANDS = ["vw", "man", "mercedes", "iveco", "toyota"]
ITEMS_RE = re.compile(r"const ITEMS\s*=\s*(\[.*?\]);", re.S)


def parse(path):
    if not path.exists():
        return []
    m = ITEMS_RE.search(path.read_text(encoding="utf-8"))
    return json.loads(m.group(1)) if m else []


def main():
    out = []
    for slug in BRANDS:
        en = parse(EN / slug / "index.html")
        pt = parse(PT / slug / "index.html")
        pt_by_pn = {it.get("pn"): it.get("d", "") for it in pt}
        for it in en:
            pn = it.get("pn")
            out.append({
                "brand": slug,
                "pn": pn,
                "d": it.get("d", ""),
                "dpt": pt_by_pn.get(pn, ""),
                "c": it.get("c", "Other"),
            })
    (REPO / "parts-index.json").write_text(
        json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    size_kb = (REPO / "parts-index.json").stat().st_size / 1024
    print(f"  \u2713 parts-index.json  ({len(out)} parts, {size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
