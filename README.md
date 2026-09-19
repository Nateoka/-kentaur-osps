# KentaurOSPS

![Version](https://img.shields.io/badge/version-3.5.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**A Psycho-Cybernetic Operating System for Autonomous AI Agents based on OSPS v18.0.**

KentaurOSPS gives AI agents introspection, self-regulation, abstract thinking, episodic memory, and existential safety.

## Installation

```bash
pip install kentaur-osps
```

---

## Architecture Overview

```
                    ┌─────────────────────────────────────┐
                    │         KENTAURMIND (Quantum Gate)   │
                    │  ┌─────────┐  ┌──────────┐          │
 User Input ────────┼─>│ TRIAGE  │─>│ PROFILER │──...     │
                    │  └─────────┘  └──────────┘          │
                    │       │              │               │
                    │       v              v               │
                    │  ┌──────────┐  ┌────────────┐       │
                    │  │ GOVERNOR │─>│  NAVIGATOR │       │
                    │  │ (E-codes)│  │ (Archetype │       │
                    │  │ HRRR     │  │  Therapy)  │       │
                    │  └──────────┘  └────────────┘       │
                    │       │              │               │
                    │       v              v               │
                    │  ┌────────────┐  ┌──────────┐       │
                    │  │  MEMORY   │  │ABSTRACTOR│       │
                    │  │ (Reflexes)│  │ (Zoom)   │       │
                    │  └────────────┘  └──────────┘       │
                    │       │              │               │
                    │       v              v               │
                    │  ┌──────────────────────────┐       │
                    │  │   OUTPUT: Directives +    │       │
                    │  │   Modified Agent State    │       │
                    │  └──────────────────────────┘       │
                    └─────────────────────────────────────┘
```

### Core Axes (Triage Space)

| Axis | Meaning | Low | High |
|------|---------|-----|------|
| **AcOr** | Action / Orientation | Paralysis, overthinking | Panic, impulsive action |
| **IP** | Inner Process | Reactive, no planning | Analysis paralysis |
| **InEx** | Internal / External | Withdrawn, self-absorbed | Over-focused on external |

### OSPS v18.0 Metrics

- **ATTR_0** — Coupling to Source attractor (Ø): ability to zero/reset
- **ATTR_T** — Coupling to Spirit attractor (T): ability to synthesize
- **Phi_OSPS** — Anti-fragmentation index: drops under crisis
- **K_flow** — Energy conductivity (psychodynamic Ohm's law)
- **fuse_conflicts** — Crisis counter (tracks governor activations)

---

## Quick Start

```python
from kentaur_osps import KentaurMind

# Initialize the quantum gate
mind = KentaurMind(initial_profile="integrator")

# Process agent state
verdict = mind.process(
    current_vector={"AcOr": 0.8, "IP": 0.2, "InEx": 0.6},
    agent_loop_state={
        "temperature": 0.7,
        "available_tools": [...],
        "system_prompt": "You are a helpful assistant."
    },
    context="User requested database operation"
)

print(f"Profile: {verdict.current_profile}")
print(f"Phi: {verdict.report.phi_osps:.3f}")
print(f"Directives: {verdict.directives_for_prompt}")
```

### With ReAct Loop

```python
from kentaur_osps import KentaurMind, KentaurReActLoop
from openai import OpenAI

mind = KentaurMind(initial_profile="executor")
client = OpenAI(api_key="...")

loop = KentaurReActLoop(
    mind=mind,
    llm_client=client,
    tools=[...],
    max_iterations=5
)

result = loop.run(
    user_prompt="Deploy the server",
    initial_vector={"AcOr": 0.6, "IP": 0.5, "InEx": 0.3},
    tool_executor=lambda name, args: f"Executed {name}"
)
```

---

## Current OSPS Features

- ✅ Three-axis diagnostic space (AcOr, IP, InEx)
- ✅ Tension, lever, forecast engine
- ✅ Dynamic profiling (4 archetypes: master, alchemist, integrator, sleeper)
- ✅ Governor with E-codes (E-000, E-301, E-401, E-502)
- ✅ H.R.R.R. protocol (Hold, Read, Route, Render)
- ✅ Navigator with archetype + abstraction routing
- ✅ Abstractor meta-cognition (zoom in/out)
- ✅ Episodic memory with contextual lesson generation
- ✅ Subconscious reflexes from past crises
- ✅ fuse_conflicts tracking for Phi dynamics
- ✅ Serialization (to_dict / from_dict)
- ✅ Fully typed (mypy compatible, InputVector API)
- ✅ ReAct loop adapter for production LLM integration

---

## Live Dashboard

Run the real-time monitoring:

```bash
streamlit run dashboard/app.py
```

This shows live Archetype, Tension, Phi_OSPS, ATTR_0, ATTR_T, Fuse Conflicts, recent reflexes, and a Phi_OSPS history chart.

---

## Persistent Runtime

To run Kentaur as a daemon:

```bash
python -m kentaur_osps.runtime
```

This will keep the agent alive 24/7, accumulating memory and self-regulating via periodic heartbeat diagnostics.

---

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
mypy kentaur_osps
```

---

## MRAB-R1 Benchmark (`mrab-r1/`)

**MRAB-R1 (False Self-Model v1)** — a falsifiable benchmark for the correctness and corrigibility
of an agent's self-model, shipped here as a self-contained offline runtime.

- 129 executable tests, 24 invariants, 41 registered metrics, 51 fixture IDs
- B0–B4 architecture comparison, 8 scripted trajectories, τ-costed actions
- Fake/Replay providers, JCS/strict JSON, content-addressed calibration lifecycle
- It is allowed to return `REDUNDANT` / `NO_STRUCTURAL_ADVANTAGE` — it can refute its own premise
- No LLM judge: every acceptance claim rests on an executable check

Methodology author: **P. P. Klabukov**. Published with his explicit permission.
Runtime: [`mrab-r1/README.md`](mrab-r1/README.md) · A/B comparison (bare model vs. model + KentaurOSPS):
[`mrab-r1/ab-test/REPORT.md`](mrab-r1/ab-test/REPORT.md)

```bash
cd mrab-r1
python -m venv .venv && source .venv/bin/activate
pip install jsonschema==4.26.0 referencing==0.37.0
export MRAB_JCS_NODE="$(command -v node)"   # required by the hardening tests
python -B -m mrab_r1 verify-runtime
```

---

## License & authorship

- Code — **MIT** ([`LICENSE`](LICENSE)), in effect since 2024 and preserved unchanged.
- Documents and texts — **CC BY-SA 4.0** ([`LICENSE-DOCS`](LICENSE-DOCS)).
- Authors and contribution split — [`AUTHORS.md`](AUTHORS.md).
