import subprocess
import sys
import os
from core.config_manager import ConfigManager

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
SERVICE_NAME = "tg-fake-status"

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

def launch_service(config):
    if not config.current_schedule:
        print("  Расписание пусто.")
        pause()
        return

    print(f"\n  Перезапускаем сервис {SERVICE_NAME}...")
    result = subprocess.run(
        ["systemctl", "restart", SERVICE_NAME],
        capture_output=True, text=True
    )

    if result.returncode == 0:
        print(f"  Сервис запущен.\n")
        print(f"  Логи в реальном времени:\n")
        print(f"    journalctl -u {SERVICE_NAME} -f\n")
    else:
        print(f"  Ошибка запуска сервиса:")
        print(f"  {result.stderr.strip()}")

    sys.exit(0)

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
        elif choice == "1": launch_service(config)
        elif choice == "2": edit_schedule(config)
        elif choice == "3": templates_menu(config)
        elif choice == "4": settings_menu(config)

if __name__ == "__main__":
    main()
