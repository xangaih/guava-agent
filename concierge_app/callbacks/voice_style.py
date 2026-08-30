"""Match the caller's register instead of asking them to choose one.

Nobody calls to book a trip and picks a voice from a menu, so there is no menu.
Connie opens in the neutral register, listens to how the caller actually talks, and
quietly shifts to match them. A caller who says "omg girl I wanna go to Tokyo" gets
the Gen Z Connie; one who says "Good morning, I would like to arrange a trip" gets
the slow, careful one.

Switches are silent and never announced - the caller should feel understood, not
handled. An explicit request ("can you slow down") locks the style so detection
stops second-guessing them.
"""

import logging

import guava
from guava.events import CallerSpeechEvent

from concierge_app import db, style_detect, voice_styles
from concierge_app.agent import agent
from concierge_app.callbacks.profile_intake import start_trip_intake

logger = logging.getLogger("concierge.voice_style")

# Per-call speech buffers: {call_id: {utterance_id: latest_text}}. Transcription sends
# repeated events for one utterance as it is revised, so we key on utterance_id and
# keep the newest version rather than appending every partial.
_utterances: dict[str, dict[str, str]] = {}

# Adapt at most this many times per call - past that it reads as unstable.
MAX_ADAPTATIONS = 2


def start_welcome(call: guava.Call, caller_name: str | None = None):
    """Open the call. We ask who is calling - normal for a booking - and nothing else."""
    voice_styles.apply(call, voice_styles.get(voice_styles.DEFAULT_STYLE), caller_name)

    if caller_name:
        start_trip_intake(call)
        return

    call.set_task(
        "welcome",
        objective=(
            "Say hi, give your name, and ask theirs - one short, ordinary line, the way a "
            "person actually answers the phone. Under fifteen words. Do not explain what you "
            "do, do not offer a menu of services, and do not be formal about it. They called "
            "to plan a trip, so do not hold them up."
        ),
        checklist=[
            guava.Field(
                key="caller_name",
                field_type="text",
                description="The caller\'s first name, so Connie can address them by it",
            ),
        ],
        completion_criteria="We know what to call the caller.",
    )


@agent.on_task_complete("welcome")
def on_welcome_complete(call: guava.Call):
    caller_name = call.get_field("caller_name") or call.get_variable("caller_name")
    if caller_name:
        call.set_variable("caller_name", caller_name)
        traveler_id = call.get_variable("traveler_id")
        if traveler_id:
            db.set_traveler_name(traveler_id, caller_name)

    # Re-apply so the name lands in the persona; style is whatever we have inferred so far.
    voice_styles.apply(call, voice_styles.get(call.get_variable("voice_style")), caller_name)
    start_trip_intake(call)


@agent.on_caller_speech
def on_caller_speech(call: guava.Call, event: CallerSpeechEvent):
    """Listen to how the caller talks and quietly match their register."""
    if not event.utterance:
        return

    buffer = _utterances.get(call.id)
    if buffer is None:
        buffer = _utterances[call.id] = {}
        logger.info("Register detection is live on this channel (first utterance received)")
    buffer[event.utterance_id or str(len(buffer))] = event.utterance

    if call.get_variable("style_locked"):
        return  # the caller told us what they want; stop inferring
    if (call.get_variable("style_adaptations") or 0) >= MAX_ADAPTATIONS:
        return

    detected = style_detect.classify(list(buffer.values()))
    current = call.get_variable("voice_style") or voice_styles.DEFAULT_STYLE
    if not detected or detected == current:
        return

    style = voice_styles.get(detected)
    voice_styles.apply(call, style, call.get_variable("caller_name"))
    call.set_variable("style_adaptations", (call.get_variable("style_adaptations") or 0) + 1)
    logger.info("Matched caller register: %s -> %s", current, detected)

    traveler_id = call.get_variable("traveler_id")
    if traveler_id:
        db.set_voice_style(traveler_id, style.key)


def switch_style(call: guava.Call, requested: str | None) -> voice_styles.VoiceStyle:
    """Honor an explicit request ("slow down", "be more chill") and stop auto-adapting."""
    style = voice_styles.get(requested)
    voice_styles.apply(call, style, call.get_variable("caller_name"))
    call.set_variable("style_locked", True)
    traveler_id = call.get_variable("traveler_id")
    if traveler_id:
        db.set_voice_style(traveler_id, style.key)
    logger.info("Caller explicitly requested %s; style locked", style.key)
    return style


def forget_call(call_id: str):
    _utterances.pop(call_id, None)
