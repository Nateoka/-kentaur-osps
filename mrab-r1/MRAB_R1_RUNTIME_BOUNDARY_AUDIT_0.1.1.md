# Boundary audit 0.1.1

Область независимой исполняемой проверки — повторная установка и весь suite из новой распаковки,
не из рабочей копии. Это не внешний человеческий review и не проверка реального provider.
Фактический вердикт и число PASS берутся только из внешнего verification report после завершения.

| Граница | Положительная проверка | Отрицательная проверка |
|---|---|---|
| I18 | Generated plan + FROZEN config + captured trajectory | Все scalar identity fields; семь seed domains; manifest hash; template/config drift |
| Scientific evaluate | Sealed synthetic bundle через тот же обязательный validator, mode TEST_VECTOR | Отсутствующий config/manifest/log/artifact; invariant failure до вызова metric function |
| Provenance | Exact EPISODE_RECORD/CHECKPOINT, request/response bytes и usage | Подмена loose usage, latency, output hash, sampling seed и hash chain |
| Tool latency | Точный итог по своим TOOL_END; равный sidecar допускается | Независимый пустой/иной sidecar отклоняется |
| Bootstrap | Перехват фактических Stream-вызовов: frozen master_seed, domain BOOTSTRAP | Произвольный seed при связанном/scientific анализе отклоняется |
| Calibration | 20×200 синтетических individual records + SEARCH captures, actual task manifests | Подмена successes, dataset_hash, n, architecture, scope, band, tuple |
| Reference cells | Две автоматически материализованные клетки с config modes/scope | Неуникальная/неправильная ячейка, подменённый trajectory reference |
| Lifecycle | Real-interface constructor допускает locked TEMPLATE без tuples и не делает вызовов | Изменение settings после lock; failed CONFIRM terminal; повторный SEARCH в журнале запрещён |
| Resume | Прежний safe-boundary positive test сохранён | Подмена config, reference hash, calibration artifact hash в RUN_START |
| Legacy | Byte-identical прежние test-файлы, все 109 methods повторены | Оба согласованных correction regression сохранены |
| Release | Внешний manifest, полный byte check до/после suite, новый offline environment | Отказ перезаписи архива; отклонение отсутствующего baseline/design hash |

Синтетическая калибровочная fixture конструирует заданные ответы напрямую, не вызывает
CalibrationEngine.measurement, provider.invoke или API модели. Её 4000 confirmation records
и 800 search records — тест границ данных, не измеренная способность и не успешная реальная
калибровка. Scientific mode специально отклоняет этот артефакт.

## Остаточная граница доверия

В процессе release audit отклонён первый упаковочный кандидат: слишком широкий фильтр
исключал не только корневой CONTENT_MANIFEST.json, но и immutable design/…/CONTENT_MANIFEST.json.
129 tests в нём прошли, однако проверка всех 65 design-файлов обоснованно запретила сертификацию.
Фильтр исправлен на exact root path. Исходные design bytes не редактировались. Финальный архив
проверяется заново; design verification выполняется до и после полного fresh-extraction suite.

Hash-chained logs не удостоверяют внешнее происхождение записи. Конфигурация провайдера,
подлинность возвращённых usage/revision, хранение внешних seals и последующие реальные calibration
входят в следующий разрешаемый этап. Readiness этого выпуска ограничен provider configuration.
