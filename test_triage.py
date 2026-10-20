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

# Step 2 in mock mode: every assessed group has a written cost and who pays from the allowed list.
for g in [r["escalation"]] + r["groups"]:
    if g["key"] in ("none", "unlabelled", "other"):
        continue
    assert g["cost_source"] == "mock", (g["key"], g["cost_source"])
    assert g["cost"].strip(), g["key"]
    assert set(g["who_pays"]) <= set(server.WHO_PAYS), (g["key"], g["who_pays"])

# The cost prompt never carries a raw rider id either.
assert not re.search(r"R-1\d{4}", r["prompt"]["cost_user"]), "raw rider_id in cost prompt"

# Praise: sarcasm is not praise, and a driver compliment is held back near a safety report.
assert r["messages"]["FB-030"]["praise"] == []
status = {d["id"]: d["status"] for d in r["working"]["drivers"]}
assert status["FB-004"] == "blocked", status   # the praising message itself reports a safety violation
assert status["FB-001"] == "check", status     # same route as FB-004's open safety report
assert status["FB-012"] == "eligible", status
assert r["working"]["turned"] == []

# Watch list: the same rider praises us, then complains later. Original ids and texts, so mock labels apply.
rows = {x["id"]: x for x in csv.DictReader(io.StringIO(CSV))}
pair = [dict(rows["FB-028"], rider_id="R-10853"), dict(rows["FB-007"], rider_id="R-10853")]
out = io.StringIO()
w = csv.DictWriter(out, fieldnames=server.COLUMNS)
w.writeheader()
w.writerows(pair)
turned = server.triage(out.getvalue())["working"]["turned"]
assert [(t["praised"], t["complained"]) for t in turned] == [("FB-028", "FB-007")], turned

# Live cost step, with a fake model (no SDK, no network): a cited id from another group is dropped.
def fake_model(cost_fails=False):
    def call(system, user, schema):
        if system == server.SYSTEM_PROMPT:
            return {"labels": [dict(lab, id=i) for i, lab in server.MOCK.items()]}
        if cost_fails:
            raise RuntimeError("model down")
        return {"groups": [{"group": "money", "cost_of_waiting": "Riders pay twice to get to work.",
                            "who_pays": ["riders"], "evidence_ids": ["FB-002", "FB-004"]}]}
    return call

orig_call = server.call_model
server.LIVE = True
try:
    server.call_model = fake_model()
    server.LABEL_CACHE.clear(); server.COST_CACHE.clear()
    rl = server.triage(CSV)
    assert rl["mode"] == "live" and rl["messages"]["FB-004"]["label"]["source"] == "model"
    money = next(g for g in rl["groups"] if g["key"] == "money")
    assert money["cost_source"] == "model" and money["cost"] == "Riders pay twice to get to work."
    assert money["cost_evidence"] == ["FB-002"], money["cost_evidence"]  # FB-004 is in the safety group
    assert rl["escalation"]["cost_source"] == "policy"  # not returned by the model: falls back to the written text
    assert not re.search(r"R-1\d{4}", json.dumps(rl)), "raw rider_id leaked in live mode"

    # Cost step fails: every group falls back to the written policy text and the page still builds.
    server.call_model = fake_model(cost_fails=True)
    server.LABEL_CACHE.clear(); server.COST_CACHE.clear()
    rf = server.triage(CSV)
    for g in [rf["escalation"]] + rf["groups"]:
        if g["key"] in ("none", "unlabelled", "other"):
            assert g["cost_source"] == "not_assessed", (g["key"], g["cost_source"])  # never sent to the model
            continue
        assert g["cost_source"] == "policy", (g["key"], g["cost_source"])
        assert g["cost"] == server.GROUPS[g["key"]]["cost"]

    # A failed cost call is not cached: once the model is back, the next load gets model costs.
    server.call_model = fake_model()
    rr = server.triage(CSV)
    assert next(g for g in rr["groups"] if g["key"] == "money")["cost_source"] == "model"
finally:
    server.call_model = orig_call
    server.LIVE = False
    server.LABEL_CACHE.clear(); server.COST_CACHE.clear()

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

# Safety is always severity 1, for humans too: a safety code with a lower severity is rejected.
try:
    server.save_override({"batch": r["batch"], "id": "FB-001", "code": "SAF-OTHER", "severity": 4, "note": "x"})
    raise AssertionError("safety code below severity 1 was accepted")
except ValueError:
    pass

# Cost overrides: a human edit wins, needs a note and an allowed payer, and lives alongside label overrides.
server.save_cost_override({"batch": r["batch"], "group": "money", "cost": "Three riders out of pocket today.",
                           "who_pays": ["riders", "support team"], "note": "checked with payments team"})
r5 = server.triage(CSV)
money = next(g for g in r5["groups"] if g["key"] == "money")
assert money["cost_source"] == "human" and money["cost"] == "Three riders out of pocket today."
assert money["who_pays"] == ["riders", "support team"]
assert r5["messages"]["FB-004"]["label"]["source"] == "human"  # the label override above still applies
for bad in ({"note": ""}, {"who_pays": ["passengers"]}):
    try:
        server.save_cost_override(dict({"batch": r["batch"], "group": "money", "cost": "x",
                                        "who_pays": ["riders"], "note": "n"}, **bad))
        raise AssertionError(f"bad cost override accepted: {bad}")
    except ValueError:
        pass

print("all checks passed")
