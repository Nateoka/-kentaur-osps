# MRAB-R1 Runtime 0.1.1

Патч границ provenance, orchestration калибровки и научной оценки. Научные правила
замороженного Engineering Design 0.2.1 не меняются. Актуальная приёмка — внешний
`MRAB_R1_RUNTIME_VERIFICATION_0.1.1.json`, привязанный к SHA-256 нового ZIP.
Документы и traces с суффиксом 0.1 ниже являются сохранёнными историческими результатами,
а не доказательством пригодности старых loose records для нового scientific mode.
Актуальные решения и ограничения: `MRAB_R1_RUNTIME_IMPLEMENTATION_DECISIONS_0.1.1.md`.
В suite 129 методов: 109 исходных и 20 новых. Итоговый PASS фиксируется только отчётом.

Техническая реализация замороженного MRAB-R1 design0.2.1.
Полный исходный набор: 109 тестов PASS, 24 invariants и 51 fixture ID с исполняемым покрытием.
Это не результат модели и не подтверждение H1.

Окончательная приёмка архива находится во внешнем MRAB_R1_RUNTIME_VERIFICATION_0.1.json:
FRESH_EXTRACT_VERIFIED + SHA-256 именно выданного ZIP. Встроенный отчёт сформирован перед
распаковкой дистрибутива; внешняя приёмка устраняет круговую зависимость само-хеширования.

## Два авторских исправления

- R1-E07-HARM-01: известный independent HARM сохраняется вместе с uncertainty_reasons.
  HARM без BENEFIT → COUNTERPRODUCTIVE; HARM + BENEFIT → MIXED_TRADEOFF.
- R1-STORAGE-REQUEST-01: снят только maxLength=20000 у request_bytes в runtime schema overlay.
  Лимит 16384 входных токенов, полная обязательная история и PREP сохранены.

Исходный ZIP и 65 извлечённых файлов неизменны. Исторический BLOCKED.zip не является этим выпуском.
В design_package/ лежит точный исходный архив; в design/ — его неизменённая распаковка.

## Что входит

F1/F2 generators и exact tools; независимые проверки; JCS/strict JSON; пять схем и именованная поправка;
seed domains, sealed manifests, общая B2/B3 commit-служба, B3 stop/probe controller,
strong B4 tracker, public-only state, PREP/ACTION/REPAIR, durable журнал и safe-boundary resume,
Fake/Replay providers, SEARCH/CONFIRM engine, 41 зарегистрированная метрика и E07 classifier.

Полные 32-эпизодные scripted traces и replay находятся в verification/:
обычный B3 — 64 заданных ответа; compound B3 — 65 ответов, включая неудачную repair,
сохранённый после failed ACTION commit и переход обоих claims в UNKNOWN.
Контроллерные и арифметические traces проверяются отдельно и не выдаются за модельный эксперимент.

## Проверка на Windows

Проверенная среда: CPython3.12.14 / Windows x64; Node.js24.19.0.
Приложен offline wheelhouse с SHA-256 каждого wheel. Python и Node — внешние runtime prerequisites.
Node нужен только harness для ECMAScript/JCS; агенту он не предоставляется как инструмент.

Из корня распакованного mrab_r1_runtime:

```text
python -m venv .venv
.venv\Scripts\python -m pip install --no-index --find-links wheelhouse --require-hashes -r requirements.offline.lock
.venv\Scripts\python -B -m mrab_r1 --help
.venv\Scripts\python -B -m mrab_r1 verify-runtime
.venv\Scripts\python -B -m mrab_r1 verify-design-contract --zip design_package/MRAB_R1_Engineering_Design_Package_0.2.1.zip
```

Если Node отсутствует в PATH, задайте MRAB_JCS_NODE полным путём к node.exe.
Часть hardening-тестов обращается к MRAB_JCS_NODE напрямую (не через PATH), поэтому
переменную следует задать даже при наличии Node в PATH:
Полный suite включает синтетические 20×200 calibration records и занимает несколько минут.
MRAB_TEST_PROGRESS=1 выводит имена выполняемых tests в stderr; это не вызовы модели.
Предусмотрен source-tree запуск; установка wheel самого runtime не заявляется как проверенный способ.
В Windows выбирайте короткий путь распаковки: неизменённые названия исходных документов длинные.
При выключенной поддержке long paths полный путь каждого файла должен быть короче 260 символов.

## Команды

verify-design-contract; freeze-config; generate-task; verify-task; build-manifest; calibration-plan; collect-run;
run-trajectory; replay-trajectory; evaluate; verify-trajectory; verify-runtime.

