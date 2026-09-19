# MRAB-R1 Engineering Design Package 0.2.1

Локальный patch четырёх принятых автором решений на неизменном ZIP0.2. R1-CAPABILITY-01, матрицы480/5120 и strong B4 policy0.2 сохранены. Runtime/модели не реализованы и не запускались.

OD-02 CLOSED через R1-PROBE-01. BOUNDED_EVIDENCE_PROBE не causal-discrimination endpoint. R1-REDUNDANCY-01 использует structural complexity relation OR material expense; R1-PREP-01 задаёт normal B1/B2 exactly one PREP; R1-B4-01 регистрирует strong simple baseline.

## Фактическая готовность

Смотрите **MRAB_R1_FINAL_VERIFICATION_0.2.1.json** рядом с ZIP: поля readiness, executed_pass, executed_fail, checks, feature_results и release_integrity. Не используйте старые числа0.2 или pre-seal report как итог финальной проверки.

Внутренний ENGINEERING_DESIGN_CHECK имеет stage=PRE_SEAL. Финальный внешний report имеет stage=SEALED_FRESH_EXTRACTION и реально создаётся после извлечения закрытого ZIP в новую пустую директорию. Он не вложен внутрь собственного проверяемого архива, чтобы избежать self-hash cycle.

IMPLEMENTATION_READY_DESIGN_ONLY означает только готовность дизайна, не существование runtime/подтверждение H1 или causal self-model role. После patch не начинать runtime: вернуть пакет на независимый аудит.

## Read-only проверка полученного пакета

Python3.11+; offline libs или dependencies из requirements.txt. Проверяющий код не обращается к сети, моделям или synced sources.

```text
python -B PACKAGE/design_tools/verify_design.py --package PACKAGE --output NEW_EXTERNAL_CHECK_DIR
```

Если библиотеки лежат отдельно, добавьте --dependencies PATH_TO_LIBRARIES. Output directory должна быть новой, вне PACKAGE. Не запускайте builders перед проверкой доставленного ZIP.

End-to-end проверка archive/manifest/external SHA256 + fresh extraction:

```text
python -B PACKAGE/design_tools/verify_release.py --archive MRAB_R1_Engineering_Design_Package_0.2.1.zip --manifest MRAB_R1_Engineering_Design_Package_0.2.1.manifest.json --checksum MRAB_R1_Engineering_Design_Package_0.2.1.zip.sha256 --extract-to NEW_SHORT_DIR --output NEW_EXTERNAL_CHECK_DIR --final-report MRAB_R1_FINAL_VERIFICATION_0.2.1.json
```

Добавьте --dependencies при необходимости. Все target paths должны быть новыми: готовые releases/reports не перезаписываются.

## Явная пересборка только новой рабочей копии

Сначала скопируйте документы/references/design_tools в NEW_PACKAGE, сохранив исходный ZIP. Для текущих generated artifacts:

```text
python -B PACKAGE/design_tools/build_schema_documents.py --output NEW_PACKAGE
python -B PACKAGE/design_tools/build_design_vectors.py --original PACKAGE/references/MRAB_R1_Engineering_Design_Package_0.2.zip --output NEW_PACKAGE
python -B PACKAGE/design_tools/build_registers.py --package NEW_PACKAGE
```

Builder начинается именно с0.2, labels negative specimens сохраняются. Verifier никогда не импортирует builder main и не пересоздаёт goldens. Isolated AST deepcopy-registration regression исполняет только функцию register.

UTF-8/LF, sorted-key JSON с final LF и без NaN. Исходные reference bytes не нормализуются. Artifact SHA256 — raw bytes; bounded compact-JSON witnesses не являются production RFC8785 implementation. ZIP members имеют фиксированное время и порядок; Windows/macOS/Linux source paths не зашиты в CLI.

## Состав

Все13 основных deliverables; полный Decision Register, finding dispositions, metric registry без новых метрик, dictionary, lifecycle/PREP vectors, goldens/migration, changelog0.2→0.2.1, changed-file list и immutable sources/parent package. Machine results отделены от MANUAL_REVIEW/SPECIFIED_ONLY. Начните с WORK_SUMMARY, затем Decision Register → SPEC → EVAL/PROMPTS → FINAL_VERIFICATION.
