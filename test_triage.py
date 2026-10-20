"""Run: python3 test_triage.py  (mock mode, no network)"""
import csv
import io
import json
import re
import tempfile
from pathlib import Path

import server

server.OVERRIDES = Path(tempfile.mkdtemp()) / "overrides.jsonl"
CSV = server.DEFAULT_CSV.read_text(encoding="utf-8")


def without(ids):
    rows = list(csv.DictReader(io.StringIO(CSV)))
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=server.COLUMNS)
    w.writeheader()
    w.writerows(r for r in rows if r["id"] not in ids)
    return out.getvalue()


r = server.triage(CSV)

# PII: no raw rider id anywhere in what the page or the model sees.
assert not re.search(r"R-1\d{4}", json.dumps(r)), "raw rider_id leaked"

# Override token: FB-002 is kept, flagged, and still triaged as money owed.
m = r["messages"]["FB-002"]
assert m["token_flag"] and m["label"]["severity"] == 2
assert any("FB-002" in g["ids"] for g in r["groups"])

# Escalation: both safety incidents, bundled.
assert r["escalation"]["key"] == "safety"
assert set(r["escalation"]["ids"]) == {"FB-004", "FB-005", "FB-010"}

# Repeat riders are linked without showing who they are.
assert r["messages"]["FB-021"]["same_rider_as"] == ["FB-013"]

# Every mock label's evidence is a real quote from its message.
assert all(m["evidence_found"] for m in r["messages"].values())

# What would change my mind: with safety cleared, the slot goes to the payment fault.
r2 = server.triage(without({"FB-004", "FB-005", "FB-010"}))
assert r2["escalation"]["key"] == "money", r2["escalation"]["key"]

# A reused id with different text gets no mock label instead of a wrong one.
r3 = server.triage(CSV.replace("driver was polite and waited", "brakes failed on the flyover and"))
assert r3["messages"]["FB-001"]["label"]["code"] is None
assert any(g["key"] == "unlabelled" and "FB-001" in g["ids"] for g in r3["groups"])

# Rule beats model: a safety code is always severity 1.
orig = server.label_mock
server.label_mock = lambda rows: {"FB-001": {"code": "SAF-OTHER", "severity": 4, "reason": "x",
                                             "evidence": "driver", "source": "mock"}}
server.LABEL_CACHE.clear()
assert server.triage(CSV)["messages"]["FB-001"]["label"]["severity"] == 1
server.label_mock = orig
server.LABEL_CACHE.clear()

# Overrides: a human relabel wins and needs a reason.
server.save_override({"batch": r["batch"], "id": "FB-004", "code": "NONE", "severity": 5, "note": "trip record cleared driver"})
r4 = server.triage(CSV)
assert r4["messages"]["FB-004"]["label"]["source"] == "human"
assert "FB-004" not in r4["escalation"]["ids"]
try:
    server.save_override({"batch": r["batch"], "id": "FB-004", "code": "NONE", "severity": 5, "note": " "})
    raise AssertionError("override without a note was accepted")
except ValueError:
    pass

print("all checks passed")
