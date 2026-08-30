https://docs.google.com/document/d/1VkowDoy3_s9TxPnSTHmZk6c9PrAD9MfwtbEYuRB71bs/edit?usp=sharing


# ClaimLine

An inbound voice agent for Harbor Mutual Insurance (fictional) built on Guava.
Callers can ask free-form policy questions (RAG over `app/data/policy_faq.md`)
or say they want to file a claim, at which point the agent switches into a
structured intake flow — policy number (redacted as sensitive), incident
date, description, and callback number (read back to confirm) — then saves
the claim to a local SQLite database and reads back a confirmation code. A
recognized caller (matched by phone number against a mock CRM) is greeted by
name and doesn't have to re-establish who they are.

This is the regulated-industry pitch: sensitive fields never appear in stored
transcripts or call audio, policy numbers are stored masked (last 3 digits
only) even in our own local database, and claim data is captured as
structured, auditable fields instead of a freeform transcript an adjuster has
to re-parse.

## Project layout

```
app/
├── agent.py                 # guava.Agent(...) instantiation
├── main.py                  # entrypoint: --phone / --webrtc / --local / --chat / --roleplay
├── env.py                   # loads .env into os.environ
├── storage.py                # sqlite helpers: init_db(), save_claim(), list_claims()
├── customer_lookup.py        # mock CRM lookup by phone / policy number
├── status_store.py           # file-backed call status + transcript, shared with dashboard.py
├── callbacks/
│   ├── lifecycle.py          # on_call_start (+ caller recognition), on_session_end, speech events
│   ├── questions.py          # on_question -> DocumentQA (RAG)
│   ├── actions.py            # on_action_request / on_action -> IntentRecognizer
│   └── claim_intake.py       # set_task checklist + on_task_complete("file_claim")
└── data/
    ├── policy_faq.md          # fictional insurer FAQ, feeds DocumentQA
    └── customers.json         # mock CRM: one seeded caller for live-demo recognition
tests/
└── test_roleplay.py          # agent.roleplay() smoke tests
dashboard.py                   # judge-facing local dashboard (FastAPI), separate process
static/index.html              # dashboard frontend, polls dashboard.py every 1.5s
```

## Running it

Set `GUAVA_AGENT_NUMBER` and (optionally) `GUAVA_API_KEY` in `.env` — see
`.env` in this repo (gitignored). Then, from this directory:

```bash
uv run main.py --chat        # fastest iteration loop, curses text chat
uv run main.py --local       # real audio via laptop mic/speakers
uv run main.py --webrtc      # browser call via app.goguava.ai/debug-webrtc
uv run main.py --phone       # listen on GUAVA_AGENT_NUMBER — call it for real
uv run main.py --roleplay "You are a caller asking about deductibles"
```

or equivalently `guava run . -- --chat` (etc, using `guava run`'s own `--` separator).

Run the automated regression checks with:

```bash
python -m tests.test_roleplay
```

Inspect saved claims with:

```bash
sqlite3 claims.db "select * from claims;"
```

### Dashboard (optional, judge-facing)

Runs as a fully separate process from the agent — if it crashes, the phone
demo is unaffected. It reads `claims.db` and `call_status.json`, both written
by the agent process.

```bash
uv run uvicorn dashboard:app --port 8787
```

Then open `http://localhost:8787` in a browser. It shows live call status,
the recognized caller's name/plan (if any), a live-scrolling transcript, and
the claims table with policy numbers masked.

Caller recognition only works over a real PSTN call (`--phone`) — `--local`,
`--chat`, `--webrtc`, and `--roleplay` never carry a real caller phone number,
so they always behave as an unrecognized caller. To see personalized
recognition live, call from the number seeded in `app/data/customers.json`.

## Demo script (~2 minutes)

1. Dial the agent's number (or open the WebRTC debug link as backup). If
   calling from the seeded demo number, point out the personalized greeting
   and that the dashboard already shows the caller's name/plan.
2. Ask a policy question, e.g. "What's my deductible?" — the RAG answer
   comes from `policy_faq.md`.
3. Say "I'd like to file a claim" — the agent detects the intent and
   switches into structured intake.
4. Give a policy number, incident date, and description, and confirm the
   callback number when it's read back. Call out that the policy number
   won't appear in the stored transcript because it's a `sensitive` field,
   and that it's stored masked in `claims.db` too.
5. Let it read back the confirmation number and hang up.
6. Show the row landing live on the dashboard's claims table (or in
   `claims.db` directly).
