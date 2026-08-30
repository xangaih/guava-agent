import logging

import guava
from guava.events import AgentSpeechEvent, BotSessionEnded, CallerSpeechEvent

from concierge_app import db, status_store, voice_styles
from concierge_app.agent import agent
from concierge_app.callbacks.profile_intake import caller_phone, start_trip_intake
from concierge_app.callbacks.voice_style import forget_call, start_welcome

logger = logging.getLogger("concierge.lifecycle")


@agent.on_call_start
def on_call_start(call: guava.Call):
    logger.info("Call started (session: %s)", call.id)
    status_store.call_started()

    traveler = db.find_traveler_by_phone(caller_phone(call))
    saved_style = db.get_voice_style(traveler["id"]) if traveler else None
    caller_name = (traveler or {}).get("name")

    if traveler:
        call.set_variable("traveler_id", traveler["id"])
    if caller_name:
        call.set_variable("caller_name", caller_name)

    if saved_style:
        # Returning caller - open in the voice and name they already gave us, no questions.
        voice_styles.apply(call, voice_styles.get(saved_style), caller_name)
        logger.info("Returning caller %s, restoring style %s", caller_name, saved_style)
        start_trip_intake(call)
    else:
        # Inbound stranger - the agent has to ask who this is anyway, so ask the
        # style preference in the same breath, then plan the trip in that voice.
        start_welcome(call, caller_name)


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
    forget_call(call.id)
