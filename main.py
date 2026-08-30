"""Entrypoint used by `guava run`. Delegates to app/main.py.

Usage: guava run . -- --chat | --local | --webrtc | --phone | --roleplay "PROMPT"
"""

from app.main import main

if __name__ == "__main__":
    main()
