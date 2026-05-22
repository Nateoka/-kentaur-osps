# Changelog

Vse zamednye izmeneniya v proekte Hermes Triage Module budut dokumentirovatsya v etom faile.

Format osnovan na [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/),
a versii sootvetstvuyut [Semantic Versioning](https://semver.org/lang/ru/).

---

## [1.5.1] - 2026-05-22

### Added
- Polnaya paketnaya struktura proekta (hermes_triage/ s __init__.py i triage.py).
- Fail py.typed dlya korrektnoi raboty type hints pri ustanovke cherez pip.
- Podderzhka mypy --strict.
- Rasshirennyi razdel "Kogda i zachem eto ispolzovat" v README.md.
- GitHub Actions CI/CD (testirovanie na Python 3.9-3.12).
- Zhestkie edge-keysy v testakh (gryaznyi JSON, nevalidnye tipy, klampping, migratsii versii).
- Polnaya dokumentatsiya: README.md, CHANGELOG.md, .gitignore.

### Changed
- AXES izmenyon s List na Tuple[AxisName, ...] dlya sovmestimosti s mypy.
- Uluchshena bezopasnost deserializatsii v from_dict().
- Obnovlyon stil dokumentatsii i primerov.

### Fixed
- Obrabotka steps=0 v metode forecast().
- Melkie PEP8 i stilevye uluchsheniya.

---

## [1.4.0] - 2026-05-20

### Added
- Parametr forecast_steps v konstruktor i report().
- Uluchshennoe uslovie stable s myagkim porogom (tens < 1e-6).
- Pereimenovanie variance -> mean_squared_deviation dlya semanticheskoi tochnosti.

### Changed
- Razdelenie porogov low (0.20) i medium (0.3) v RiskThresholds.

---

## [1.3.0] - 2026-05-18

### Added
- Sistema rychagov (lever) s prioritetom osei (AcOr > IP > InEx).
- Prognoz dvizheniya k tseli (forecast).
- Eksport metrik dlya Prometheus/Grafana (export_metrics).
- Polnaya tipizatsiya i immunitabelnost dataklassov.

### Initial Release
- Bazovaya funktsionalnost: tension, report, EMA/mediana, serializatsiya.

---

## [1.2.0] - 2026-05-15

### Added
- Pervaya rabochaya versiya modulya.
- Podderzhka EMA i mediany.
- Bazovaya serializatsiya/deserializatsiya.
