# ClaimLine

An inbound voice agent for Harbor Mutual Insurance (fictional) built on Guava.
Callers can ask free-form policy questions (RAG over `app/data/policy_faq.md`)
or say they want to file a claim, at which point the agent switches into a
structured intake flow — policy number (redacted as sensitive), incident
date, description, and callback number (read back to confirm) — then saves
the claim to a local SQLite database and reads back a confirmation code.

This is the regulated-industry pitch: sensitive fields never appear in stored
transcripts or call audio, and claim data is captured as structured, auditable
fields instead of a freeform transcript an adjuster has to re-parse.

## Project layout

```
app/
├── agent.py                 # guava.Agent(...) instantiation
├── main.py                  # entrypoint: --phone / --webrtc / --local / --chat / --roleplay
├── env.py                   # loads .env into os.environ
├── storage.py                # sqlite helpers: init_db(), save_claim(), list_claims()
├── callbacks/
│   ├── lifecycle.py          # on_call_start, on_task_complete("greeting"), on_session_end
│   ├── questions.py          # on_question -> DocumentQA (RAG)
│   ├── actions.py            # on_action_request / on_action -> IntentRecognizer
│   └── claim_intake.py       # set_task checklist + on_task_complete("file_claim")
└── data/
    └── policy_faq.md          # fictional insurer FAQ, feeds DocumentQA
tests/
└── test_roleplay.py          # agent.roleplay() smoke tests
```

## Running it

Set `GUAVA_AGENT_NUMBER` and (optionally) `GUAVA_API_KEY` in `.env` — see
`.env` in this repo (gitignored). Then, from this directory:

```bash
uv run main.py -- --chat        # fastest iteration loop, curses text chat
uv run main.py -- --local       # real audio via laptop mic/speakers
uv run main.py -- --webrtc      # browser call via app.goguava.ai/debug-webrtc
uv run main.py -- --phone       # listen on GUAVA_AGENT_NUMBER — call it for real
uv run main.py -- --roleplay "You are a caller asking about deductibles"
```

or equivalently `guava run . -- --chat` (etc).

Run the automated regression checks with:

```bash
python -m tests.test_roleplay
```

Inspect saved claims with:

```bash
sqlite3 claims.db "select * from claims;"
```

## Demo script (~2 minutes)

1. Dial the agent's number (or open the WebRTC debug link as backup).
2. Ask a policy question, e.g. "What's my deductible?" — the RAG answer
   comes from `policy_faq.md`.
3. Say "I'd like to file a claim" — the agent detects the intent and
   switches into structured intake.
4. Give a policy number, incident date, and description, and confirm the
   callback number when it's read back. Call out that the policy number
   won't appear in the stored transcript because it's a `sensitive` field.
5. Let it read back the confirmation number and hang up.
6. Show the row in `claims.db`.
