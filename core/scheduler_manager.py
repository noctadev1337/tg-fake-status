from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz

class SchedulerManager:
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone=pytz.utc)

    def load(self, sessions_utc, bot):
        self.scheduler.remove_all_jobs()
        for s in sessions_utc:
            sh, sm = s["start"]
            eh, em = s["end"]
            handler = bot.make_session_handler(eh, em)
            self.scheduler.add_job(handler, "cron", hour=sh, minute=sm)
            print(f"  сессия  UTC {sh:02d}:{sm:02d} -> {eh:02d}:{em:02d}")

    def start(self):
        self.scheduler.start()

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
