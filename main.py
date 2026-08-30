"""Entrypoint used by `guava run`. Dispatches to app/main.py (ClaimLine) or
concierge_app/main.py (Concierge) based on --agent. Both bind to the same
GUAVA_AGENT_NUMBER, so only run one at a time with --phone.

Usage: guava run . -- --agent claimline --phone   (default agent)
       guava run . -- --agent concierge --chat
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--agent", choices=["claimline", "concierge"], default="claimline")
    known, remaining = parser.parse_known_args()

    sys.argv = [sys.argv[0]] + remaining

    if known.agent == "concierge":
        from concierge_app.main import main as run
    else:
        from app.main import main as run
    run()


if __name__ == "__main__":
    main()
