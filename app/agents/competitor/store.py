"""
Stores raw page-text snapshots directly in SQLite. Earlier this went
through ChromaDB with a full sentence-transformers embedding pass on
every save — but the comparison logic only ever grouped chunks by
timestamp and diffed the raw text, so those embeddings were computed
and never used. Removing that step is what fixed the slow response
time: this table read/write is near-instant, and the actual latency
you'll still see is just the network crawl + the LLM summarization
call, both of which are unavoidable.
"""
from datetime import datetime
from app.db.database import get_db


def save_snapshot(site_id: str, chunks: list[str], timestamp: str):
    with get_db() as conn:
        conn.executemany(
            "INSERT INTO site_snapshots (site_id, chunk_text, snapshot_time) VALUES (?, ?, ?)",
            [(site_id, chunk, timestamp) for chunk in chunks],
        )


def get_latest_two_snapshots(site_id: str) -> tuple[list[str], list[str]]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT DISTINCT snapshot_time FROM site_snapshots WHERE site_id = ? ORDER BY snapshot_time DESC LIMIT 2",
            (site_id,),
        ).fetchall()

        if len(rows) < 2:
            if len(rows) == 1:
                current = conn.execute(
                    "SELECT chunk_text FROM site_snapshots WHERE site_id = ? AND snapshot_time = ?",
                    (site_id, rows[0]["snapshot_time"]),
                ).fetchall()
                return [], [r["chunk_text"] for r in current]
            return [], []

        latest_time, previous_time = rows[0]["snapshot_time"], rows[1]["snapshot_time"]

        current = conn.execute(
            "SELECT chunk_text FROM site_snapshots WHERE site_id = ? AND snapshot_time = ?",
            (site_id, latest_time),
        ).fetchall()
        previous = conn.execute(
            "SELECT chunk_text FROM site_snapshots WHERE site_id = ? AND snapshot_time = ?",
            (site_id, previous_time),
        ).fetchall()

        return [r["chunk_text"] for r in previous], [r["chunk_text"] for r in current]
