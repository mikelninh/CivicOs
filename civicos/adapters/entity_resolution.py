"""CivicOS adapter for the evaluated SafeTrace entity-resolution contract.

The scoring logic mirrors the SafeTrace proof so CivicOS can consume the same
SAME_AS / REVIEW / REJECT semantics without importing the source repository at
runtime. The provider repository remains the canonical benchmark/provenance.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
import re
from typing import Any

AUTO_MERGE_THRESHOLD = 0.72
REVIEW_THRESHOLD = 0.58
LEGAL_SUFFIXES = r"\b(gmbh|ggmbh|ag|se|eg|mbh|ug)\b"
PROVIDER = "mikelninh/digital-democracy-studio:safetrace/entity_resolution"


def normalize(text: str) -> str:
    text = (text or "").lower()
    for src, dst in {"ß": "ss", "ä": "ae", "ö": "oe", "ü": "ue"}.items():
        text = text.replace(src, dst)
    text = re.sub(LEGAL_SUFFIXES, " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def _root_domain(domain: str) -> str:
    domain = (domain or "").lower().removeprefix("www.")
    parts = domain.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else domain


def _postcode(address: str) -> str:
    match = re.search(r"\b\d{5}\b", address or "")
    return match.group(0) if match else ""


def _jaccard(left: str, right: str) -> float:
    a, b = set(normalize(left).split()), set(normalize(right).split())
    return len(a & b) / len(a | b) if a | b else 0.0


def _name_similarity(left: str, right: str) -> float:
    a, b = normalize(left), normalize(right)
    return max(SequenceMatcher(None, a, b).ratio(), _jaccard(left, right))


def _director_overlap(left: list[str], right: list[str]) -> float:
    for la in left:
        a = [t for t in normalize(la).split() if t != "dr"]
        for rb in right:
            b = [t for t in normalize(rb).split() if t != "dr"]
            if a and b and a[-1] == b[-1] and a[0][0] == b[0][0]:
                return 1.0
    return 0.0


@dataclass(frozen=True)
class EntityResolution:
    left_id: str
    right_id: str
    score: float
    decision: str
    relation: str
    evidence: dict[str, Any]
    provider: str = PROVIDER

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def resolve_pair(left: dict[str, Any], right: dict[str, Any]) -> EntityResolution:
    name = _name_similarity(str(left.get("name", "")), str(right.get("name", "")))
    left_domain = str(left.get("domain", "")).lower().removeprefix("www.")
    right_domain = str(right.get("domain", "")).lower().removeprefix("www.")
    exact_domain = bool(left_domain and right_domain) and left_domain == right_domain
    root_domain = bool(left_domain and right_domain) and _root_domain(left_domain) == _root_domain(right_domain)
    address = _jaccard(str(left.get("address", "")), str(right.get("address", "")))
    left_pc, right_pc = _postcode(str(left.get("address", ""))), _postcode(str(right.get("address", "")))
    postcode = bool(left_pc and right_pc) and left_pc == right_pc
    director = _director_overlap(list(left.get("directors", [])), list(right.get("directors", [])))

    score = 0.45 * name + 0.20 * float(exact_domain) + 0.10 * float(root_domain) + 0.15 * address + 0.05 * float(postcode) + 0.05 * director
    decision = "auto_merge" if score >= AUTO_MERGE_THRESHOLD else "human_review" if score >= REVIEW_THRESHOLD else "reject"
    relation = "SAME_AS" if decision == "auto_merge" else "REVIEW" if decision == "human_review" else "DISTINCT"
    evidence = {
        "name_similarity": round(name, 3),
        "exact_domain": exact_domain,
        "shared_root_domain": root_domain,
        "address_similarity": round(address, 3),
        "postcode_match": postcode,
        "director_overlap": bool(director),
        "left_source": left.get("source"),
        "right_source": right.get("source"),
    }
    return EntityResolution(
        left_id=str(left.get("record_id") or left.get("id") or left.get("name", "left")),
        right_id=str(right.get("record_id") or right.get("id") or right.get("name", "right")),
        score=round(score, 3),
        decision=decision,
        relation=relation,
        evidence=evidence,
    )
