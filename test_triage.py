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

# Multi-label coding: primary code first, secondary codes for other issues, "also mentioned" across groups.
m14 = r["messages"]["FB-014"]
assert m14["label"]["code"] == "OPS-LATE" and [s["code"] for s in m14["label"]["secondary"]] == ["OPS-AC"]
by_key = {g["key"]: g for g in [r["escalation"]] + r["groups"]}
assert {"FB-014", "FB-017"} <= set(by_key["ac"]["also_ids"]), by_key["ac"]["also_ids"]
assert {"FB-005", "FB-010"} <= set(by_key["late"]["also_ids"]), by_key["late"]["also_ids"]
assert not set(by_key["ac"]["also_ids"]) & set(by_key["ac"]["ids"])  # also-mentioned is never counted twice
assert "support" not in by_key
assert any(g["key"] == "support" and g["also_ids"] == ["FB-021"] for g in r["secondary_only"]), r["secondary_only"]
assert sum(g["ids"].count("FB-021") for g in by_key.values()) == 1
for m in r["messages"].values():  # every secondary code is documented by a real quote
    assert all(s["evidence"] in m["text"] for s in m["label"]["secondary"]), m["id"]
    assert m["dropped_codes"] == [], m["id"]

# Modifiers: model ones from the label, derived ones from code.
mods = {i: set(m["modifiers"]) for i, m in r["messages"].items()}
assert all("RP" in mods[i] for i in ("FB-005", "FB-010", "FB-013", "FB-021"))
assert all("TK" in mods[i] for i in ("FB-002", "FB-012"))
assert "PR" in mods["FB-001"] and "PR" not in mods["FB-030"]
assert {"TP", "LC", "ON"} <= mods["FB-005"] and "SC" in mods["FB-014"]
assert sum("RP" in v for v in mods.values()) == 4 and sum("TK" in v for v in mods.values()) == 2
assert len(r["coding_rules"]) == 8
assert set(r["modifiers"]) == {"SC", "TP", "LC", "ON", "RP", "TK", "PR"}

# Coding rules enforced by code on live output (fake model, no network).
FAKE = {
    # A safety issue coded as secondary is resequenced to primary, with severity 1.
    "FB-007": {"code": "OPS-LATE", "severity": 3, "evidence": "bus was 8 min late",
               "secondary": [{"code": "SAF-OTHER", "evidence": "missed my connection"}], "modifiers": ["XX", "ON"]},
    # A secondary code whose quote is not in the message is dropped and recorded; so is a repeat of the primary.
    "FB-009": {"code": "OPS-COMFORT", "severity": 4, "evidence": "bus was quite crowded today",
               "secondary": [{"code": "OPS-AC", "evidence": "the AC was freezing"},
                             {"code": "OPS-COMFORT", "evidence": "couldn't get my usual seat"}], "modifiers": []},
    # NONE stands alone.
    "FB-028": {"code": "NONE", "severity": 5, "evidence": "Love the service",
               "secondary": [{"code": "OPS-LATE", "evidence": "commute"}], "modifiers": []},
}
def coding_model(system, user, schema):
    if system == server.SYSTEM_PROMPT:
        return {"labels": [dict(lab, **FAKE.get(i, {}), id=i) for i, lab in server.MOCK.items()]}
    return {"groups": []}

server.LIVE = True
try:
    server.call_model = coding_model
    server.LABEL_CACHE.clear(); server.COST_CACHE.clear()
    rc = server.triage(CSV)
    m7 = rc["messages"]["FB-007"]
    assert m7["label"]["code"] == "SAF-OTHER" and m7["label"]["severity"] == 1
    assert m7["label"]["evidence"] == "missed my connection"
    assert m7["label"]["secondary"] == [{"code": "OPS-LATE", "evidence": "bus was 8 min late"}]
    assert m7["label"]["modifiers"] == ["ON"]  # unknown modifier dropped
    assert "FB-007" in rc["escalation"]["ids"]
    m9 = rc["messages"]["FB-009"]
    assert m9["label"]["secondary"] == []
    assert {d["code"] for d in m9["dropped_codes"]} == {"OPS-AC", "OPS-COMFORT"}, m9["dropped_codes"]
    m28 = rc["messages"]["FB-028"]
    assert m28["label"]["code"] == "NONE" and m28["label"]["secondary"] == []
    assert m28["dropped_codes"][0]["code"] == "OPS-LATE"
finally:
    server.call_model = orig_call
    server.LIVE = False
    server.LABEL_CACHE.clear(); server.COST_CACHE.clear()

# Overrides with secondary codes and modifiers.
server.save_override({"batch": r["batch"], "id": "FB-011", "code": "OPS-AC", "severity": 3, "note": "also late",
                      "secondary": ["OPS-LATE"], "modifiers": ["ON"]})
r6 = server.triage(CSV)
lab11 = r6["messages"]["FB-011"]["label"]
assert lab11["source"] == "human" and lab11["secondary"] == [{"code": "OPS-LATE", "evidence": ""}]
assert lab11["modifiers"] == ["ON"] and r6["messages"]["FB-011"]["modifiers"] == ["ON"]
assert "FB-011" in next(g for g in r6["groups"] if g["key"] == "late")["also_ids"]
for bad, msg in (({"code": "OPS-LATE", "secondary": ["SAF-OTHER"]}, "safety code first"),
                 ({"code": "NONE", "severity": 5, "secondary": ["OPS-LATE"]}, "NONE stands alone"),
                 ({"code": "OPS-LATE", "secondary": ["NONE"]}, "NONE stands alone"),
                 ({"code": "OPS-LATE", "secondary": ["OPS-LATE"]}, "Each code once"),
                 ({"code": "OPS-LATE", "secondary": ["BOGUS"]}, "valid secondary"),
                 ({"code": "OPS-LATE", "modifiers": ["RP"]}, "modifiers")):
    try:
        server.save_override(dict({"batch": r["batch"], "id": "FB-007", "severity": 3, "note": "n"}, **bad))
        raise AssertionError(f"bad override accepted: {bad}")
    except ValueError as e:
        assert msg in str(e), (bad, e)

print("all checks passed")
