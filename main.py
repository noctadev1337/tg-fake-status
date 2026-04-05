import asyncio
import sys
import os
from core.config_manager import ConfigManager
from core.activity import ActivityBot
from core.scheduler_manager import SchedulerManager

BANNER = """\033[36m
  ████████╗ ██████╗     ███████╗ █████╗ ██╗  ██╗███████╗    ███████╗████████╗ █████╗ ████████╗██╗   ██╗███████╗
  ╚══██╔══╝██╔════╝     ██╔════╝██╔══██╗██║ ██╔╝██╔════╝    ██╔════╝╚══██╔══╝██╔══██╗╚══██╔══╝██║   ██║██╔════╝
     ██║   ██║  ███╗    █████╗  ███████║█████╔╝ █████╗      ███████╗   ██║   ███████║   ██║   ██║   ██║███████╗
     ██║   ██║   ██║    ██╔══╝  ██╔══██║██╔═██╗ ██╔══╝      ╚════██║   ██║   ██╔══██║   ██║   ██║   ██║╚════██║
     ██║   ╚██████╔╝    ██║     ██║  ██║██║  ██╗███████╗    ███████║   ██║   ██║  ██║   ██║   ╚██████╔╝███████║
     ╚═╝    ╚═════╝     ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝    ╚══════╝   ╚═╝   ╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚══════╝
\033[0m  Telegram Fake Status
"""

SEP = "  " + "─" * 70

def clear(): os.system("clear")
def banner(): print(BANNER)
def line(): print(SEP)

def ask(prompt):
    try:
        sys.stdout.write(prompt)
        sys.stdout.flush()
        raw = sys.stdin.buffer.readline()
        return raw.decode("utf-8", errors="replace").strip()
    except (KeyboardInterrupt, EOFError):
        print(); return ""

def pause(): ask("  [Enter] продолжить...")
def to_utc(h, m, offset): return (h - offset) % 24, m

def show_schedule(config):
    line()
    sessions = config.current_schedule
    tz = config.timezone_offset
    sign = "+" if tz >= 0 else ""
    if not sessions:
        print("  Текущее расписание: пусто")
    else:
        print(f"  Текущее расписание  (UTC{sign}{tz}):\n")
        for i, s in enumerate(sessions, 1):
            sh, sm = s["start"]["hour"], s["start"]["minute"]
            eh, em = s["end"]["hour"],   s["end"]["minute"]
            print(f"    {i}.  {sh:02d}:{sm:02d} -> {eh:02d}:{em:02d}")
    line()

def edit_schedule(config):
    while True:
        clear(); banner(); show_schedule(config)
        print("""
  [a] Добавить сессию
  [d] Удалить сессию
  [c] Очистить расписание
  [0] Назад
""")
        choice = ask("  > ")
        if choice == "0": break
        elif choice == "a":
            try:
                sh, sm = map(int, ask("  Начало (HH:MM): ").split(":"))
                assert 0<=sh<=23 and 0<=sm<=59
                eh, em = map(int, ask("  Конец  (HH:MM): ").split(":"))
                assert 0<=eh<=23 and 0<=em<=59
                sessions = list(config.current_schedule)
                sessions.append({
                    "start": {"hour": sh, "minute": sm},
                    "end":   {"hour": eh, "minute": em}
                })
                config.set_current_schedule(sessions)
                print(f"  Добавлено {sh:02d}:{sm:02d} -> {eh:02d}:{em:02d}")
            except:
                print("  Неверный формат. Используй HH:MM")
            pause()
        elif choice == "d":
            sessions = config.current_schedule
            if not sessions: print("  Расписание пусто."); pause(); continue
            show_schedule(config)
            try:
                idx = int(ask("  Номер для удаления: ")) - 1
                assert 0 <= idx < len(sessions)
                s = sessions[idx]
                config.set_current_schedule([x for i,x in enumerate(sessions) if i != idx])
                print(f"  Удалено {s['start']['hour']:02d}:{s['start']['minute']:02d} -> {s['end']['hour']:02d}:{s['end']['minute']:02d}")
            except: print("  Неверный номер.")
            pause()
        elif choice == "c":
            config.clear_current(); print("  Очищено."); pause()

