"""
Runs the competitor check automatically on a schedule, instead of only
when a user happens to send a chat message. This is what makes it a
real "watcher" rather than something you have to remember to ask about.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from app.agents.competitor.registry import list_sites, update_last_report
from app.agents.competitor.agent import track_site

_scheduler = BackgroundScheduler()


def check_all_sites():
    for site_id, info in list_sites().items():
        result = track_site(site_id, info["url"])
        update_last_report(site_id, result)
        print(f"[scheduler] {site_id}: {result}")


def start_scheduler(interval_minutes: int = 60):
    _scheduler.add_job(check_all_sites, "interval", minutes=interval_minutes, id="competitor_check")
    _scheduler.start()
