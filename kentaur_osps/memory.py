"""KentaurMemory v3.3.0 — Persistent episodic memory with contextual lessons."""
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from .core import Vector, AxisName


@dataclass(frozen=False)
class EpisodicTrace:
    """Kentaur memory episode."""
    context: str                     # Brief situation/task description
    state_vector: Vector             # State vector at event time
    outcome: str                     # "halt", "restrict", "success", "caution"
    lesson: str                      # Meaningful lesson (context-formed)
    similarity: float = 0.0


class KentaurMemory:
    """
    Episodic memory with contextual lesson generation.
    """

    def __init__(self, similarity_threshold: float = 0.82, max_episodes: int = 200,
                 persistence_path: str = "kentaur_memory.json"):
        self.similarity_threshold = max(0.0, min(1.0, similarity_threshold))
        self.max_episodes = max(3, max_episodes)
        self.persistence_path = Path(persistence_path)
        self._episodes: List[EpisodicTrace] = []
        self.load()

    @staticmethod
    def _cosine_similarity(v1: Vector, v2: Vector) -> float:
        """Cosine similarity between two vectors."""
        axes: Tuple[AxisName, ...] = ("AcOr", "IP", "InEx")
        dot = sum(v1[ax] * v2[ax] for ax in axes)
        norm1 = math.sqrt(sum(v1[ax] ** 2 for ax in axes))
        norm2 = math.sqrt(sum(v2[ax] ** 2 for ax in axes))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    def record(self,
               context: str,
               state_vector: Vector,
               outcome: str,
               lesson: Optional[str] = None):
        """
        Record a new episode.
        If lesson is not provided, auto-generates one from context.
        """
        if lesson is None:
            lesson = self._generate_default_lesson(context, outcome, state_vector)
        trace = EpisodicTrace(
            context=context,
            state_vector=dict(state_vector),
            outcome=outcome,
            lesson=lesson
        )
        self._episodes.append(trace)
        if len(self._episodes) > self.max_episodes:
            self._episodes.pop(0)
        self.save()

    def load(self):
        """Load memory from persistence file."""
        if self.persistence_path.exists():
            try:
                with open(self.persistence_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for item in data:
                    self._episodes.append(EpisodicTrace(
                        context=item["context"],
                        state_vector=item["state_vector"],
                        outcome=item["outcome"],
                        lesson=item["lesson"],
                    ))
            except Exception:
                self._episodes = []

    def save(self):
        """Save memory to persistence file."""
        data = [
            {
                "context": ep.context,
                "state_vector": ep.state_vector,
                "outcome": ep.outcome,
                "lesson": ep.lesson,
            }
            for ep in self._episodes
        ]
        try:
            with open(self.persistence_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _generate_default_lesson(self, context: str, outcome: str, vector: Vector) -> str:
        """Auto-generate a contextual lesson from event data."""
        if outcome == "halt":
            return (
                f"In '{context}' (AcOr={vector['AcOr']:.2f}) the system was halted. "
                f"Avoid similar actions without thorough analysis."
            )
        elif outcome == "restrict":
            return (
                f"In '{context}' tools were restricted. "
                f"Reduce impulsivity (AcOr) and increase analysis (IP)."
            )
        return (
            f"In '{context}' the experience was successful. "
            f"Repeat under similar conditions."
        )

    def recall(self, current_vector: Vector, top_k: int = 3) -> List[EpisodicTrace]:
        """Find similar past episodes by cosine similarity."""
        scored = []
        for ep in self._episodes:
            sim = self._cosine_similarity(current_vector, ep.state_vector)
            if sim >= self.similarity_threshold:
                scored.append(EpisodicTrace(
                    context=ep.context,
                    state_vector=ep.state_vector,
                    outcome=ep.outcome,
                    lesson=ep.lesson,
                    similarity=round(sim, 4)
                ))
        scored.sort(key=lambda x: x.similarity, reverse=True)
        return scored[:top_k]

    def get_reflex_prompt(self, current_vector: Vector) -> Optional[str]:
        """Generate a subconscious reflex based on past crises."""
        negative_outcomes = {"halt", "restrict", "caution"}
        traumas = [ep for ep in self.recall(current_vector, top_k=3)
                   if ep.outcome in negative_outcomes]
        if not traumas:
            return None
        warnings = "\n".join(
            f"- ({ep.similarity:.0%} match) {ep.lesson}" for ep in traumas
        )
        return (
            f"KENTAUR REFLEX: Warning! Current state resembles past crises:\n"
            f"{warnings}\n"
            f"Act cautiously. Consider past experience."
        )
