# Runtime 0.1.1 — implementation decisions

Область: provenance → calibration orchestration → scientific evaluation. Замороженные
65 design-файлов, оригинальный ZIP, пять исходных схем и научные определения неизменны.
Это технический выпуск, не эмпирический результат и не подтверждение H1.

1. **R11-I18**. Scientific plan требует actual FROZEN config. До работы с trajectory
   проверяются hash manifest, config hash, schema, неизменяемые настройки и hashes реально
   загруженных runtime/prompt-компонентов. Все запрошенные поля плановой идентичности,
   семь seed digests и episode schedule сверяются явно. Старый двухаргументный validator
   допустим лишь для помеченного design test manifest и не открывает scientific evaluator.
2. **R11-FAIL-CLOSED**. Весь переданный набор проходит обязательную проверку до первого
   вычисления метрик. Любой сбой границы — typed INFRA_FAILURE. Исключение отдельного
   корректно зарегистрированного infra-эпизода/неполной траектории остаётся прежней научной
   семантикой; повреждение источника не превращается в attrition или научный результат.
3. **R11-CAPTURE-BUNDLE**. Collector связывает RUN_START, CALL_REQUEST/RESPONSE/USAGE,
   EPISODE_RECORD, TOOL_START/END и конечный CHECKPOINT. CHECKPOINT хранит exact trajectory.
   Проверяются request bytes, доступные raw output bytes, model/call settings и MODEL seeds.
   Ресурсные поля дополнительно сверяются с наблюдениями, сохранёнными в CALL_RESPONSE.
   Bundle содержит hashes конфигурации, плана, артефакта и голов журналов. При анализе bundle
   заново проверяется против исходных цепочек; флаг PASS не является входным основанием.
4. **R11-RESOURCE**. Tool latency приходит исключительно из согласованного TOOL_END своего
   эпизода. Внешний resource sidecar — только проверяемая exact copy. Перенос новых timings
   replay в исходные научные измерения запрещён этой границей.
5. **R11-BOOTSTRAP**. Существующий joint block BOOTSTRAP domain использует frozen master_seed
   напрямую, без нового преобразования или изменения resampling. Ровно frozen bootstrap_draws.
   Arbitrary seed разрешён лишь для DESIGN_TEST_VECTOR_NOT_MODEL_RESULT. Для сохранения
   прежних арифметических tests legacy API с явно переданным seed без scientific inputs
   маркируется test vector и лишён empirical entitlements. CLI требует эту маркировку явно.
6. **R11-CAL-LOCK**. provider/capability/prompt/tool/scientific settings запираются до SEARCH.
   Lock содержит настроенный TEMPLATE с пустыми selected tuples. Единственные разрешённые
   различия final config — configuration_status и selected_difficulty_tuples. Никакая другая
   настройка, включая seed, timeout, budget, tokenizer или sampling, не может измениться.
7. **R11-CAL-ARTIFACT**. Отдельная runtime envelope, не поправка исходной schema. Содержит
   lock, config/provider/runtime identities, четыре tuple identities, четыре confirmation
   item-manifest hashes, все 20 cells, PASS gate и hash предшествующей цепочки. В журнале
   артефакт запечатывается отдельным событием. Counts пересчитываются из individual captures,
   включая ответ ACTION, item identity, split isolation, SOLO/reset/PREP policy и manifest bytes.
   Search selection проверяется по объявленному порядку кандидатов и исходным 40 measurements.
8. **R11-REFERENCE**. Из артефакта берутся строго две уникальные клетки: architecture × family ×
   target band (контрольная семья HIGH). Проверяются n=200, common tuple, dataset hash,
   scope, difficulty/context, capability configuration и execution modes. В real mode произвольные
   reference cells запрещены. Fake/Replay без артефакта сохранены только для прежних offline tests.
9. **R11-TERMINAL-CONFIRM**. Неудачный gate полного CONFIRM сохраняет отдельный sealed artifact
   со всеми 20 cells и gate_status=CALIBRATION_NOT_FEASIBLE, затем терминальную причину. Никакого цикла донастройки SEARCH. Частичная либо повреждённая
   калибровка не выпускает пригодный для MAIN PASS artifact. Повторный вход в непустой журнал запрещён.
10. **R11-RESUME**. С RUN_START сравниваются trajectory, manifest, config, runtime/provider,
    calibration artifact и exact reference identity. Старые журналы без новых seal-полей не получают
    доверия автоматически: они остаются историческими evidence, а не незаметно мигрируют в science.
11. **R11-PERFORMANCE**. Batch-проверка цепочки использует тот же ECMAScript/JCS serializer;
    parity проверяется тестом. Успешная проверка calibration кэшируется только по hash заново
    прочитанных bytes + artifact/config + mode, никогда по пути, timestamp или чужому флагу.
    Общий экземпляр валидатора answer может передаваться при массовой проверке; правила не меняются.
12. **R11-RELEASE**. Внешние manifest, SHA и fresh-extraction report не включаются сами в себя.
    Новая распаковка, новая offline-среда, проверка полного набора файлов до и после tests.
    В публичном отчёте — относительные evidence paths, без имени пользователя Windows.
    CAS convention для freeze-config документирован в README. Исходные результаты 0.1 сохранены.

## Сохранённые авторские решения

- R1-E07-HARM-01: known independent HARM не уничтожается missing conditional CI; сохраняются
  uncertainty reasons; HARM + BENEFIT → MIXED_TRADEOFF, HARM без BENEFIT → COUNTERPRODUCTIVE.
- R1-STORAGE-REQUEST-01: снят только request_bytes/maxLength. PREP, полная история и 16384-token
  input cap неизменны; исходные schema bytes остаются прежними.

## Ограничения доверия и следующий этап

Hash chain — доказательство внутренней согласованности, не криптографическая подпись провайдера.
Хранитель должен удерживать внешний artifact hash до MAIN и головы журналов до анализа. Полная
злонамеренная перепись всех артефактов вместе с доверенными внешними hashes не предотвращается
самоподписанными JSON. Аутентификация сервиса, реальные usage accounting/tokenizer и observed model
revision проверяются отдельно при конфигурации провайдера. Встроенных real adapters по-прежнему нет.

Приёмка использует только offline synthetic/Fake/Replay evidence. Ни реальные SEARCH/CONFIRM,
ни model smoke/pilot, ни научное сравнение B0–B4 в этом patch не проводятся.
