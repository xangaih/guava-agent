import logging
from pathlib import Path

import guava
from guava.helpers.rag import DocumentQA

from app.agent import agent

logger = logging.getLogger("app.questions")

FAQ_PATH = Path(__file__).resolve().parent.parent / "data" / "policy_faq.md"

document_qa = DocumentQA(
    documents=FAQ_PATH.read_text(),
    namespace="harbor-mutual-policy-faq",
)


@agent.on_question
def on_question(call: guava.Call, question: str) -> str:
    logger.info("Question received: %s", question)
    answer = document_qa.ask(question)
    logger.info("Answering: %s", answer)
    return answer
