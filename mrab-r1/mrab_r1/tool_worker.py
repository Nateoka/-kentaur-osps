"""One isolated deterministic tool request. No profile, model or evaluator input."""
import json
import sys
from .canonical import loads
from .tasks import verify_task


def main():
    spec=loads(sys.stdin.buffer.read())
    result=verify_task(spec)
    sys.stdout.buffer.write(json.dumps(result,separators=(",",":"),allow_nan=False).encode("utf-8"))


if __name__=="__main__":main()
