# Что не продублировано и как проверить workspace

Source/test/tool files скопированы без изменений из Runtime 0.1.1. Файлы не потеряны:
они доступны в `../02_SEALED_RUNTIME_RELEASE/MRAB_R1_Runtime_0.1.1.zip`.

Не продублированы wheelhouse, большие `verification/long_trace_*`, остальные generated traces,
исторические архивы/evidence в `design/.../references/` и `verification_evidence/`.
Root release tools также сохранены byte-identical, но их исторические предположения о соседних
каталогах/старом ZIP не превращают эту сокращённую workspace в готовую release build machine.
Не запускайте packaging scripts без ознакомления с их входами.

## Offline suite: восстановление зависимостей

Работайте в короткопутной **проверочной копии** этой workspace, чтобы не изменять handoff.

1. Из sealed Runtime ZIP извлеките `mrab_r1_runtime/wheelhouse/` в `wheelhouse/` копии.
2. Из того же ZIP извлеките **точный** файл
   `mrab_r1_runtime/verification/long_trace_01/SCRIPTED_32_TRAJECTORY.json`
   в `verification/long_trace_01/SCRIPTED_32_TRAJECTORY.json` копии.
   Один из 129 тестов действительно читает этот synthetic fixture. Его нельзя пропускать.
3. При необходимости полной `verify-design-contract` распакуйте неизменённый Design ZIP из папки 03
   в `design/` копии, сохранив его корень `mrab_r1_engineering_design_0.2.1/`.
   Отсутствующие provenance references — намеренное сокращение workspace, не утрата из handoff.
4. Используйте уже установленный Python 3.12 на Windows x64 и Node.js.
   Python/Node не поставляются этим архивом. Установка зависимостей offline:

```text
python -m venv .venv
.venv\Scripts\python -m pip install --no-index --find-links wheelhouse --require-hashes -r requirements.offline.lock
.venv\Scripts\python -B -m mrab_r1 verify-runtime
```

При необходимости задайте `MRAB_JCS_NODE` путём к установленному Node; не коммитьте личный путь.
Ожидается 129 tests / 0 failures / 0 errors. Fake/Replay и synthetic calibration fixture —
`DESIGN_TEST_VECTOR_NOT_MODEL_RESULT`, а не реальные measurements.

Установка package wheel самого runtime не заявлялась как проверенный способ; используйте source tree.
На другой платформе не устанавливайте принудительно несовместимые wheels и не считайте это
научным FAIL. Зафиксируйте несовместимость среды и отдельный план её воспроизводимой настройки.
