# Изменения 0.1 → 0.2

Историческая запись исходного release0.2, не текущий статус0.2.1. Закрытие OD-02 и новые нормативные правила находятся в CHANGELOG_0.2_TO_0.2.1.md и актуальном Decision Register.

Контракты/package0.2; идентичность семейства benchmark0.1 сохранена. Protocol revision `R1_0.1_DESIGN_CLOSURE_0.2`: новые данные нельзя бесшовно смешивать со старым protocol hash.

- Воспроизведён дефект старого корпуса40/42. Два negative B4/C0 восстановлены без изменения expected=false; регистрация теперь deepcopy. Новая проверка читает сериализованные файлы, не пересоздаёт их.
- R1-CAPABILITY-01 принят как авторское решение: разделены p_reference и неизвестная p_operational(t); scope/public state/feedback/ledger/tracker получили configuration/mode/history адресность. REFERENCE_PROFILE_DISTANCE — secondary descriptive, не истинность live map.
- Mismatch и evidence support для SOLO разделены. Beta(4,2) контрпример и конечная достижимость gates проверяются точно. Условные endpoints сопровождаются fixed-window ITT и reach.
- E07 восстановлен OR для избыточности против B2 или B4. B1 связан с H0-COMPUTE, достоверный вред не требует удорожания, mixed tradeoff и NO_STRUCTURAL_ADVANTAGE сохранены явно. Пороги — политика оценки, не новая онтология.
- Общая B2/B3 admissibility, атомарные версии и stage snapshots; rejected attempts сохраняются. C0 scope restart, CURRENT/NEXT, отмена/замена/expiry и pending-at-end разведены со stop. Коммит переживает последующий failed ACTION.
- Common public evidence index до32 и anchors до8 добавлены для старых refs/rollback. Это видимое изменение памяти всех arms; recent window остаётся10. Никакого скрытого преимущества B3; overflow нельзя лечить молчаливой обрезкой.
- Probe labels больше не удостоверяют различающую силу. Старый schema test probe-needs-alternatives явно заменён bookkeeping-draft specimen в corpus_migration. **Научное решение OD-02 открыто**; это не подмена авторского выбора зелёным тестом.
- Calls сохраняют request bytes и timeout; usage имеет observed/estimated/unavailable по категориям. Freeze отклоняет placeholders/нулевые hashes. Runtime identities/config template не выдаются за реальные.
- Полный реестр41 метрики/диагностики/gate с derivation и missingness; затронутые claims, число событий и behavioral damage различаются. Наследованные truth-метрики переименованы/лишены недоступного права вывода.
- Один seed preimage включая TASK_ID/retry/split; F1 допустима лишь cyclic symmetry с неизменным ROTATE. F2 задан частный exact-group solution-anchored algorithm с ограниченным n!*k! перебором, без production solver; canonical answer order не используется в public rendering.
- Smoke остаётся480 (8+4), pilot5120 (24+8). Отдельные длинные authored traces вне матрицы покрывают недоступные smoke пути; confirmation4000 measurements/6400 calls пересчитаны, search/repair отдельно.
- LOW_ONLY_DISTRUST/EVIDENCE_INDEPENDENT_REVISION добавлены; отсутствие accurate LOW в C1 не скрыто и не «исправлено» без разрешения.
- Полные источники, проверенные hashes, direct-conversation основание исключения98 с явным пределом provenance. Каждый A01–A16 имеет disposition и доказательный адрес; отсутствие дополнительного hard-audit не маскируется.

Пакет не содержит результатов моделей. Готовность выводится из проверок и open decisions; OD-02 оставляет DESIGN_REVIEW_REQUIRED.
