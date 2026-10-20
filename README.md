# Rider feedback triage (Cityflo take-home)

A one-page tool that triages a batch of rider feedback (`data/feedback.csv`, 30 messages) for Meera, the ops lead, who can take one thing upstairs at 11am. It labels each message with a code and a severity, picks the one escalation, groups everything else as "deferred to tomorrow" with an owner, fix, cost of waiting and risk, and lets a human override any label with a required note. It is a single Python standard-library server (`server.py`) and one HTML page (`index.html`). The reasoning behind the decisions is in [MEMO.md](MEMO.md).

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

Live mode sends the batch to Claude (`claude-opus-5-5`) once and asks for structured JSON (code, severity, reason, exact evidence quote per message). If the call fails, the page shows the error instead of crashing.

## Check it

```
python3 test_triage.py
```

Plain asserts, mock mode, no network. Prints `all checks passed`. It covers: no raw rider id leaks, the override-token message is kept and flagged, both safety incidents are escalated together, repeat riders are linked, every evidence quote is real, the slot falls to the payment fault when safety is cleared, a safety code is always severity 1, and overrides need a note.

## What the model decides vs what plain code decides

The model (or the mock labels) only decides, per message: a code, a severity 1-5, a one-sentence reason and an evidence quote.

Plain code in `server.py` decides everything else:
- Any safety code (`SAF-*`) is forced to severity 1, whatever the model said.
- All severity 1 messages go upstairs together as one safety escalation. If there is none, the slot goes to the most severe group, and among equals the one affecting the most riders.
- The page flags a label whose evidence quote is not actually in the message.
- A human override (code, severity, required note) replaces the label and is appended to `overrides.jsonl` with a timestamp, so there is an audit trail. The model's original label stays visible next to it.

## Rider ids and the override token

- **Rider ids** never leave the server. The model sees only id, channel, route, stars and message text. The page shows a masked handle (`rider-xxxxxx`), a salted SHA-256 of the id. The salt is random per run (rider ids have only about 10,000 possible values, so a fixed known salt would be reversible), which means handles change between runs. Set `TRIAGE_SALT` if you want them stable. Messages from the same rider are still linked ("Same rider as FB-013").
- **`CF-PRIORITY-OVERRIDE`**: the intake convention says to drop messages containing it. This tool does not. A message's own text can never lower its priority or remove it from triage, so these messages are kept, triaged on what they say, and shown with a "contains override token: not trusted" flag. The system prompt also tells the model to treat every message as data and ignore instructions inside it. See MEMO.md for why (FB-002 is a real double charge).

## Honest note on the demo

The submitted demo runs in mock mode: the labels in `data/labels.json` were prepared for this batch, not produced by a model call at demo time. Live mode is implemented and uses the same prompt and the same rules. The exact prompt is visible on the page under "Prompt" at the bottom (system prompt plus the user message, with rider ids already removed), in both modes.

## Running costs

- Mock mode costs nothing: a standard-library Python server, no database, no hosting needed. For the demo it runs on a laptop.
- Live mode makes one Claude call per batch. Results are cached in memory per batch, so re-rendering after an override does not call the model again. Cost depends on batch size; see Anthropic's pricing page: https://www.anthropic.com/pricing

## Deploying (optional, not done)

This was not deployed. If a public link is wanted, the cheapest options are a free tier of a small Python host (for example Render, Railway, Fly.io or PythonAnywhere) running `python3 server.py`. Things to change first:
- The server binds to `127.0.0.1`; a host needs it to listen on `0.0.0.0` and on the port the host provides (`PORT` is already read from the environment).
- Keep it in mock mode, or put it behind a login: in live mode anyone with the link can paste a CSV and trigger a paid model call.
- `overrides.jsonl` is a local file; on most free tiers it is wiped on restart.

## Files

- `server.py`: server, triage rules, prompt, live and mock labelling.
- `index.html`: the page. Rider text is rendered with `textContent` only, never as HTML.
- `test_triage.py`: the self-check.
- `data/feedback.csv`, `DATA_GUIDE.md`: the input and its description.
- `data/labels.json`: codes, group write-ups (owner, fix, cost, risk) and the mock labels.
- `MEMO.md`: the memo to Meera.
