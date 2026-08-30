import logging

import guava
from guava.events import BotSessionEnded

from app.agent import agent

logger = logging.getLogger("app.lifecycle")


@agent.on_call_start
def on_call_start(call: guava.Call):
    logger.info("Call started (session: %s)", call.id)
    call.set_task(
        "greeting",
        objective=(
            "Greet the caller warmly as Riley from Harbor Mutual Insurance. "
            "Answer any policy questions they have, or help them file a claim "
            "if they want to report an incident."
        ),
        checklist=[
            guava.Say(
                "Thanks for calling Harbor Mutual Insurance, this is Riley. "
                "How can I help you today?"
            ),
        ],
        completion_criteria=(
            "The caller has no more questions and is not trying to file a claim."
        ),
    )


@agent.on_task_complete("greeting")
def on_greeting_complete(call: guava.Call):
    call.hangup(final_instructions="Thank the caller for calling and say goodbye.")


@agent.on_session_end
def on_session_end(call: guava.Call, event: BotSessionEnded):
    logger.info(
        "Call ended (session: %s), reason: %s", call.id, event.termination_reason
    )
