# Focus — контроль фокуса

Локально следит чем ты занимаешься и напоминает о лимитах (игры / ютуб).

## Что умеет
- **Детект по окну** (бесплатно): читает заголовок активного окна + exe, определяет `game / youtube / youtube_edu / work` по ключевым словам. Работает 100% локально, 0% нагрузки.
- **Vision** (умно): каждые ~45 сек делает скриншот → кидает в **локальную** vision-LLM через Ollama (`moondream` ~1.7GB, идеально для RTX 3050 4GB). Она понимает что реально на экране, даже если заголовок окна не информативен.
- **Ругань**: голосом `pyttsx3` + уведомление Windows + смешной роаст от второй LLM (`llama3.1:8b` или `qwen2.5-coder:1.5b`).
- **Лимиты** настраиваются в `config.yaml`.

## Быстрый старт
```bat
# 1. зависимости (уже стоят у тебя)
py -m pip install -r requirements.txt

# 2. vision модель (1.7GB, один раз)
ollama pull moondream

# 3. запуск
py focus_nanny.py
# или двойной клик start.bat
```

Остановить: `Ctrl+C`

## Настройка `config.yaml`
- `check_interval: 3` — как часто проверять окно
- `vision_interval: 45` — как часто скринить (не ставь <15, будет жрать VRAM)
- `enable_vision: true/false` — можно выключить тяжелую часть и оставить только детект по окну (супер легко, подойдет даже с 2GB VRAM)
- `vision_model: "moondream"` — самая легкая. Альтернативы: `llava:7b`, `minicpm-v:8b`, `llava-phi3`
- `chat_model: "llama3.1:8b"` — кто тебя ругает. Если тормозит → поставь `qwen2.5-coder:1.5b` (в 5x быстрее)
- `limits.game_minutes: 30` и т.д.
- `games:` — список exe игр, `work_keywords:` и т.д. — добавь свои
- `enable_voice: true/false`

## Как это работает с твоими "двумя оламами"
У тебя уже стоят `qwen2.5-coder:1.5b` и `llama3.1:8b` — они **не умеют в картинки**, только текст. 
- Для скриншотов нужна **vision-модель** (`moondream` / `llava`). Это тоже Ollama, просто другой вес.
- Схема: `скриншот → moondream (что на экране?) → llama3.1/qwen (сгенерируй ругань)`

Ты можешь оставить `moondream` для зрения и `qwen2.5-coder:1.5b` для ругани — будет максимально быстро и влезет в 4GB VRAM (по очереди, не одновременно).

## Производительность
- Без vision: ~10 MB RAM, 0% GPU
- С vision (moondream): ~1.8GB VRAM на 5 сек каждые 45 сек, в остальное время 0
- Если лагает в играх — увеличь `vision_interval: 90` или `enable_vision: false`

## Расширения идеи
- Добавить блокировку сайтов/процессов (`taskkill` + `hosts`)
- Логи в файл + график продуктивности за день
- Telegram-бот который пишет маме 😈

## Тест без запуска
```bat
py -c "import win32gui; print(win32gui.GetWindowText(win32gui.GetForegroundWindow()))"
py -c "import ollama; print(ollama.chat(model='llama3.1:8b', messages=[{'role':'user','content':'скажи аяяяй'}])['message']['content'])"
```
