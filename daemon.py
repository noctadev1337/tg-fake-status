import asyncio
import sys
import os
sys.path.insert(0, '/root/tg-activity')

from core.config_manager import ConfigManager
from core.activity import ActivityBot
from core.scheduler_manager import SchedulerManager

def to_utc(h, m, offset): return (h - offset) % 24, m

async def main():
    config = ConfigManager()
    sessions = config.current_schedule
    if not sessions:
        print("расписание пусто — выход")
        return

    bot = ActivityBot(config)
    await bot.connect()

    tz = config.timezone_offset
    sessions_utc = [
        {
            "start": to_utc(s["start"]["hour"], s["start"]["minute"], tz),
            "end":   to_utc(s["end"]["hour"],   s["end"]["minute"],   tz)
        }
        for s in sessions
    ]

    sched = SchedulerManager()
    sched.load(sessions_utc, bot)
    sched.start()
    print("планировщик запущен")

    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        sched.stop()
        await bot.go_offline()
        await bot.disconnect()

asyncio.run(main())
