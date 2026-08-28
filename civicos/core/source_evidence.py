from __future__ import annotations
from dataclasses import dataclass
from html import unescape
import re
from typing import Any
from civicos.core.models import EvidenceExcerpt, EvidenceFact


@dataclass(frozen=True)
class FactProfile:
    fact_id: str
    claim_id: str | None
    label: str
    value: Any
    patterns: tuple[str, ...]


PROFILES: dict[str, tuple[FactProfile, ...]] = {
    "arbeitsagentur_kiz": (
        FactProfile("kiz:max-per-child", "benefit:kinderzuschlag", "Kinderzuschlag maximum per child/month", 297, (r"\b297\b",)),
    ),
    "familienportal_elterngeld_amount": (
        FactProfile("elterngeld:basis-range", "benefit:elterngeld", "Basiselterngeld monthly range", "€300–€1,800", (r"\b300\b", r"(?:1[.\s]?800|1800)")),
        FactProfile("elterngeld:plus-range", "benefit:elterngeld", "ElterngeldPlus monthly range", "€150–€900", (r"\b150\b", r"\b900\b")),
    ),
    "familienportal_elterngeld_eligibility": (
        FactProfile("elterngeld:hours", "benefit:elterngeld", "Maximum weekly work-hours signal", 32, (r"\b32\b.{0,40}(?:stund|hour)",)),
        FactProfile("elterngeld:income-ceiling", "benefit:elterngeld", "Taxable-income ceiling signal", 175000, (r"175[.\s]?000",)),
    ),
    "familienportal_unterhaltsvorschuss": (
        FactProfile("uv:0-5", "benefit:unterhaltsvorschuss", "Unterhaltsvorschuss age 0–5 monthly amount", 227, (r"\b227\b",)),
        FactProfile("uv:6-11", "benefit:unterhaltsvorschuss", "Unterhaltsvorschuss age 6–11 monthly amount", 299, (r"\b299\b",)),
        FactProfile("uv:12-17", "benefit:unterhaltsvorschuss", "Unterhaltsvorschuss age 12–17 monthly amount", 394, (r"\b394\b",)),
    ),
    "berlin_but_service": (
        FactProfile("but:school-supplies", "benefit:bildung-teilhabe", "Berlin school-supplies support signal", 195, (r"\b195\b",)),
    ),
    "berlin_wohngeld": (
        FactProfile("wohngeld:calculation-factors", "benefit:wohngeld", "Wohngeld calculation factors present", ["household", "rent", "income"], (r"haushalt", r"miet", r"einkommen")),
    ),
}


def _plain_text(body: bytes) -> str:
    text = body.decode("utf-8", errors="replace")
    text = re.sub(r"(?is)<script\b.*?</script>", " ", text)
    text = re.sub(r"(?is)<style\b.*?</style>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = unescape(text)
    return " ".join(text.split())


def _window(text: str, start: int, end: int, radius: int = 170) -> str:
    left = max(0, start - radius)
    right = min(len(text), end + radius)
    return text[left:right].strip()


def extract_live_facts(source_id: str, body: bytes, receipt_id: str) -> tuple[list[EvidenceExcerpt], list[EvidenceFact]]:
    """Extract only narrow, pre-declared facts from current official bytes.

    This is intentionally conservative. A fact is marked verified only when every
    declared deterministic pattern is present in the fetched source. It does not
    generalise to unprofiled claims and does not infer legal applicability.
    """
    profiles = PROFILES.get(source_id, ())
    if not profiles:
        return [], []

    text = _plain_text(body)
    lower = text.lower()
    excerpts: list[EvidenceExcerpt] = []
    facts: list[EvidenceFact] = []

    for profile in profiles:
        matches = [re.search(pattern, lower, flags=re.IGNORECASE) for pattern in profile.patterns]
        if not all(matches):
            continue
        first = next(match for match in matches if match is not None)
        excerpt_id = f"excerpt:{source_id}:{profile.fact_id}"
        excerpt = EvidenceExcerpt(
            excerpt_id=excerpt_id,
            receipt_id=receipt_id,
            source_id=source_id,
            text=_window(text, first.start(), first.end()),
            extraction_method="declared_pattern_profile_v4",
        )
        excerpts.append(excerpt)
        facts.append(EvidenceFact(
            fact_id=profile.fact_id,
            claim_id=profile.claim_id,
            source_id=source_id,
            receipt_id=receipt_id,
            label=profile.label,
            value=profile.value,
            status="verified",
            excerpt_id=excerpt_id,
            extraction_method="declared_pattern_profile_v4",
            details={"profile_patterns": list(profile.patterns), "semantic_scope": "narrow source fact; not full eligibility/applicability verification"},
        ))

    return excerpts, facts
