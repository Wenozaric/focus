# Focus — SwiftUI

Дорогой нативный UI для macOS (SwiftUI, HIG) + логика на Python.

## Архитектура
```
focus-nanny/            # Python логика (Windows/Linux трекинг + vision)
  bridge.py             # JSONL over stdout/stdin: tick + vision + limits
  config.yaml, session.json
focus-nanny-swift/      # SwiftUI фронтенд (macOS 14+)
  Package.swift         # SPM
  Sources/FocusNanny/
    FocusNannyApp.swift
    DesignTokens.swift  # палитра Вин11 Fluent / Apple HIG, radius 12
    Models/Category.swift, AppState.swift
    Services/PythonBridge.swift  # запускает bridge.py, читает JSONL
    Views/ContentView.swift + Cards/* + Components/*
```

## UI (все пункты ТЗ)
- **Bento Grid**: карточки `card()` — radius 12, border 1px `#E2E8F0` 7%, двойная тень
- **Слайдеры**: `FluentSlider` (трек 4px + thumb 16px белая с бордером) + `StepperControl` с `−/+` — `ttk.Scale` нет
- **Бары 6px**: `Capsule height 6` без заглушек, цвет = цвету иконки категории
- **Типографика**: `.rounded/.monospaced` системный (SF Pro на macOS, Segoe UI Variable на Windows-аналоге), hero 34pt bold, muted `#334155` контрастный
- **Интерактив**: акцентная кнопка `Capsule fill #0EA5E9`, вердикт в `VerdictBlock` с `padding 12`

## Запуск
macOS:
```sh
cd focus-nanny-swift
swift run
# или собрать
swift build -c release && .build/release/FocusNanny
```
Требует `python3` c `bridge.py` рядом (`../focus-nanny/bridge.py`). Без Python — мок-данные (демо).

Windows: старый `app_gui.py` (FluentSlider на tkinter) остаётся рабочим — логика та же.

## Логика (Python)
`bridge.py` раз в `check_interval` шлёт `{"type":"tick","totals":{...},"currentCat":...,"visionText":...}`. Swift читает `readabilityHandler` и обновляет `@Published`.
Обратно Swift шлёт `{"type":"set_limits",...}` и `{"type":"vision_now"}`.
