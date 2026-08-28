"""GitLaw contract adapter.

CivicOS keeps legal retrieval behind an explicit provider boundary. This module
performs deterministic citation parsing and resolves a small set of official
source URLs locally; broader section-level verification is delegated to GitLaw.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
import re
from typing import Any

PROVIDER = "mikelninh/gitlaw"
CITATION_RE = re.compile(r"§{1,2}\s*(?P<section>\d+[a-zA-Z]?)(?:\s*Abs\.\s*(?P<paragraph>\d+))?(?:\s*(?P<law>[A-Za-zÄÖÜäöüß0-9-]+))?")

LAW_ROUTES = {
    "VwVfG": "https://www.gesetze-im-internet.de/vwvfg/",
    "BGB": "https://www.gesetze-im-internet.de/bgb/",
    "WoGG": "https://www.gesetze-im-internet.de/wogg/",
    "SGB": "https://www.gesetze-im-internet.de/sgb_10/",
}


@dataclass(frozen=True)
class CitationCheck:
    raw: str
    section: str | None
    paragraph: str | None
    law_code: str | None
    syntax_valid: bool
    official_url: str | None
    verification: str
    provider: str = PROVIDER

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def verify_citation(raw: str, *, default_law: str | None = None) -> CitationCheck:
    match = CITATION_RE.search(raw or "")
    if not match:
        return CitationCheck(raw=raw, section=None, paragraph=None, law_code=default_law, syntax_valid=False, official_url=None, verification="invalid_syntax")

    section = match.group("section")
    paragraph = match.group("paragraph")
    law = match.group("law") or default_law
    base = LAW_ROUTES.get(law or "")
    official_url = f"{base}__{section.lower()}.html" if base and section else None
    verification = "official_route_resolved" if official_url else "requires_gitlaw_lookup"
    return CitationCheck(raw=raw, section=section, paragraph=paragraph, law_code=law, syntax_valid=True, official_url=official_url, verification=verification)


def verify_many(citations: list[str], *, default_law: str | None = None) -> list[dict[str, Any]]:
    return [verify_citation(c, default_law=default_law).to_dict() for c in citations]
