"""
This module defines the evaluation process for the ReservationAgent using ragas.
The evaluation includes both retrieval and generation metrics to assess the agent's performance in providing
accurate and relevant parking information based on user queries.

The evaluation dataset conatins the following benchmarks:
- Retrieval accuracy (context_recall): Assesses whether the retrieval step returns the correct supporting documents.
- Faithfulness: Checks if the generated answer is grounded in the retrieved context (i.e., not hallucinated).
- Answer relevancy: Evaluates how relevant the generated answer is to the user’s question.
- Answer correctness: Measures if the answer is factually correct, often compared to a ground-truth answer.
- Context relevancy: Measures how relevant the retrieved documents are to the query.
"""

import json
import re
import time
from dataclasses import dataclass

import pandas as pd
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas import EvaluationDataset, evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import answer_correctness, answer_relevancy, context_recall, faithfulness

from chat_engine.core.agents.apsr_agent import APSRAgent
from chat_engine.core.agents.agent_models import ApsrSessionContext

DEFAULT_SESSION_CONTEXT = ApsrSessionContext(
    authenticated=True,
    username="john.doe",
    thread_id="eval-01",
    vehicle_id=1,
    selected_vehicle="Mitsubishi EVAL",
    selected_location="Szeged",
    selected_preferences=[],
)


@dataclass(frozen=True)
class EvalCase:
    user_input: str
    reference: str


def _to_context_text(context_entry: dict) -> str:
    """Normalize retrieved parking info into stable text for ragas context metrics."""
    return json.dumps(context_entry, ensure_ascii=True, sort_keys=True)


def _strip_markdown(text: str) -> str:
    """Remove markdown formatting so RAGAS can extract plain factual claims."""
    text = re.sub(r"#{1,6}\s*", "", text)  # headings
    text = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", text)  # bold / italic
    text = re.sub(r"`{1,3}[^`]*`{1,3}", "", text)  # inline code / code blocks
    text = re.sub(r"^[-*+]\s+", "", text, flags=re.MULTILINE)  # bullet points
    text = re.sub(r"\n{2,}", " ", text)  # collapse blank lines
    return text.strip()


def run_evaluation(cases: list[EvalCase]):
    """Run the RAG evaluation and show the summary."""

    ragas_eval_dataset = []
    eval_dataset = []
    for case in cases:
        agent = APSRAgent()
        start_time = time.time()
        response = agent.invoke(prompt=case.user_input, history=[], session_context=DEFAULT_SESSION_CONTEXT)
        end_time = time.time()

        config = {"configurable": {"thread_id": DEFAULT_SESSION_CONTEXT.thread_id}}
        state_snapshot = agent.agent.get_state(config=config)
        retrieved_info = state_snapshot.values.get("retrieved_parking_info")

        ragas_eval_dataset.append(
            {
                "user_input": case.user_input,
                "retrieved_contexts": [_to_context_text(info) for info in (retrieved_info or [])],
                "response": _strip_markdown(response),
                "reference": case.reference,
            }
        )

    eval_df = evaluate_with_ragas(ragas_eval_dataset)
    eval_df.to_excel("ragas_evaluation_results.xlsx", index=True)


RAGAS_JUDGE_MODEL = "gpt-4o"


def evaluate_with_ragas(dataset: list[dict]) -> dict:
    """Evaluate the RAG performance using RAGas."""
    ragas_dataset = EvaluationDataset.from_list(dataset)
    llm = LangchainLLMWrapper(ChatOpenAI(model=RAGAS_JUDGE_MODEL, temperature=0))
    embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings())
    results = evaluate(
        dataset=ragas_dataset,
        metrics=[context_recall, faithfulness, answer_relevancy, answer_correctness],
        llm=llm,
        embeddings=embeddings,
        raise_exceptions=False,  # Ensure that evaluation continues even if some cases fail
        show_progress=True,  # Show progress for better visibility during evaluation
    )
    return results.to_pandas()


# ========== Evaluation Dataset ==========
DEFAULT_EVAL_CASES: list[EvalCase] = [
    EvalCase(
        user_input="What are the parking options available at Budapest airport?",
        reference=(
            "At Budapest airport, Liszt Airport Park & Go (HU-BUD-001) offers open-air parking, "
            "24/7 security, shuttle service, EV charging, and accessibility support."
        ),
    ),
    EvalCase(
        user_input="Which parking lot near Keleti station has valet parking?",
        reference=(
            "Keleti Station Multi-storey Parking (HU-BP-KELETI-002) offers valet parking "
            "and is located at Baross ter 11, Budapest."
        ),
    ),
    EvalCase(
        user_input="Which parking options in Budapest include EV charging?",
        reference=(
            "In Budapest, EV charging is available at Liszt Airport Park & Go (HU-BUD-001), "
            "Keleti Station Multi-storey Parking (HU-BP-KELETI-002), and Nyugati Station "
            "Underground Parking (HU-BP-NYUGATI-006)."
        ),
    ),
    EvalCase(
        user_input="Which location has the lowest listed general parking price?",
        reference=("Miskolc Bus Terminal Parking (HU-MISKOLC-007) has the lowest listed general " "price at 1200."),
    ),
    EvalCase(
        user_input="Which parking lots have 24/7 operating hours?",
        reference=(
            "Liszt Airport Park & Go (HU-BUD-001) and Debrecen Airport Express Parking " "(HU-DEB-003) operate 24/7."
        ),
    ),
]

if __name__ == "__main__":
    default_cases = DEFAULT_EVAL_CASES
    custom_cases = None

    run_evaluation(cases=custom_cases or default_cases)
