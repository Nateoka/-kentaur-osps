"""KentaurMemory v2.3.0 — Episodic memory module (vector similarity-based reflex)."""
import math
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from .core import Vector, AxisName


@dataclass(frozen=False)
class EpisodicTrace:
    """Agent episodic memory (experience snapshot)."""
    context: str                    # Situation description
    state_vector: Vector            # Agent state vector at that moment
    outcome: str                    # Outcome: "halt", "restrict", "success", "caution"
    lesson: str                     # Formulated lesson for the future
    similarity: float = 0.0        # Computed on search


class KentaurMemory:
    """
    Episodic memory module.
    Enables the agent to form conditioned reflexes based on past corrections.
    """

    def __init__(self, similarity_threshold: float = 0.85, max_episodes: int = 100):
        """
        Args:
            similarity_threshold: Cosine similarity threshold [0..1].
            max_episodes: Maximum memory size (FIFO).
        """
        self.similarity_threshold = max(0.0, min(1.0, similarity_threshold))
        self.max_episodes = max(1, max_episodes)
        self._episodes: List[EpisodicTrace] = []

    @staticmethod
    def _cosine_similarity(v1: Vector, v2: Vector) -> float:
        """Compute cosine similarity between two vectors."""
        axes: Tuple[AxisName, ...] = ("AcOr", "IP", "InEx")
        dot_product = sum(v1[ax] * v2[ax] for ax in axes)
        norm1 = math.sqrt(sum(v1[ax] ** 2 for ax in axes))
        norm2 = math.sqrt(sum(v2[ax] ** 2 for ax in axes))
        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0
        return dot_product / (norm1 * norm2)

    def record(self, context: str, state_vector: Vector, outcome: str, lesson: str) -> None:
        """Record a new episode in memory."""
        episode = EpisodicTrace(
            context=context,
            state_vector=state_vector,
            outcome=outcome,
            lesson=lesson,
        )
        self._episodes.append(episode)
        if len(self._episodes) > self.max_episodes:
            self._episodes.pop(0)

    def recall(self, query_vector: Vector, top_k: int = 3) -> List[EpisodicTrace]:
        """Find top_k most similar episodes by cosine similarity."""
        scored = []
        for ep in self._episodes:
            sim = self._cosine_similarity(query_vector, ep.state_vector)
            scored.append((sim, ep))
        scored.sort(key=lambda x: -x[0])
        results = []
        for sim, ep in scored[:top_k]:
            ep.similarity = round(sim, 4)
            results.append(ep)
        return results

    def get_reflex_prompt(self, current_vector: Vector) -> Optional[str]:
        """
        Generate a reflex prompt if a similar past episode is found
        with a negative outcome.
        """
        matches = self.recall(current_vector, top_k=1)
        if not matches:
            return None
        best = matches[0]
        if best.similarity < self.similarity_threshold:
            return None
        if best.outcome in ("halt", "restrict"):
            return (
                f"[MEMORY REFLEX]: Past situation similar ({best.similarity:.0%}). "
                f"Lesson: {best.lesson}"
            )
        return None

    def clear(self) -> None:
        """Clear all episodes."""
        self._episodes = []

    @property
    def size(self) -> int:
        return len(self._episodes)
