"""
Scores whether the Competitor Watcher's summary is actually grounded in
the real snapshot text, or whether the LLM hallucinated details that
aren't in the source. This is the metric that matters most for a RAG
agent specifically — speed doesn't matter if the answer is made up.
"""
# ragas/langchain are NOT imported at module level — same reasoning as the
# transformers fix above. They're imported inside the function, only when a
# groundedness score is actually requested (which itself only happens when
# a real, specific change is detected — see agent.py's skip logic).
import os
from dotenv import load_dotenv

load_dotenv()

_faithfulness = None


def _get_faithfulness():
    global _faithfulness
    if _faithfulness is None:
        from ragas.metrics import Faithfulness
        from ragas.llms import LangchainLLMWrapper
        from langchain_groq import ChatGroq

        eval_llm = LangchainLLMWrapper(ChatGroq(
            model="openai/gpt-oss-20b",
            api_key=os.getenv("GROQ_API_KEY"),
        ))
        _faithfulness = Faithfulness(llm=eval_llm)
    return _faithfulness


async def score_groundedness(question: str, context: list[str], answer: str) -> float:
    from ragas import SingleTurnSample

    sample = SingleTurnSample(
        user_input=question,
        response=answer,
        retrieved_contexts=context,
    )
    score = await _get_faithfulness().single_turn_ascore(sample)
    return round(score, 2)
