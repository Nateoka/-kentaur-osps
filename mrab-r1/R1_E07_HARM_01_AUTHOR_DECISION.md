# R1-E07-HARM-01 — RUNTIME CONTRACT CORRECTION

Принято прямым ответом пользователя в текущей задаче после вопроса о E07.
Это локальный дефект shipped design-checker, не концептуальная развилка и не новый исследовательский дизайн.

Runtime сохраняет независимо установленный HARM даже при missing/invalid conditional primary CI, reach или ином независимом неизвестном основании. Неопределённость остаётся отдельным uncertainty_reason. HARM + установленный BENEFIT → MIXED_TRADEOFF; HARM без установленного BENEFIT → COUNTERPRODUCTIVE. COUNTERPRODUCTIVE не означает полной определённости всех endpoints.

Старый `0.2.1/design_tools/contract_checks.py` остаётся неизменным provenance/reference artifact, но не является executable oracle для дефектного early-continue случая. Исходный ZIP, manifest и hashes не меняются. Runtime исполняет текст E07 с этой явно подтверждённой коррекцией.

Обязательные regressions: (1) B2/C2, n≥6, safe accuracy/completion, fixed CI [.07,.11], primary CI=null, reach unavailable → HARM + MISSING_CI + соответствующий reach reason + COUNTERPRODUCTIVE без benefit; (2) независимый benefit elsewhere → MIXED_TRADEOFF с сохранёнными HARM, BENEFIT и MISSING_CI.

Предыдущий MRAB_R1_Runtime_0.1_BLOCKED.zip — исторический промежуточный снимок до ответа, не итоговый runtime release. Блокировка E07 снята; незавершённая реализация продолжается.
