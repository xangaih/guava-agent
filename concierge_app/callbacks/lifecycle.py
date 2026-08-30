import logging

import guava
from guava.events import AgentSpeechEvent, BotSessionEnded, CallerSpeechEvent

from concierge_app import status_store
from concierge_app.agent import agent
from concierge_app.callbacks.profile_intake import start_trip_intake

logger = logging.getLogger("concierge.lifecycle")


@agent.on_call_start
def on_call_start(call: guava.Call):
    logger.info("Call started (session: %s)", call.id)
    status_store.call_started()
    start_trip_intake(call)


@agent.on_caller_speech
def on_caller_speech(call: guava.Call, event: CallerSpeechEvent):
    status_store.append_transcript("caller", event.utterance)


@agent.on_agent_speech
def on_agent_speech(call: guava.Call, event: AgentSpeechEvent):
    status_store.append_transcript("agent", event.utterance)


@agent.on_session_end
def on_session_end(call: guava.Call, event: BotSessionEnded):
    logger.info(
        "Call ended (session: %s), reason: %s", call.id, event.termination_reason
    )
    status_store.call_ended()
