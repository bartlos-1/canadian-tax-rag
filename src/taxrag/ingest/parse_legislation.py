"""Parse Justice Laws XML (ITA / ITR) into provision-level units.

Output: one JSON line per *provision unit*:
  - normally one subsection, e.g. ITA 118.5(1)
  - a section with no subsections becomes one unit, e.g. ITA 2
  - definitions subsections (e.g. 248(1)) become one unit per defined term

This module does NOT chunk. Units can be very long (some subsections run to
thousands of tokens) or very short. Chunking them is a separate step; see src/taxrag/ingest/chunk.py.

Usage:
    python -m taxrag.ingest.parse_legislation data/raw/legislation/ita.xml data/processed/ita_units.jsonl --act ITA
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from lxml import etree

LIMS = "{http://justice.gc.ca/lims}"
# Elements whose text we don't want in the provision body
SKIP = {"HistoricalNote", "MarginalNote", "Label", "DefinedTermFr", "Footnote"}
# Structural children rendered as their own indented lines
STRUCT = {"Subsection", "Paragraph", "Subparagraph", "Clause", "Subclause", "Subsubclause",
          "Definition", "ContinuedParagraph", "ContinuedSubparagraph", "ContinuedClause",
          "ContinuedSectionSubsection", "ContinuedDefinition", "FormulaGroup", "FormulaDefinition",
          "FormulaParagraph"}


@dataclass
class Unit:
    id: str                      # e.g. "ITA 118.5(1)" or "ITA 248(1) 'employee'"
    act: str
    section: str
    subsection: str | None
    marginal_note: str | None    # short official title, e.g. "Tuition credit"
    breadcrumb: list[str]        # ["PART I Income Tax", "DIVISION E Computation of Tax", ...]
    text: str
    defined_term: str | None = None
    inforce_start: str | None = None
    last_amended: str | None = None
    cross_refs: list[str] = field(default_factory=list)  # external act refs; internal ones are plain text, extract them later


def _label(el) -> str:
    return (el.findtext("Label") or "").strip()


def _render(el, depth: int = 0) -> list[str]:
    """Flatten a provision element to indented lines like '(a) text', keeping the legal structure visible."""
    lines: list[str] = []
    own: list[str] = []
    for child in el:
        if not isinstance(child.tag, str) or child.tag in SKIP:
            continue
        if child.tag in STRUCT:
            if own:
                lines.append("  " * depth + " ".join(own))
                own = []
            lab = _label(child)
            sub = _render(child, depth + 1)
            if sub and lab:
                sub[0] = "  " * (depth + 1) + f"{lab} " + sub[0].lstrip()
            lines.extend(sub)
        else:
            t = " ".join("".join(child.itertext()).split())
            if t:
                own.append(t)
    if own:
        lines.append("  " * depth + " ".join(own))
    return lines


def _heading_text(h) -> str:
    lab = (h.findtext("Label") or "").strip()
    title = " ".join("".join((h.find("TitleText") if h.find("TitleText") is not None else h).itertext()).split())
    if lab and title.startswith(lab):
        title = title[len(lab):].strip()
    return f"{lab} {title}".strip()


def _xrefs(el) -> list[str]:
    return sorted({" ".join("".join(x.itertext()).split()) for x in el.iter("XRefExternal")})


def parse(xml_path: Path, act: str):
    root = etree.parse(str(xml_path)).getroot()
    stack: dict[int, str] = {}
    for el in root.find("Body"):
        if el.tag == "Heading":
            lvl = int(el.get("level", "1"))
            stack = {k: v for k, v in stack.items() if k < lvl}
            stack[lvl] = _heading_text(el)
            continue
        if el.tag != "Section" or el.find("Repealed") is not None and len(el) <= 3:
            continue
        sec = _label(el)
        crumb = [stack[k] for k in sorted(stack)]
        sec_note = (el.findtext("MarginalNote") or "").strip() or None
        subs = el.findall("Subsection")
        if not subs:
            yield Unit(f"{act} {sec}", act, sec, None, sec_note, crumb, "\n".join(_render(el)),
                       inforce_start=el.get(f"{LIMS}inforce-start-date"),
                       last_amended=el.get(f"{LIMS}lastAmendedDate"), cross_refs=_xrefs(el))
            continue
        for ss in subs:
            if ss.find("Repealed") is not None and ss.find("Text") is None:
                continue
            lab = _label(ss)
            note = (ss.findtext("MarginalNote") or "").strip() or sec_note
            defs = ss.findall("Definition")
            common = dict(act=act, section=sec, subsection=lab, marginal_note=note, breadcrumb=crumb,
                          inforce_start=ss.get(f"{LIMS}inforce-start-date"),
                          last_amended=ss.get(f"{LIMS}lastAmendedDate"))
            if len(defs) > 3:  # a definitions subsection: one unit per term
                for d in defs:
                    term = " ".join("".join(d.findtext("Text/DefinedTermEn") or
                                            next(d.iter("DefinedTermEn"), etree.Element("x")).itertext()).split())
                    yield Unit(f"{act} {sec}{lab} '{term}'", text="\n".join(_render(d)),
                               defined_term=term or None, cross_refs=_xrefs(d), **common)
            else:
                yield Unit(f"{act} {sec}{lab}", text="\n".join(_render(ss)), cross_refs=_xrefs(ss), **common)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("xml", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--act", default="ITA")
    a = ap.parse_args()
    a.out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with a.out.open("w") as f:
        for u in parse(a.xml, a.act):
            f.write(json.dumps(asdict(u), ensure_ascii=False) + "\n")
            n += 1
    print(f"wrote {n} units -> {a.out}")


if __name__ == "__main__":
    main()
