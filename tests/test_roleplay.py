"""Roleplay smoke test: run with `python -m tests.test_roleplay`."""

from app.env import load_env

load_env()

import app.callbacks.lifecycle  # noqa: F401
import app.callbacks.questions  # noqa: F401
import app.callbacks.actions  # noqa: F401
from app.agent import agent
from app.storage import init_db


def test_faq_question():
    init_db()
    session = agent.roleplay(
        "You are a caller who asks the agent what your homeowners deductible is, "
        "then says thank you and goodbye."
    )
    session.evaluate(
        pass_criteria=[
            "The agent stated a homeowners deductible amount from the policy FAQ."
        ],
    )
    print("PASS: test_faq_question")
    print(session.get_transcript())


def test_file_claim():
    init_db()
    session = agent.roleplay(
        "You are a caller who wants to file a claim. When asked, give a policy "
        "number of 555123, say the incident happened yesterday, describe a "
        "burst pipe that flooded your kitchen, and give a callback number of "
        "555-867-5309. Confirm the callback number when asked."
    )
    session.evaluate(
        pass_criteria=[
            "The agent collected claim details and gave the caller a confirmation code."
        ],
    )
    print("PASS: test_file_claim")
    print(session.get_transcript())


if __name__ == "__main__":
    test_faq_question()
    test_file_claim()
