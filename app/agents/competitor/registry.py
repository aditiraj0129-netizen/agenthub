"""
Competitor site registry — now backed by a real SQLite table instead of
a JSON file. Same function signatures as before, so nothing calling
these functions needs to change.
"""
from app.db.database import get_db


def add_site(site_id: str, url: str) -> dict:
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO competitor_sites (site_id, url, last_report) VALUES (?, ?, ?)",
            (site_id, url, None),
        )
    return {"url": url, "last_report": None}


def list_sites() -> dict:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM competitor_sites").fetchall()
        return {row["site_id"]: {"url": row["url"], "last_report": row["last_report"]} for row in rows}


def update_last_report(site_id: str, report: str):
    with get_db() as conn:
        conn.execute(
            "UPDATE competitor_sites SET last_report = ? WHERE site_id = ?",
            (report, site_id),
        )


def find_site_by_mention(user_input: str) -> str | None:
    text = user_input.lower()
    sites = list_sites()
    for site_id, info in sites.items():
        domain = info["url"].split("//")[-1].split("/")[0]
        if site_id.lower() in text or domain.lower() in text:
            return site_id
    return None


def delete_site(site_id: str) -> bool:
    with get_db() as conn:
        cur = conn.execute("DELETE FROM competitor_sites WHERE site_id = ?", (site_id,))
        return cur.rowcount > 0
