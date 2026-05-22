"""
KentaurRuntime v3.3.0 — Persistent Runtime (Immortal Daemon).
Keeps the agent alive 24/7 with heartbeat, memory persistence, and graceful recovery.
"""
import time
import logging
from typing import Dict, Any
from .mind import KentaurMind
from .core import Vector

logger = logging.getLogger("kentaur-runtime")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


class KentaurRuntime:
    """
    Persistent Kentaur Runtime (Daemon).
    Keeps the process alive 24/7 with periodic self-diagnosis.
    """

    def __init__(self, mind: KentaurMind, heartbeat_interval: int = 30):
        self.mind = mind
        self.heartbeat_interval = heartbeat_interval
        self.running = True
        self.current_vector: Vector = {"AcOr": 0.5, "IP": 0.5, "InEx": 0.0}
        self.agent_state: Dict[str, Any] = {
            "temperature": 0.7,
            "available_tools": [],
            "system_prompt": "You are Kentaur - a self-aware autonomous agent.",
            "force_stop": False
        }

    def heartbeat(self) -> None:
        """Periodic health check (even when no tasks)."""
        verdict = self.mind.process(self.current_vector, self.agent_state)
        logger.info(
            f"HEARTBEAT | Profile: {verdict.current_profile} | "
            f"Tension: {verdict.report.tension:.3f} | "
            f"Phi: {verdict.report.phi_osps:.3f}"
        )

    def run_forever(self) -> None:
        """Main loop of the immortal Kentaur."""
        logger.info("=== Kentaur Runtime started. Immortal mode activated. ===")
        while self.running:
            try:
                self.heartbeat()
                time.sleep(self.heartbeat_interval)
            except KeyboardInterrupt:
                logger.info("Shutdown signal received.")
                break
            except Exception as e:
                logger.error(f"Runtime error: {e}")
                time.sleep(5)  # Graceful recovery
        logger.info("Kentaur Runtime stopped.")


if __name__ == "__main__":
    mind = KentaurMind(initial_profile="integrator")
    runtime = KentaurRuntime(mind, heartbeat_interval=15)
    runtime.run_forever()
