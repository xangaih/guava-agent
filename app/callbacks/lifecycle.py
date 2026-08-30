import logging

import guava
from guava.events import AgentSpeechEvent, BotSessionEnded, CallerSpeechEvent

from app.agent import agent
from app.customer_lookup import lookup_by_phone
from app.status_store import append_transcript, call_ended, call_started

logger = logging.getLogger("app.lifecycle")


@agent.on_call_start
def on_call_start(call: guava.Call):
    logger.info("Call started (session: %s)", call.id)

    customer = None
    call_info = call.call_info
    if call_info.call_type == "pstn" and call_info.from_number:
        customer = lookup_by_phone(call_info.from_number)

    call_started(customer)

    if customer:
        call.set_variable("customer", customer)
        call.send_instruction(
            f"The caller has been identified as an existing customer: "
            f"name={customer['name']}, policy_number={customer['policy_number']}, "
            f"plan={customer['plan']}, member_since={customer['member_since']}. "
            "Greet them by name and mention you have their account pulled up. "
            "If they file a claim, you already have their policy number from "
            "their account, so you don't need to ask for it again."
        )
        greeting = guava.Say(
            f"Thanks for calling Harbor Mutual Insurance, this is Riley. "
            f"Hi {customer['name']}, I've got your account pulled up. "
            "How can I help you today?"
        )
    else:
        greeting = guava.Say(
            "Thanks for calling Harbor Mutual Insurance, this is Riley. "
            "How can I help you today?"
        )

    call.set_task(
        "greeting",
        objective=(
            "Greet the caller warmly as Riley from Harbor Mutual Insurance. "
            "Answer any policy questions they have, or help them file a claim "
            "if they want to report an incident."
        ),
        checklist=[greeting],
        completion_criteria=(
            "The caller has no more questions and is not trying to file a claim."
        ),
    )


@agent.on_task_complete("greeting")
def on_greeting_complete(call: guava.Call):
    call.hangup(final_instructions="Thank the caller for calling and say goodbye.")


@agent.on_caller_speech
def on_caller_speech(call: guava.Call, event: CallerSpeechEvent):
    append_transcript("caller", event.utterance)


@agent.on_agent_speech
def on_agent_speech(call: guava.Call, event: AgentSpeechEvent):
    append_transcript("agent", event.utterance)


@agent.on_session_end
def on_session_end(call: guava.Call, event: BotSessionEnded):
    logger.info(
        "Call ended (session: %s), reason: %s", call.id, event.termination_reason
    )
    call_ended()
