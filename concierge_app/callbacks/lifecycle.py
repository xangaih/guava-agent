import logging

import guava
from guava.events import BotSessionEnded

from concierge_app.agent import agent
from concierge_app.callbacks.profile_intake import start_trip_intake

logger = logging.getLogger("concierge.lifecycle")


@agent.on_call_start
def on_call_start(call: guava.Call):
    logger.info("Call started (session: %s)", call.id)
    start_trip_intake(call)


@agent.on_session_end
def on_session_end(call: guava.Call, event: BotSessionEnded):
    logger.info(
        "Call ended (session: %s), reason: %s", call.id, event.termination_reason
    )
