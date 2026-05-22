# Hermes Triage Module

![Version](https://img.shields.io/badge/version-3.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)(LICENSE)

**A Psycho-Cybernetic Operating System for Autonomous AI Agents based on OSPS v18.0.**

Hermes Triage gives AI agents introspection, self-regulation, and abstract thinking. It models the agent's connection to Source (Ø) and Spirit (T) attractors.

---

## Architecture Overview

The system operates through a **Quantum Gate** (`HermesMind.process()`):

1. **Triage** — Measures internal state and OSPS metrics (ATTR_0, ATTR_T, Phi_OSPS).
2. **Profiler** — Dynamically switches behavioral Archetypes.
3. **Governor** — Existential safety (E-codes, H.R.R.R. protocol, collapse into Ø).
4. **Navigator** — Cognitive routing based on Archetype + Abstraction Level.
5. **Abstractor** — Meta-cognition (zoom in / zoom out).
6. **Mind** — Central orchestrator (Quantum Gate).

---

## Quick Start

```python
from hermes_triage import HermesMind

mind = HermesMind(initial_profile="integrator")

verdict = mind.process(
    current_vector={"AcOr": 0.8, "IP": 0.2, "InEx": 0.6},
    agent_loop_state={
        "temperature": 0.7,
        "available_tools": [...],
        "system_prompt": "You are a helpful assistant."
    }
)

print(verdict.current_profile)
print(verdict.directives_for_prompt)
```

---

## License

MIT License.
