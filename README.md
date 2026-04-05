# TG-FAKE-STATUS

Планировщик активности Telegram-аккаунта. Автоматически выставляет статус «онлайн» в заданные временные окна. Длинные сессии разбиваются на блоки по 4 минуты с короткой паузой — Telegram не сбрасывает статус.

```
  ████████╗ ██████╗     ███████╗ █████╗ ██╗  ██╗███████╗    ███████╗████████╗ █████╗ ████████╗██╗   ██╗███████╗
  ╚══██╔══╝██╔════╝     ██╔════╝██╔══██╗██║ ██╔╝██╔════╝    ██╔════╝╚══██╔══╝██╔══██╗╚══██╔══╝██║   ██║██╔════╝
     ██║   ██║  ███╗    █████╗  ███████║█████╔╝ █████╗      ███████╗   ██║   ███████║   ██║   ██║   ██║███████╗
     ██║   ██║   ██║    ██╔══╝  ██╔══██║██╔═██╗ ██╔══╝      ╚════██║   ██║   ██╔══██║   ██║   ██║   ██║╚════██║
     ██║   ╚██████╔╝    ██║     ██║  ██║██║  ██╗███████╗    ███████║   ██║   ██║  ██║   ██║   ╚██████╔╝███████║
     ╚═╝    ╚═════╝     ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝    ╚══════╝   ╚═╝   ╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚══════╝
```

---

## Требования

- Python 3.10+
- Linux (Ubuntu 22.04+)
- Telegram-аккаунт (не бот)
- Сервер за пределами РФ (если Telegram заблокирован)

---

## Установка

### 1. Клонируем репозиторий

```bash
git clone https://github.com/yourname/tg-fake-status
cd tg-fake-status
```

### 2. Создаём виртуальное окружение

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Устанавливаем зависимости

```bash
pip install -r requirements.txt
```

### 4. Создаём `.env`

```bash
cp .env.example .env
```

Открываем `.env` и вписываем свои данные:

```env
API_ID=2040
API_HASH=b18441a1ff607e10a989891a5462e627
SESSION_PATH=/root/tg-fake-status/session
```

> `API_ID` и `API_HASH` можно получить на [my.telegram.org](https://my.telegram.org) → API development tools.

---

## Авторизация

Выполняется один раз. Сессия сохраняется в файл и больше не запрашивается.

```bash
source venv/bin/activate
python3 auth_qr.py
```

Откроется QR-код в терминале. В Telegram на телефоне:

**Настройки → Устройства → Подключить устройство** → сканируй QR.

Если включена двухфакторная аутентификация — скрипт запросит пароль.

---

## Настройка расписания

Запускаем интерактивное меню:

```bash
source venv/bin/activate
PYTHONIOENCODING=utf-8 python3 main.py
```

**Шаг 1 — устанавливаем часовой пояс:**

```
[4] Настройки → [t] Изменить часовой пояс
```

Вводим смещение от UTC. Примеры: `3` для Москвы, `2` для Берлина, `-5` для Нью-Йорка.

**Шаг 2 — создаём расписание:**

```
[2] Редактировать расписание → [a] Добавить сессию
```

Вводим время начала и конца в локальном времени (по заданному поясу):

```
Начало (HH:MM): 22:00
Конец  (HH:MM): 23:30
```

Добавляем столько сессий, сколько нужно.

**Шаг 3 — сохраняем как шаблон:**

```
[3] Шаблоны → [s] Сохранить текущее расписание как шаблон
```

Вводим название, например `night`. Если расписание не сохранено как шаблон — после остановки планировщика оно автоматически очищается.

**Шаг 4 — выходим из меню:**

```
[0] Выход
```

---

## Запуск как системный сервис

### 1. Правим путь в сервис-файле

Открываем `tg-fake-status.service` и убеждаемся что пути верны:

```ini
[Unit]
Description=TG-Fake-Status Scheduler
After=network.target

[Service]
ExecStart=/root/tg-fake-status/venv/bin/python3 /root/tg-fake-status/daemon.py
WorkingDirectory=/root/tg-fake-status
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1
Environment=PYTHONIOENCODING=utf-8

[Install]
WantedBy=multi-user.target
```

### 2. Устанавливаем сервис

```bash
cp tg-fake-status.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable tg-fake-status
```

### 3. Запускаем

```bash
systemctl start tg-fake-status
```

### 4. Смотрим логи

```bash
# логи в реальном времени
journalctl -u tg-fake-status -f

# последние 50 строк
journalctl -u tg-fake-status -n 50

# логи за сегодня
journalctl -u tg-fake-status --since today
```

### 5. Управление сервисом

```bash
# статус
systemctl status tg-fake-status

# остановить
systemctl stop tg-fake-status

# перезапустить (нужно после изменения расписания)
systemctl restart tg-fake-status

# убрать из автозапуска
systemctl disable tg-fake-status
```

---

## Изменение расписания на работающем сервисе

```bash
# редактируем расписание
source venv/bin/activate
PYTHONIOENCODING=utf-8 python3 main.py

# перезапускаем сервис чтобы подхватил новое расписание
systemctl restart tg-fake-status
```

---

## Как работает логика сессий

Telegram сбрасывает статус «онлайн» через ~5 минут без активности клиента. Чтобы обойти это ограничение, каждая сессия разбивается на блоки:

```
22:00  входим онлайн     (блок 240с)
22:04  уходим оффлайн    (пауза 20с)
22:04  входим онлайн     (блок 240с)
22:08  уходим оффлайн    (пауза 20с)
...
23:30  сессия завершена
```

Время начала и конца вводится в локальном часовом поясе — конвертация в UTC происходит автоматически.

---

## Структура проекта

```
tg-fake-status/
├── main.py                   # интерактивное CLI-меню
├── daemon.py                 # фоновый запуск для сервиса
├── auth_qr.py                # первичная авторизация через QR
├── config.json               # текущее расписание и настройки
├── templates/                # шаблоны расписаний (отдельные json)
│   └── night.json
├── core/
│   ├── __init__.py
│   ├── activity.py           # логика онлайн/оффлайн и блоков
│   ├── config_manager.py     # работа с config.json и шаблонами
│   └── scheduler_manager.py  # APScheduler (UTC)
├── venv/                     # виртуальное окружение (не в git)
├── .env                      # API ключи (не в git)
├── .env.example              # пример конфига
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
└── tg-fake-status.service    # systemd unit
```

---

## Лицензия

MIT — делай с кодом что хочешь.
