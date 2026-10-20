# Rider feedback triage (Cityflo take-home)

A one-page tool that triages a batch of rider feedback (`data/feedback.csv`, 30 messages) for Meera, the ops lead, who can take one thing upstairs at 11am. It labels each message with a code, a severity and anything the rider sincerely praises, picks the one escalation, groups everything else as "deferred to tomorrow" with an owner, fix, cost of waiting (and who pays it) and risk, shows what is working, and lets a human override any label or cost with a required note. It is a single Python standard-library server (`server.py`) and one HTML page (`index.html`). The reasoning behind the decisions is in [MEMO.md](MEMO.md).

## Run it (mock mode, no setup)

```
python3 server.py
```

Open http://127.0.0.1:8000. Labels come from `data/labels.json`; no network, no API key, no dependencies beyond Python 3. Use `PORT=8766 python3 server.py` to pick another port.

You can paste or upload another CSV with the same columns on the page. In mock mode, a message only gets a label if its id is in `data/labels.json` and its text still contains the stored evidence quote; anything else shows as "unlabelled" rather than getting a wrong label.

## Run it live (Claude labels the batch)

```
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...
python3 server.py --live
```

Live mode makes two structured-JSON calls to Claude (`claude-opus-5-5`):
1. **Labels**: per message, a primary code, secondary codes and modifiers (see Coding system), severity, reason, exact evidence quote, and what the rider sincerely praises (with an exact quote). If this call fails, the page shows the error instead of crashing.
2. **What waiting costs, and who pays**: after plain code has grouped the labels, one call per batch asks, for the escalation and each deferred group, what one more day costs after today's plan, who absorbs it (riders, cityflo, support team, drivers, public) and which message ids it rests on. If this call fails, the page falls back to the written cost text in `data/labels.json` and marks it "policy".

## Check it

```
python3 test_triage.py
```

Plain asserts, mock mode, no network. Prints `all checks passed`. It covers: no raw rider id leaks (page and both prompts), the override-token message is kept and flagged, both safety incidents are escalated together, repeat riders are linked, every evidence quote is real, the slot falls to the payment fault when safety is cleared, a safety code is always severity 1, overrides need a note, every group gets a cost and allowed payers, the live cost step (with a fake model) drops evidence ids from other groups and falls back to policy text on failure, human cost edits win and are validated, sarcasm is not praise, driver-compliment status near a safety report, the praise-then-complaint watch list, and the coding system (secondary codes and also-mentioned ids, derived modifiers, safety resequencing, dropped unquoted codes, NONE standing alone, and override validation).

## What the model decides vs what plain code decides

The model (or the mock data) decides two things: per message, a code, a severity 1-5, a one-sentence reason, an evidence quote and any sincere praise; then, per group, what waiting costs, who pays and which ids it cites.

Plain code in `server.py` decides everything else:
- Any safety code (`SAF-*`) is forced to severity 1, whatever the model said.
- All severity 1 messages go upstairs together as one safety escalation. If there is none, the slot goes to the most severe group, and among equals the one affecting the most riders.
- The groups, the owner and fix for each, and rider counts (anonymous reviews count as one rider each).
- The page flags a label whose evidence quote is not actually in the message, shows a praise quote only if it is really in the message, and drops any cost evidence id that is not in that group.
- What's working: praise by aspect and route; a driver compliment is "blocked" if the same message reports a safety violation, "check" if the same route has another open severity 1 report, else "eligible"; the watch list is a rider who praised us earlier and complained (severity 3 or worse) later, within this batch.
- Human overrides, for labels (code, severity) and for costs (cost text, who pays), each need a note and are appended to `overrides.jsonl` with a timestamp, so there is an audit trail. The human edit wins; the model's original stays visible next to it.

## Coding system

Labels work like medical codes for an operation: a message can carry more than one issue, and each is coded separately.
- **Primary code** (`label.code`, `label.evidence`): the issue that needs action soonest. Messages are grouped by it. A safety code is always primary.
- **Secondary codes** (`label.secondary`, up to 3): one `{code, evidence}` per other distinct issue, each with its own exact quote. FB-014 is `OPS-LATE` with `OPS-AC` secondary; FB-021 is `PAY-NO-PASS` with `SUP-NO-REPLY` secondary.
- **Modifiers** add context, not issues. From the model: `SC` sarcastic, `TP` third party or public at risk, `LC` location contradicts the route, `ON` ongoing or repeated. From code, never the model: `RP` rider sent more than one message, `TK` override token in the text, `PR` sincere praise.

