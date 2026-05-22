# Hermes Triage Module

![Version](https://img.shields.io/badge/version-2.3.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![Tests](https://img.shields.io/badge/tests-20%20passed-brightgreen.svg)

**A Psycho-Cybernetic Operating System for Autonomous AI Agents.**

Hermes Triage is a diagnostic and control framework that provides AI agents with introspection, self-regulation, and abstract thinking capabilities. It moves beyond simple prompt engineering by giving agents a mathematical model of their own internal state.

---

## Core Architecture

The system operates as a layered nervous system:

1. **Triage (Receptors):** Measures the agent's state along 3 axes: AcOr (Action Orientation), IP (Inner Process), and InEx (Internal-External focus). Calculates tension, resilience, and risk.
2. **Governor (Immune System):** Enforces boundaries. Blocks dangerous tools and interrupts loops when risk is critical.
3. **Navigator (Prefrontal Cortex):** Prescribes specific tools and cognitive patterns to restore balance.
4. **Profiler (Endocrine System):** Switches behavioral profiles (Analyst, Executor, Crisis) on the fly.
5. **Memory (Scars):** Episodic memory based on vector similarity. Prevents the agent from repeating past mistakes.
6. **Abstractor (Meta-cognition):** Detects if the agent is stuck in details (Concrete Swamp) or lost in philosophy, and forces a zoom shift.
7. **Mind (Central Nervous System):** A unified facade orchestrating all modules in a single `process()` call.

---

## Quick Start

### Installation

```bash
pip install hermes-triage
```

### Usage

```python
from hermes_triage import HermesMind

# Initialize the agent's nervous system
mind = HermesMind(profile="executor")

# Process agent state in a loop
verdict = mind.process(
    current_vector={"AcOr": 0.9, "IP": 0.1, "InEx": 0.5},  # Agent is panicking
    agent_loop_state={
        "temperature": 0.8,
        "available_tools": ["execute_bash", "think_step_by_step"],
        "system_prompt": "You are a helpful assistant."
    }
)

# Apply system directives
if verdict.modified_state.get("force_stop"):
    raise SystemExit("Agent halted by Governor")

print(f"Risk: {verdict.report.risk}")
print(f"Directives: {verdict.modified_state}")
```

---

## Development

### Setup

```bash
pip install -e ".[dev]"
```

### Testing & Linting

```bash
pytest tests/ -v
ruff check .
mypy hermes_triage
```

---

## License

MIT License.
