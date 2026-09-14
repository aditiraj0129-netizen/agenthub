"""
The real Competitor Watcher agent.
Flow: crawl the page -> chunk it -> save snapshot -> compare to the
previous snapshot -> ask an LLM to summarize what meaningfully changed.

Model choice: Groq's llama-3.1-8b-instant — fast and free-tier friendly.
"""
import os
from datetime import datetime
import litellm
from dotenv import load_dotenv
from app.agents.competitor.crawler import fetch_page_text, chunk_text
from app.guardrails.content_sanitizer import sanitize_external_content
from app.agents.competitor.store import save_snapshot, get_latest_two_snapshots
from app.agents.competitor.registry import list_sites, find_site_by_mention, update_last_report
import asyncio
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from app.evaluation.groundedness import score_groundedness


def _run_async_safely(coro):
    """
    We're inside FastAPI's already-running event loop, so we can't call
    asyncio.run() directly (it errors if a loop is already running).
    Running it in a separate thread gives it a clean event loop of its own.
    """
    with concurrent.futures.ThreadPoolExecutor() as pool:
        future = pool.submit(asyncio.run, coro)
        return future.result()

load_dotenv()
# litellm auto-detects GROQ_API_KEY from the environment for "groq/..." models —
# no manual assignment needed, as long as .env actually loaded it.


def track_site(site_id: str, url: str) -> str:
    text = fetch_page_text(url)
    text = sanitize_external_content(text, source_label=f"crawled page ({url})")
    chunks = chunk_text(text)
    timestamp = datetime.utcnow().isoformat()

    save_snapshot(site_id, chunks, timestamp)
    previous, current = get_latest_two_snapshots(site_id)

    if not previous:
        return f"First snapshot of {site_id} saved ({len(current)} chunks). Nothing to compare yet."

    return summarize_changes(site_id, previous, current)


def summarize_changes(site_id: str, previous: list[str], current: list[str]) -> str:
    prev_text = "\n".join(previous)[:3000]
    curr_text = "\n".join(current)[:3000]

    prompt = f"""You are a competitor-monitoring analyst. Compare these two
snapshots of the same webpage and report ONLY the meaningful changes
(pricing, new features, messaging shifts). Ignore trivial wording changes.
If nothing meaningful changed, say so clearly.

PREVIOUS SNAPSHOT:
{prev_text}

CURRENT SNAPSHOT:
{curr_text}

Meaningful changes:"""

    try:
        response = litellm.completion(
            model=os.getenv("COMPETITOR_MODEL", "groq/openai/gpt-oss-20b"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,             # more headroom so reasoning doesn't eat the whole budget
            reasoning_effort="low",     # this task doesn't need deep reasoning, just comparison
        )
        content = response["choices"][0]["message"]["content"]
        final_answer = content.strip() if content and content.strip() else "No meaningful changes detected (empty model response)."

        no_change_phrases = ["no meaningful change", "no meaningful changes", "nothing meaningful changed"]
        is_no_change_answer = any(phrase in final_answer.lower() for phrase in no_change_phrases)

        try:
            if is_no_change_answer:
                raise ValueError("Skipping groundedness scoring: no factual claims to verify in a 'no change' answer.")
            score = _run_async_safely(score_groundedness(
                question="What meaningfully changed between these two snapshots?",
                context=[prev_text, curr_text],
                answer=final_answer,
            ))
            final_answer += f"\n\n[groundedness score: {score}/1.0]"
        except Exception:
            pass  # scoring is a nice-to-have; never let it break the main response

        return final_answer
    except Exception as e:
        # TEMPORARY: surfaces the real error instead of hiding it, so we can debug.
        # We'll remove this raw exposure once things are stable (Step 6 replaces
        # it with proper structured error logging).
        return f"[DEBUG ERROR] {type(e).__name__}: {str(e)}"


def _check_one_site(site_id: str, url: str) -> str:
    result = track_site(site_id, url)
    update_last_report(site_id, result)
    return f"[{site_id}] {result}"


def competitor_agent(user_input: str) -> str:
    """
    If the user mentions a registered site by name/domain, track just that one.
    Otherwise, check ALL registered sites IN PARALLEL (each site's crawl + LLM
    call is independent, so there's no reason to wait for one before starting
    the next — this is what actually cuts multi-site latency down).
    """
    sites = list_sites()
    if not sites:
        return ("No sites registered yet. Register one first via "
                "POST /competitor/sites with a site_id and url.")

    matched = find_site_by_mention(user_input)
    targets = {matched: sites[matched]} if matched else sites

    if len(targets) == 1:
        site_id, info = next(iter(targets.items()))
        return _check_one_site(site_id, info["url"])

    with ThreadPoolExecutor(max_workers=len(targets)) as pool:
        futures = [pool.submit(_check_one_site, site_id, info["url"]) for site_id, info in targets.items()]
        reports = [f.result() for f in futures]

    return "\n".join(reports)
