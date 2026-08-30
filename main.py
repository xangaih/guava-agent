"""Entrypoint used by `guava run` and `uv run main.py`.

Runs the Concierge travel planner by default. Set APP=claimline to run the older
Harbor Mutual insurance agent in app/ instead.

Usage: guava run . -- --chat | --local | --webrtc | --phone | --roleplay "PROMPT"
"""

import os

if os.environ.get("APP", "concierge").lower() == "claimline":
    from app.main import main
else:
    from concierge_app.main import main

if __name__ == "__main__":
    main()