def templates_menu(config):
    while True:
        clear(); banner(); line()
        print("  ШАБЛОНЫ\n")
        names = config.list_templates()
        if not names:
            print("  (нет шаблонов)")
        else:
            for i, name in enumerate(names, 1):
                t = config.load_template(name)
                print(f"  {i}.  {name}  ({len(t)} сессий)")
        line()
        print("""
  [s] Сохранить текущее расписание как шаблон
  [a] Применить шаблон
  [d] Удалить шаблон
  [0] Назад
""")
        choice = ask("  > ")
        if choice == "0": break
        elif choice == "s":
            if not config.current_schedule: print("  Расписание пусто."); pause(); continue
            name = ask("  Название: ")
            if name: config.save_template(name); print(f"  Сохранено '{name}'.")
            pause()
        elif choice == "a":
            if not names: print("  Нет шаблонов."); pause(); continue
            try:
                idx = int(ask("  Номер (0 — отмена): ")) - 1
                if idx == -1: continue
                assert 0 <= idx < len(names)
                config.apply_template(names[idx])
                print(f"  Применён '{names[idx]}'.")
            except: print("  Неверный номер.")
            pause()
        elif choice == "d":
            if not names: print("  Нет шаблонов."); pause(); continue
            try:
                idx = int(ask("  Номер (0 — отмена): ")) - 1
                if idx == -1: continue
                assert 0 <= idx < len(names)
                config.delete_template(names[idx]); print(f"  Удалён '{names[idx]}'.")
            except: print("  Неверный номер.")
            pause()

def settings_menu(config):
    while True:
        clear(); banner(); line()
        tz = config.timezone_offset
        sign = "+" if tz >= 0 else ""
        print(f"  НАСТРОЙКИ\n")
        print(f"  Часовой пояс:  UTC{sign}{tz}")
        line()
        print("""
  [t] Изменить часовой пояс
  [0] Назад
""")
        choice = ask("  > ")
        if choice == "0": break
        elif choice == "t":
            raw = ask("  Смещение от UTC (например: 3, -5, 0): ")
            try:
                config.set_timezone(int(raw))
                tz = config.timezone_offset
                sign = "+" if tz >= 0 else ""
                print(f"  Установлен UTC{sign}{tz}")
            except: print("  Неверный формат. Введи целое число.")
            pause()

async def run_scheduler(config):
    sessions = config.current_schedule
    if not sessions:
        print("  Расписание пусто.")
        pause(); return

    bot = ActivityBot(config)
    await bot.connect()

    tz = config.timezone_offset
    sessions_utc = []
    for s in sessions:
        sh, sm = to_utc(s["start"]["hour"], s["start"]["minute"], tz)
        eh, em = to_utc(s["end"]["hour"],   s["end"]["minute"],   tz)
        sessions_utc.append({"start": (sh, sm), "end": (eh, em)})

    sched = SchedulerManager()
    print(); line()
    print("  Запуск планировщика:")
    sched.load(sessions_utc, bot)
    sched.start()
    print("  Работает. Ctrl+C для остановки.")
    line()

    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        sched.stop()
        await bot.go_offline()
        await bot.disconnect()
        if not config.is_saved_as_template():
            config.clear_current()
            print("  Расписание не сохранено как шаблон — очищено.")

def main():
    config = ConfigManager()
    while True:
        clear(); banner(); show_schedule(config)
        tz = config.timezone_offset
        sign = "+" if tz >= 0 else ""
        print(f"""
  [1] Запустить планировщик
  [2] Редактировать расписание
  [3] Шаблоны
  [4] Настройки  (UTC{sign}{tz})
  [0] Выход
""")
        choice = ask("  > ")
        if choice == "0": sys.exit(0)
        elif choice == "1": asyncio.run(run_scheduler(config))
        elif choice == "2": edit_schedule(config)
        elif choice == "3": templates_menu(config)
        elif choice == "4": settings_menu(config)

if __name__ == "__main__":
    main()
