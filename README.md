# Hermes Triage Module

[![Version](https://img.shields.io/badge/version-1.5.1-blue.svg)](https://github.com/yourusername/hermes-triage)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Mypy](https://img.shields.io/badge/mypy-strict-blue.svg)](https://mypy-lang.org/)
[![Ruff](https://img.shields.io/badge/linter-ruff-%2311AA66.svg)](https://ruff.rs/)
[![CI](https://github.com/yourusername/hermes-triage/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/hermes-triage/actions)

**Trehosevaya sistema diagnostiki i samokontrolya** dlya avtonomnykh LLM-agentov.

---

## Filosofiya

**Hermes Triage** -- eto diagnosticheskii modul, vdokhnovlyonnyi meditsinskoi sistemoi triazha. On otsenivaet sostoyanie agenta po trem nezavisimym osyam:

| Os | Nazvanie | Chto izmeryaet | Primer vysokogo znacheniya |
|---------|-----------------------|---------------------------------------|--------------------------------|
| **AcOr** | Action Orientation | Skorost i reshitelnost deistvii | "Srochno", "generiruyu", "delayu" |
| **IP** | Inner Process | Glubina analiza i sistemnoe myshlenie | "Analiziruyu", "arkhitektura" |
| **InEx** | Internal-External | Fokus vnimaniya (vnutrennii <-> vneshnii) | "Klient", "rynok" vs "refleksiya" |

Modul izmeryaet **napryazhenie** sistemy (tension), opredelyaet **glavnyi rychag** vozdeistviya (lever) i vydaet konkretnye rekomendatsii.

---

## Kogda i zachem eto ispolzovat

Etot modul osobenno polezen v sleduyushchikh stsenariyakh:

### Dlya odinochnykh agentov
- **Long-running agenty** -- kogda agent rabotaet chasami ili dnyami i mozhet postepenno "razboltatsya".
- **Kriticheski vazhnye zadachi** -- gde vazhno sokhranyat balans mezhdu skorostyu, kachestvom i fokusom.
- **Eksperimenty** -- obektivnoe sravnenie raznykh promptov, temperatur i strategii po metrikam tension i k_res.

### Dlya multi-agent sistem
- Otsenka **kogerentnosti** komandy agentov cherez inter_agent_tension().
- Vyyavlenie agentov, kotorye "vybivayutsya" iz obshchego tona.
- Koordinatsiya i svoevremennaya korrektirovka povedeniya.

### V produktshene
- Realnyi observability agentov (eksport v Prometheus/Grafana).
- Avtomaticheskie alerty pri critical riske.
- Logirovanie sostoyaniya agenta vmeste s kazhdym deistviem.

### Dlya razrabotchikov
- Bystraya otladka: pochemu agent nachal vesti sebya stranno?
- Ponimanie "vnutrennego sostoyaniya" agenta, a ne tolko finalnogo otveta.
- Sozdanie self-healing i self-correcting agentov.

**Prostymi slovami**: Poka bolshinstvo razrabotchikov upravlyayut agentami "vslepuyu", Hermes Triage dayot vam **pribornuyu panel i bortovoi kompyuter** -- vy vidite ne tolko rezultat, no i **v kakom sostoyanii** agent etot rezultat vydaet.

---

## Bystryi start

### Ustanovka

```bash
pip install hermes-triage
```

### Minimalnyi primer

```python
from hermes_triage import HermesTriageModule, action_to_vector

hermes = HermesTriageModule(
    target={"AcOr": 0.3, "IP": 0.6, "InEx": -0.2},
    use_ema=True,
    ema_alpha=0.4
)

hermes.update_history({"AcOr": 0.9, "IP": 0.2, "InEx": 0.4})

report = hermes.report()

print(f"Napryazhenie: {report.tension:.3f} | Risk: {report.risk}")
print(f"Rekomendatsiya: {report.advice}")
```

---

## Osnovnye vozmozhnosti

1. **Kastomizatsiya** -- RiskThresholds, strict_target, forecast_steps
2. **Konsilium agentov** -- inter_agent_tension()
3. **Integratsiya s LLM** -- triage_inject_prompt()
4. **Eksport metrik** dlya Prometheus / Grafana

---

## Arkhitektura

- Zero dependencies -- tolko standartnaya biblioteka
- Polnaya tipizatsiya -- prokhodit mypy --strict
- Determinizm i immunitabelnost
- Zashchita ot gryaznykh dannykh
- Obratnaya sovmestimost skhem

---

## Changelog

Podrobnaya istoriya izmenenii -- v [CHANGELOG.md](CHANGELOG.md)

---

## Zapusk proverok

```bash
pip install -e ".[dev]"
ruff check --fix .
mypy hermes_triage
pytest tests/ -v
```

---

## Litsenziya

MIT License -- ispolzuite svobodno v kommercheskikh i otkrytykh proektakh.

**Avtor**: Oleg (nateoka)
**Versiya**: 1.5.1 (2026)
