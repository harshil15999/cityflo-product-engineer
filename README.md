# Rider feedback triage (Cityflo take-home)

**Try the mock version:** https://harshil15999.github.io/cityflo-product-engineer/

A read-only static demo with mock labels. Run it locally for the full tool: changing labels, editing costs, loading a new batch and live mode.

## What it does

Thirty untriaged rider messages land at 9:40am; standup is at 11. The tool turns them into one decision and a priced backlog:

- **One thing to escalate**, with a "Why today" built from the batch. Here: driver safety (rash overtaking at a school crossing; a driver watching a movie on the highway).
- **What to fix today** without escalating: money taken with no pass delivered, and late buses.
- **Everything else, deferred at a known cost**: owner, fix, cost of waiting a day, who pays, risk.
- **What's working**: praise, driver compliments safe to reward, and a watch list.
- **Labels a human can check and change**: primary and secondary codes plus a 7-position event code (e.g. `S-D-U-S-M-P-R`), each backed by the rider's exact words, changeable through a guided form with a required reason.

Safety is always severity 1, rider ids never leave the server, and a message's own text can never hide it from triage.

## Who it's for

**Meera, the ops lead**, who can take exactly one thing upstairs at 11 and needs the cost of sitting on the rest. Present mode shows the same answer in large type for the meeting room. The reasoning is in [MEMO.md](MEMO.md), which opens with a one-page answer.

## Set it up locally

Needs only Python 3.

```
git clone https://github.com/harshil15999/cityflo-product-engineer.git
cd cityflo-product-engineer
python3 server.py
```

Open http://127.0.0.1:8000. Mock mode reads labels from `data/labels.json`: no network, no API key. `PORT=8766 python3 server.py` picks another port.

**Live mode** (Claude labels the batch):

```
pip install -r requirements.txt
read -rs ANTHROPIC_API_KEY && export ANTHROPIC_API_KEY   # not echoed or saved to history
python3 server.py --live
```

The key is read from the environment only; it is never written, logged or sent to the page.

**Self-check:** `python3 test_triage.py` (mock mode, no network) prints `all checks passed`.

**Static demo:** `python3 server.py --export demo.json` regenerates the file GitHub Pages serves when there's no server.

## How it decides

- **The model** (or mock data) labels each message: codes, severity, reason, exact evidence quote, sincere praise. A second call writes each group's cost of waiting and who pays, citing message ids. Both prompts are visible on the page.
- **Plain code** decides the rest: safety is forced to severity 1; all severity 1 goes up as one escalation (otherwise the most severe group hitting the most riders); "Why today", groups, owners and rider counts; every quote is checked against the message; the commute window and repeat/corroboration come from timestamps and the batch.
- **Humans** can override any label or cost with a required note, saved to `overrides.jsonl` as an audit trail.

The full coding rules and the event-code legend are in the page's **Coding rules** dialog.

## Privacy and untrusted text

- Rider ids never reach the model or the page; the page shows a salted, masked handle.
- Messages containing `CF-PRIORITY-OVERRIDE` are kept and flagged, not dropped (FB-002 is a real double charge; see MEMO.md).
- Rider text is rendered with `textContent` only and treated as data in prompts.

## Optional extras

- **Fast read**: header button, off by default, bolds word starts for faster scanning.
- **Usage analytics**: self-hosted [GoatCounter](https://github.com/arp242/goatcounter), off unless started. It records feature names only (never rider text, ids or search terms). Run GoatCounter on `127.0.0.1:8081`, then `ANALYTICS_URL=http://127.0.0.1:8081 python3 server.py`; a **Usage** button then opens its dashboard.

## Files

`server.py` (server, rules, prompts) · `index.html` (the page) · `test_triage.py` · `data/feedback.csv` and `DATA_GUIDE.md` (input) · `data/labels.json` (codes, event tables, group write-ups, mock labels) · `demo.json` (static demo data) · `MEMO.md` · `decisions.jsonl`.

**For reviewers:** `decisions.jsonl` quotes messages the candidate typed, anchored as `turn N (transcript line L)`: N counts only typed prompts, L is the line in the raw `.jsonl` transcript. Decisions typed mid-task are anchored as `message sent mid-turn (transcript line L)`.
