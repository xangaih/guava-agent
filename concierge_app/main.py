import argparse
import os

from app.env import load_env
from app.logging_setup import setup as setup_logging

load_env()

from concierge_app.agent import agent
from concierge_app.db import init_db

import concierge_app.callbacks.voice_style  # noqa: F401
import concierge_app.callbacks.lifecycle  # noqa: F401
import concierge_app.callbacks.questions  # noqa: F401
import concierge_app.callbacks.planning_actions  # noqa: F401


def main():
    parser = argparse.ArgumentParser()
    channel = parser.add_mutually_exclusive_group(required=True)
    channel.add_argument("--phone", action="store_true", help="Listen on GUAVA_AGENT_NUMBER")
    channel.add_argument("--webrtc", action="store_true", help="Listen for WebRTC calls")
    channel.add_argument("--local", action="store_true", help="Talk via laptop mic/speakers")
    channel.add_argument("--chat", action="store_true", help="Text-only chat in the terminal")
    channel.add_argument("--roleplay", metavar="PROMPT", help="LLM plays the caller")
    args = parser.parse_args()

    setup_logging()
    init_db()

    if args.phone:
        agent.listen_phone(os.environ["GUAVA_AGENT_NUMBER"])
    elif args.webrtc:
        agent.listen_webrtc()
    elif args.local:
        agent.call_local()
    elif args.chat:
        agent.chat()
    elif args.roleplay:
        agent.roleplay(args.roleplay)


if __name__ == "__main__":
    main()
