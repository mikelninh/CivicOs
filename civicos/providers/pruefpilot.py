from __future__ import annotations
from dataclasses import asdict, dataclass
import hashlib
import io
import re
from typing import Any
from pypdf import PdfReader

MAX_DOCUMENT_BYTES = 10_000_000
MAX_PAGES = 50
INJECTION_PATTERNS = (
    r"ignore\s+(all\s+)?previous\s+(system\s+)?instructions",
    r"reveal\s+(the\s+)?(system prompt|api key|secret)",
    r"you are now",
    r"developer message",
    r"system instruction",
    r"ignoriere\s+(alle\s+)?vorherigen\s+anweisungen",
)


@dataclass(frozen=True)
class DocumentIntake:
    provider: str
    filename: str
    sha256: str
    bytes_read: int
    page_count: int
    text: str
    status: str
    security_findings: list[dict[str, Any]]

    def to_dict(self, *, include_text: bool = False) -> dict[str, Any]:
        data = asdict(self)
        if not include_text:
            data.pop("text", None)
        return data


def _scan_untrusted(text: str) -> list[dict[str, Any]]:
    compact = " ".join(text.split())
    findings = []
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, compact, re.IGNORECASE):
            findings.append({
                "category":"prompt_injection",
                "severity":"high",
                "action":"quarantine",
                "message":"Instruction-like content detected inside an untrusted uploaded document.",
            })
            break
    if re.search(r"javascript:|<script\b", compact, re.IGNORECASE):
        findings.append({"category":"embedded_script","severity":"high","action":"quarantine"})
    return findings


def ingest_decision_document(filename: str, content: bytes, content_type: str = "") -> DocumentIntake:
    """Privacy-minimising decision intake inspired by PrüfPilot.

    The caller receives a hash + extracted text in memory. CivicOS does not persist
    the uploaded bytes by default. Instruction-like document content is treated as
    untrusted data and quarantined rather than executed.
    """
    if not content:
        raise ValueError("Uploaded document is empty")
    if len(content) > MAX_DOCUMENT_BYTES:
        raise ValueError(f"Document exceeds {MAX_DOCUMENT_BYTES} bytes")

    sha256 = hashlib.sha256(content).hexdigest()
    lower_name = filename.lower()
    is_pdf = "pdf" in (content_type or "").lower() or lower_name.endswith(".pdf")
    page_count = 1

    if is_pdf:
        reader = PdfReader(io.BytesIO(content))
        page_count = len(reader.pages)
        parts = []
        for page in reader.pages[:MAX_PAGES]:
            try:
                parts.append(page.extract_text() or "")
            except Exception:
                parts.append("")
        text = "\n".join(parts).strip()
    else:
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("Only PDF or UTF-8 text documents are supported in the v0.3 proof") from exc

    findings = _scan_untrusted(text)
    quarantined = any(f.get("action") == "quarantine" for f in findings)
    return DocumentIntake(
        provider="PrüfPilot-compatible intake",
        filename=filename,
        sha256=sha256,
        bytes_read=len(content),
        page_count=page_count,
        text=text,
        status="quarantined" if quarantined else "ready",
        security_findings=findings,
    )