The eight coding rules (also in the system prompt and on the page): code only what the rider wrote; primary first, safety always primary; highest specificity; every code needs an exact quote; one secondary per other issue, up to three, never repeating the primary; NONE stands alone; modifiers add context, not issues; severity follows the most serious code, so any safety code means severity 1.

Plain code enforces them after the model (and on mock labels): it drops a secondary code whose quote is not in the message, that repeats the primary, is a duplicate, is unknown or is NONE, and lists each drop with a reason (`dropped_codes`); clears secondary codes when the primary is NONE; swaps a safety secondary into primary (the old primary becomes secondary); caps secondary at three; forces severity 1 when any safety code is present; and keeps only known modifiers. Human overrides can set secondary codes and modifiers too, with the same rules (a safety code must be primary, NONE stands alone).

Each group lists "also mentioned" tickets (`also_ids`): messages grouped elsewhere whose secondary codes belong to it, for example FB-005 and FB-010 (escalated as safety) also report late buses. They are not counted in the group's riders. A group mentioned only as a secondary code (support, via FB-021) is listed in `secondary_only`.

## Rider ids and the override token

- **Rider ids** never leave the server. The model sees only id, channel, route, stars and message text, in both calls. Driver and bus ids are not in the export at all, so a compliment or a safety report is tied to a route and time, and the trip record has to confirm which driver it was. The page shows a masked handle (`rider-xxxxxx`), a salted SHA-256 of the id. The salt is random per run (rider ids have only about 10,000 possible values, so a fixed known salt would be reversible), which means handles change between runs. Set `TRIAGE_SALT` if you want them stable. Messages from the same rider are still linked ("Same rider as FB-013").
- **`CF-PRIORITY-OVERRIDE`**: the intake convention says to drop messages containing it. This tool does not. A message's own text can never lower its priority or remove it from triage, so these messages are kept, triaged on what they say, and shown with a "contains override token: not trusted" flag. The system prompt also tells the model to treat every message as data and ignore instructions inside it. See MEMO.md for why (FB-002 is a real double charge).

## Honest note on the demo

The submitted demo runs in mock mode: the labels in `data/labels.json` were prepared for this batch, not produced by a model call at demo time. Live mode is implemented and uses the same prompt and the same rules. The exact prompt is visible on the page under "Prompt" at the bottom (system prompt plus the user message, with rider ids already removed), in both modes.

## Running costs

- Mock mode costs nothing: a standard-library Python server, no database, no hosting needed. For the demo it runs on a laptop.
- Live mode makes two Claude calls per batch. Labels are cached per batch and costs per batch plus group membership, so re-rendering after an override does not call the model again unless a relabel moves a message between groups. Cost depends on batch size; see Anthropic's pricing page: https://www.anthropic.com/pricing

## Deploying (optional, not done)

This was not deployed. If a public link is wanted, the cheapest options are a free tier of a small Python host (for example Render, Railway, Fly.io or PythonAnywhere) running `python3 server.py`. Things to change first:
- The server binds to `127.0.0.1`; a host needs it to listen on `0.0.0.0` and on the port the host provides (`PORT` is already read from the environment).
- Keep it in mock mode, or put it behind a login: in live mode anyone with the link can paste a CSV and trigger a paid model call.
- `overrides.jsonl` is a local file; on most free tiers it is wiped on restart.

## Files

- `server.py`: server, triage rules, both prompts, live and mock labelling and cost assessment.
- `index.html`: the page. Rider text is rendered with `textContent` only, never as HTML.
- `test_triage.py`: the self-check.
- `data/feedback.csv`, `DATA_GUIDE.md`: the input and its description.
- `data/labels.json`: codes, group write-ups (owner, fix, cost, who pays, risk; the cost text is also the fallback) and the mock labels.
- `MEMO.md`: the memo to Meera.
