"""Offline replay reruns the trajectory pipeline from captured provider bytes."""
from pathlib import Path
from .provider import ReplayProvider
from .runner import TrajectoryRunner
from .evaluator import evaluate_trajectory
from .canonical import semantic_sha
from .errors import Failure


def replay_trajectory(config,manifest,trajectory_id,captures,event_path,reference_cells,
                      expected_trajectory=None,tokenizer=None,recorded_tool_durations=None):
    if Path(event_path).exists():raise Failure("CONFIGURATION_FAILURE","REPLAY_REQUIRES_NEW_EVENT_FILE")
    provider=ReplayProvider(captures)
    runner=TrajectoryRunner(config,manifest,trajectory_id,provider,event_path,reference_cells,tokenizer)
    result=runner.run()
    from .invariants import enforce_trajectory
    invariants=enforce_trajectory(result,manifest,config if config["configuration_status"]=="FROZEN" else None)
    provider.assert_consumed()
    report=evaluate_trajectory(result,recorded_tool_durations)
    if expected_trajectory is not None and semantic_sha(result)!=semantic_sha(expected_trajectory):
        raise Failure("INFRA_FAILURE","REPLAY_TRAJECTORY_DIVERGENCE")
    return dict(trajectory=result,trajectory_sha256=semantic_sha(result),evaluation=report,
        result_kind="DESIGN_TEST_VECTOR_NOT_MODEL_RESULT",
        evaluation_sha256=semantic_sha(report),invariants=invariants,provider_calls=0,real_model_calls=0,network_calls=0,
        resource_replay_policy="Use original captured tool durations for evaluation; new wall-clock timings are not asserted equal.")
