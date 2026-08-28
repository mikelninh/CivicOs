from __future__ import annotations
import json
import os
from pathlib import Path
from civicos.core.models import EvidenceReceipt


class EvidenceVault:
    """Small local evidence vault for the master proof.

    Public official-source bytes may be persisted when explicitly requested.
    User documents default to receipt-only and should never be written here unless
    a caller deliberately opts into a reviewed storage policy.
    """

    def __init__(self, root: str | Path | None = None):
        configured = root or os.getenv("CIVICOS_EVIDENCE_DIR")
        self.root = Path(configured).expanduser() if configured else None

    @property
    def enabled(self) -> bool:
        return self.root is not None

    def store_public_source(self, receipt: EvidenceReceipt, body: bytes) -> EvidenceReceipt:
        if not self.root:
            return receipt
        folder = self.root / "public" / receipt.source_id / receipt.receipt_id
        folder.mkdir(parents=True, exist_ok=True)
        raw_path = folder / "original.bin"
        meta_path = folder / "receipt.json"
        raw_path.write_bytes(body)
        stored = receipt.model_copy(update={"storage_state":"stored", "storage_path":str(raw_path)})
        meta_path.write_text(json.dumps(stored.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8")
        return stored
