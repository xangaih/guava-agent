import logging

import guava
from guava import SuggestedAction
from guava.helpers.llm import IntentRecognizer

from app.agent import agent
from app.callbacks.claim_intake import start_claim_intake

logger = logging.getLogger("app.actions")

ACTIONS = {
    "file_claim": "The caller wants to open or file a new insurance claim.",
}
intent_recognizer = IntentRecognizer(ACTIONS)


@agent.on_action_request
def on_action_request(call: guava.Call, request: str) -> list[SuggestedAction] | None:
    logger.info("Action request received: %s", request)
    return intent_recognizer.classify(request)


@agent.on_action("file_claim")
def on_file_claim(call: guava.Call):
    logger.info("Starting claim intake for call %s", call.id)
    start_claim_intake(call)