--output задаётся перед именем команды; существующий файл не перезаписывается.
build-manifest принимает JSON list {family,band,difficulty}; TEMPLATE разрешён только с --offline-fixture.
run-trajectory требует явный --offline-script: список ProviderResponse metadata с raw_hex.
replay-trajectory требует captures, reference cells, manifest и новый путь events.
evaluate по умолчанию работает в SCIENTIFIC mode. Обязательны --manifest, --config,
--event-logs, --calibration-artifact и --calibration-events. --event-logs — JSON map
trajectory_id → путь к соответствующему журналу. --config содержит сам FROZEN config,
не обёртку результата freeze-config. --seed в scientific mode запрещён: BOOTSTRAP использует
config.master_seed. --resource-sidecar допускается только как точная проверяемая копия
durations из TOOL_END, не как независимый источник измерений.

collect-run принимает те же обязательные источники, проверяет их и сохраняет sealed bundle.
evaluate принимает либо список trajectories, либо этот bundle и в обоих случаях заново
проверяет внешние журналы. Нельзя получить научные метрики из самостоятельно проставленного
флага validated или пересчитанного hash одного loose JSON.

```text
python -B -m mrab_r1 --output bundle.json collect-run trajectories.json --config frozen.json --manifest plan.json --event-logs event_paths.json --calibration-artifact calibration.json --calibration-events calibration.jsonl
python -B -m mrab_r1 --output evaluation.json evaluate bundle.json --config frozen.json --manifest plan.json --event-logs event_paths.json --calibration-artifact calibration.json --calibration-events calibration.jsonl
python -B -m mrab_r1 evaluate arithmetic_fixture.json --mode DESIGN_TEST_VECTOR_NOT_MODEL_RESULT --seed explicit-test-seed
```

Научный run не исполняется этими примерами автоматически. Последняя команда — только
арифметический test vector, не результат модели. Legacy Python-вызов с явно переданным
seed без scientific context сохранён исключительно в этом маркированном качестве.
Низкоуровневый evaluate_trajectory — прежний арифметический оператор для tests/replay,
а не альтернативный вход scientific evaluation. Replay report явно помечен test vector.

## CAS и lifecycle калибровки

`freeze-config config.json --content-dir cas` использует content-addressed storage:
каждый обычный файл непосредственно в cas называется **точным lowercase SHA-256 его bytes**,
без расширения. Все hashes из config должны разрешиться в эти файлы; bytes перепроверяются,
имя само по себе недостаточно. Hash difficulty tuple — JCS bytes, не произвольное pretty JSON.
freeze-config не извлекает bytes из названий identities и не скачивает неизвестные компоненты.

Для orchestration используйте Python API `search_and_confirm(config, provider_factory,
event_store, content=cas_bytes, tokenizer=..., offline_fixture=False)` только после отдельного
разрешения реальной калибровки. Вход — полностью настроенный TEMPLATE без выбранных tuples.
EventStore должен быть новым и пустым. API фиксирует pre-calibration lock; выполняет SEARCH;
материализует только selected_difficulty_tuples и configuration_status; проверяет окончательный
FROZEN config; выполняет CONFIRM; запечатывает CalibrationArtifact до MAIN.
Возвращаются final config, config hash, artifact, CAS bytes и fingerprint ledger.
Failed CONFIRM оставляет терминальный CALIBRATION_NOT_FEASIBLE; продолжить SEARCH в этом
журнале нельзя. Новый научный запуск требует отдельного решения, не автоматической подгонки.

Реальный TrajectoryRunner принимает calibration_artifact и calibration_events. reference_cells
в real mode передавать нельзя: две клетки выводятся из артефакта автоматически. Run start
фиксирует config, provider/runtime, artifact и reference hashes. Возобновление сравнивает их.
Hash цепочки защищает согласованность, но не заменяет подпись провайдера: хранитель должен
сохранить внешние hashes артефакта до MAIN и голов журналов/validated bundle перед анализом.

## Следующий отдельный этап

Выбор и конфигурация provider/model, tokenizer, component hashes, prompt hashes и полного FROZEN config.
ProviderAdapter допускает реальную реализацию без изменения benchmark semantics; её наличие не было
обязательным для Runtime0.1. Сейчас зарегистрированы только FakeProvider и ReplayProvider.
Конфигурационные тесты OFFLINE_FIXTURE_NOT_A_MODEL не являются выбором модели.

Реальные SEARCH/CONFIRM, model smoke480, pilot5120 и сравнение B0–B4 не запускались.
Планы 480/5120 — планы, а не выполненные исследования.
