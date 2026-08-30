https://docs.google.com/document/d/1VkowDoy3_s9TxPnSTHmZk6c9PrAD9MfwtbEYuRB71bs/edit?usp=sharing


# Concierge

A voice-first travel planning agent built on Guava. Callers dial in and plan a
trip out loud: Connie proposes hotels, restaurants, and experiences against a
real budget, tracks the itinerary in SQLite, and offers concrete tradeoffs when
something would push the trip over budget.

The distinguishing feature is that **Connie matches how you talk**. Rather than
asking callers to pick a voice, she opens in a neutral register, listens to the
caller's own words, and shifts to match them - a caller who opens with "yo, i
wanna go to kyoto" gets a Gen Z register; one who opens with "Good morning, I
would like to arrange a trip" gets a slower, careful one that repeats details
back. Switches are silent, and an explicit request ("slow down") locks the style.

## Project layout

```
concierge_app/
├── agent.py                  # guava.Agent(...) instantiation
├── main.py                   # entrypoint: --phone / --webrtc / --local / --chat / --roleplay
├── env.py                    # loads .env from the repo root into os.environ
├── logging_setup.py          # guava logging config
├── db.py                     # sqlite schema, seed data, traveler/trip/itinerary helpers
├── voice_styles.py           # the three registers + set_persona() composition
├── style_detect.py           # lexical register detection from caller speech
├── callbacks/
│   ├── lifecycle.py          # on_call_start (+ returning-caller recognition), on_session_end
│   ├── voice_style.py        # welcome task, on_caller_speech register matching
│   ├── questions.py          # on_question
│   ├── planning_actions.py   # on_action_request / on_action -> IntentRecognizer
│   └── profile_intake.py     # trip intake checklist + on_task_complete("trip_intake")
└── specialists/
    ├── hotels.py, restaurants.py, experiences.py   # inventory proposals
    └── budget.py             # category splits, tradeoff generation
concierge_dashboard.py         # judge-facing local dashboard (FastAPI), separate process
concierge_static/index.html    # dashboard frontend
```

## Running it

Set `GUAVA_API_KEY` and `GUAVA_AGENT_NUMBER` in `.env` **at the repo root**
(gitignored). `--phone` listens on whatever `GUAVA_AGENT_NUMBER` is set to.

```bash
guava run . -- --chat        # fastest iteration loop, text chat
guava run . -- --local       # real audio via laptop mic/speakers
guava run . -- --webrtc      # browser call via app.goguava.ai/debug-webrtc
guava run . -- --phone       # listen on GUAVA_AGENT_NUMBER - call it for real
guava run . -- --roleplay "You are a caller who wants a week in Kyoto"
```

Run the dashboard in a second terminal: `uv run concierge_dashboard.py`.

## Voice styles

Three registers, all on the same `grace` TTS voice and the same identity
(Connie / Concierge) - only the persona prose changes, via `call.set_persona()`.

| Style | Register |
|---|---|
| `genz` | Heavy slang, short sentences, reacts before recommending |
| `friendly` | Everyday American, warm, no slang - the default every call opens in |
| `steady` | Slow and clear, one option at a time, repeats names and numbers back |

Detection lives in `style_detect.py` and is deliberately lexical rather than an
LLM call, since it runs on every utterance: it has to be instant, free, and
deterministic enough to unit test. It abstains rather than guessing when the
evidence is thin, so a neutral caller simply stays in `friendly`.

To see recognition of a returning caller, call twice from the same number - the
second call opens already knowing your name and your register.
