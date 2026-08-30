"""Entrypoint used by `guava run` and `uv run main.py`.

Runs Concierge, the voice-first travel planner in concierge_app/.

Usage: guava run . -- --chat | --local | --webrtc | --phone | --roleplay "PROMPT"
"""

from concierge_app.main import main

if __name__ == "__main__":
    main()
