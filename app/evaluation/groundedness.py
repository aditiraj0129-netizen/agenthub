"""
Scores whether the Competitor Watcher's summary is actually grounded in
the real snapshot text, or whether the LLM hallucinated details that
aren't in the source. This is the metric that matters most for a RAG
agent specifically — speed doesn't matter if the answer is made up.
"""
from ragas import SingleTurnSample
from ragas.metrics import Faithfulness
from ragas.llms import LangchainLLMWrapper
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv()

_eval_llm = LangchainLLMWrapper(ChatGroq(
    model="openai/gpt-oss-20b",
    api_key=os.getenv("GROQ_API_KEY"),
))
_faithfulness = Faithfulness(llm=_eval_llm)


async def score_groundedness(question: str, context: list[str], answer: str) -> float:
    sample = SingleTurnSample(
        user_input=question,
        response=answer,
        retrieved_contexts=context,
    )
    score = await _faithfulness.single_turn_ascore(sample)
    return round(score, 2)
