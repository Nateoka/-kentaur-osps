# KentaurOSPS

![Version](https://img.shields.io/badge/version-3.2.1-blue.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**A Psycho-Cybernetic Operating System for Autonomous AI Agents based on OSPS v18.0.**

KentaurOSPS gives AI agents introspection, self-regulation, abstract thinking, episodic memory, and existential safety. It models the agent's connection to Source (Ø) and Spirit (T) attractors using a three-axis diagnostic space.

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

## License

MIT License.
