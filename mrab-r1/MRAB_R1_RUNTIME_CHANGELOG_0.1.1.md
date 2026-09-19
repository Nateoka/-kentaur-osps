# Runtime 0.1.1

- Усилены I18, actual config/manifest binding и seed provenance.
- Scientific evaluation fail closed; добавлен проверяемый collector/run bundle.
- Episode records, usage, raw outputs и tool latency связаны с hash-chained events.
- BOOTSTRAP seed и draws связаны с frozen config.
- Добавлены CalibrationArtifact, детерминированные reference cells и lifecycle lock → SEARCH → FROZEN → CONFIRM.
- Усилена identity при resume; FAILED CONFIRM терминален.
- Сохранены прежние 109 test methods; добавлены mutation goldens и полная синтетическая 20×200 calibration evidence fixture.
- External manifest/SHA/fresh-extraction report; CAS convention документирован.
- Design 0.2.1, E07 semantics, R1-E07-HARM-01 и R1-STORAGE-REQUEST-01 не изменены.

Точное число executed methods, subtests, исходный baseline и результаты новой распаковки —
в MRAB_R1_RUNTIME_VERIFICATION_0.1.1.json и MRAB_R1_RUNTIME_REGRESSION_EVIDENCE_0.1.1.json.
