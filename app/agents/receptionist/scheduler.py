"""
Runs every minute in the background, checking for any employee whose
task should be finished by now, and freeing them up automatically —
this is the "after that time period, track and assign them free again"
behavior you asked for.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from app.agents.receptionist.agent import release_expired_employees

_scheduler = BackgroundScheduler()


def check_expired_tasks():
    released = release_expired_employees()
    if released:
        print(f"[receptionist scheduler] Freed {released} employee(s) whose tasks completed.")


def start_receptionist_scheduler():
    _scheduler.add_job(check_expired_tasks, "interval", minutes=1, id="release_employees")
    _scheduler.start()
