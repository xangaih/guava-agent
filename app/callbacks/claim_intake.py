import logging

import guava

from app.agent import agent
from app.storage import save_claim

logger = logging.getLogger("app.claim_intake")


def start_claim_intake(call: guava.Call):
    call.set_task(
        "file_claim",
        objective="Collect the details needed to open a claim.",
        checklist=[
            guava.Field(
                key="policy_number",
                field_type="digit_sequence",
                sensitive=True,
                description="The caller's policy number",
            ),
            guava.Field(
                key="incident_date",
                field_type="date",
                description="When the incident happened",
            ),
            guava.Field(
                key="description",
                field_type="text",
                description="What happened, in the caller's own words",
            ),
            guava.Field(
                key="callback_number",
                field_type="text",
                description="Best number to reach them at",
            ),
            "Read the callback number back to the caller to confirm.",
        ],
    )


@agent.on_task_complete("file_claim")
def on_claim_complete(call: guava.Call):
    incident_date = call.get_field("incident_date")
    fields = {
        "policy_number": call.get_field("policy_number"),
        "incident_date": (
            "{year:04d}-{month:02d}-{day:02d}".format(**incident_date)
            if incident_date
            else None
        ),
        "description": call.get_field("description"),
        "callback_number": call.get_field("callback_number"),
    }
    confirmation_code = save_claim(call.id, fields)
    logger.info("Claim saved, confirmation code: %s", confirmation_code)
    call.hangup(
        final_instructions=(
            f"Tell the caller their confirmation number is {confirmation_code}, "
            "thank them, then say goodbye."
        )
    )
