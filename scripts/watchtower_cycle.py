from __future__ import annotations
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from civicos.connectors.official import SourceError, fetch_official
from civicos.core.models import EvidenceFact
from civicos.core.snapshot_store import SnapshotStore
from civicos.core.source_change import evaluate_source_change
from civicos.core.source_evidence import extract_live_facts
from civicos.core.watchtower import evaluate_watchtower

ROOT = Path(__file__).resolve().parents[1]
BASELINES = json.loads((ROOT / "data" / "watchtower_baselines.json").read_text(encoding="utf-8"))


def run_cycle(*, output: Path, state_db: str | None = None) -> dict:
    store = SnapshotStore(state_db) if state_db else None
    rows = []
    for source_id, baseline in BASELINES["sources"].items():
        previous = [EvidenceFact.model_validate(item) for item in baseline.get("facts", [])]
        try:
            receipt, body = fetch_official(source_id)
            _, current = extract_live_facts(source_id, body, receipt.receipt_id)
            impact = evaluate_source_change(
                source_id,
                previous_sha256=None,
                current_sha256=receipt.sha256,
                previous_facts=previous,
                current_facts=current,
            )
            report = evaluate_watchtower(impact, monitor_metadata={"provider":"scheduled_watchtower","baseline_version":BASELINES["version"]})
            if store:
                store.save(receipt, current, {"watchtower": report.model_dump(mode="json")})
            rows.append({
                "source_id": source_id,
                "status": "ok",
                "receipt": receipt.model_dump(mode="json"),
                "impact": impact.model_dump(mode="json"),
                "watchtower": report.model_dump(mode="json"),
            })
        except SourceError as exc:
            rows.append({"source_id": source_id, "status": "fetch_failed", "error": str(exc)})

    summary = {
        "sources": len(rows),
        "successful": sum(row["status"] == "ok" for row in rows),
        "fetch_failed": sum(row["status"] != "ok" for row in rows),
        "notify": sum(row.get("watchtower", {}).get("alert_decision") == "notify" for row in rows),
        "review": sum(row.get("watchtower", {}).get("alert_decision") == "review" for row in rows),
        "suppressed": sum(row.get("watchtower", {}).get("alert_decision") == "suppressed" for row in rows),
    }
    result = {
        "version": "1.0.0-rc1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "baseline_version": BASELINES["version"],
        "summary": summary,
        "results": rows,
        "policy": "New semantic baselines require human review; scheduled monitoring never auto-promotes changed facts.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="artifacts/watchtower-report.json")
    parser.add_argument("--state-db", default=None)
    args = parser.parse_args()
    result = run_cycle(output=Path(args.output), state_db=args.state_db)
    print(json.dumps(result["summary"], ensure_ascii=False))
    # Network failures stay visible in the report; only a total outage fails the cycle.
    if result["summary"]["successful"] == 0:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
