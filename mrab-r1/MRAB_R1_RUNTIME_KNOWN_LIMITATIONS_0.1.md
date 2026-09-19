# Known limitations — Runtime 0.1

## Что означает техническая готовность

Пакет реализует MRAB-R1 и проверен deterministic/offline средствами.
Он не утверждает calibration feasibility, соблюдение JSON конкретной моделью, превосходство B3,
причинную роль self-profile или истинность operational capability.

До использования дистрибутива проверьте внешний MRAB_R1_RUNTIME_VERIFICATION_0.1.json:
FRESH_EXTRACT_VERIFIED и совпадающий archive SHA-256. Встроенный отчёт предшествует этому шагу.

## Эксплуатационные границы

- Реальный adapter и модель не выбраны. По исходному заданию §11 real adapter не обязателен.
  Будущий adapter обязан обеспечить deadline/acceptance semantics, фактическую revision и usage,
  не добавлять retries/скрытую историю; identity проверяется против FROZEN config.
- BYTE_QUARTER_TEST_TOKENIZER_0.1 — только deterministic test double. Нужен tokenizer выбранной модели.
- Стандартные tools исполняются в отдельном процессе с deadline; произвольный callable разрешён только
  для offline failure injection. Его нельзя выдавать за зарегистрированный реальный tool.
- Resume только после durable CHECKPOINT. Неполный эпизод, stale writer lease и повреждённый хвост
  требуют явного recovery/replay; ничего не удаляется автоматически.
- Денежная стоимость остаётся null без зарегистрированного полного price source.
  Неизвестные usage counters не подменяются нулём; test counters не являются измерением модели.
- Для точной исходной latency evaluation нужен sidecar с записанными tool durations.
  Новое wall-clock время при replay не обязано совпадать и не заменяет старое измерение.
- Подтверждён source-tree запуск CPython3.12 / Windows x64. Offline wheelhouse содержит native wheel
  именно этой платформы. Другие ОС/версии Python и wheel-install самого runtime не сертифицированы.
- Node — отдельная JCS-зависимость; его путь задаётся локально, binary hash входит в component identity.
- Windows без long-path support требует короткой папки распаковки: полный путь файла <260 символов.
  Первая приёмочная распаковка достигла 260 на длинном immutable source name и остановилась.
  Имя временной папки сокращено; имена исходных документов и runtime semantics не менялись.

## Методологические границы

- Beta accumulation — локальная evidence heuristic по exact operational key, не известное живое p.
- Множество key-specific latency/association результатов сохраняется как by_key, без придуманного scalar.
- Conditional reach может быть недостаточным в ограниченном окне. Отсутствие CI не стирает fixed HARM.
- Зафиксированные engineering defaults перечислены в IMPLEMENTATION_DECISIONS.
- 109 tests / 24 invariants / 51 fixture ID означают регрессионное покрытие,
  а не доказательство правильности для всех мыслимых входов или worst-case bound любого CSP.
- Два длинных end-to-end traces и контроллерные 32-step traces имеют разные уровни проверок.
  Ни один не является модельным pilot или источником эмпирического вывода.

E07 и ограничение request_bytes закрыты явными авторскими решениями; это не текущие блокеры.
Runtime verification network attempts = 0. При разработке отдельно прочитан официальный RFC JCS.
