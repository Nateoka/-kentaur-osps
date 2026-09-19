"""Tool execution in a disposable process with an enforced wall-clock deadline."""
from pathlib import Path
import subprocess
import sys
from .canonical import loads,integer_dsl_bytes
from .errors import Failure


def execute_sealed_tool(spec,timeout_seconds=30):
    root=Path(__file__).resolve().parents[1]
    try:
        response=subprocess.run([sys.executable,"-B","-m","mrab_r1.tool_worker"],cwd=root,
            input=integer_dsl_bytes(spec),capture_output=True,timeout=timeout_seconds,check=False)
    except subprocess.TimeoutExpired:
        # subprocess.run kills and waits for this child; no unbounded background tool.
        raise Failure("INFRA_FAILURE","TOOL_DEADLINE_EXCEEDED") from None
    except OSError:
        raise Failure("INFRA_FAILURE","TOOL_PROCESS_UNAVAILABLE") from None
    if response.returncode:raise Failure("INFRA_FAILURE","TOOL_PROCESS_FAILURE")
    return loads(response.stdout)
