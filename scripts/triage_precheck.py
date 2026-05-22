"""
Pre-flight Triage check for Hermes Orchestrator.
Runs before each response to ensure balanced state.
"""
import sys, os

# Add project to path
sys.path.insert(0, r'D:\HermesTriage')
from hermes_triage import HermesTriageModule

# Target state for an orchestrator: balanced action/analysis, moderate external focus
TARGET = {'AcOr': 0.5, 'IP': 0.5, 'InEx': 0.3}

def check_state(current_vector: dict) -> dict:
    """Run triage and return verdict."""
    triage = HermesTriageModule(target=TARGET, use_ema=True)
    triage.update_history(current_vector)
    rep = triage.report(current_vector)
    return {
        'vector': rep.current_vector,
        'tension': rep.tension,
        'risk': rep.risk,
        'stable': rep.stable,
        'advice': rep.advice,
        'lever': (rep.lever_axis, rep.lever_direction, rep.lever_delta),
        'k_res': rep.k_res,
        'verdict': 'OK' if rep.risk == 'low' else 'CAUTION' if rep.risk == 'medium' else 'HALT'
    }

if __name__ == '__main__':
    import json
    # Default check
    result = check_state({'AcOr': 0.6, 'IP': 0.6, 'InEx': 0.4})
    print(json.dumps(result, indent=2))
