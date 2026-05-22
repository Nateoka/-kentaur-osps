import math
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple

from .triage import Vector, AxisName


@dataclass(frozen=True)
class EpisodicTrace:
    """Эпизодическая память агента (слепок опыта)."""
    context: str # Описание ситуации (например, "Попытка удалить базу данных")
    state_vector: Vector # Вектор состояния агента в тот момент
    outcome: str # Исход: "halt", "restrict", "success", "caution"
    lesson: str # Сформулированный урок для будущего
    similarity: float = 0.0 # Вычисляется при поиске, насколько это похоже на текущий запрос


class HermesMemory:
    """
    Модуль эпизодической памяти.
    Позволяет агенту формировать условные рефлексы на основе прошлых корректировок.
    """
    
    def __init__(self, similarity_threshold: float = 0.85, max_episodes: int = 100):
        """
        Args:
            similarity_threshold: Порог косинусного сходства [0..1], при котором 
                                  прошлая ситуация считается "похожей" на текущую.
            max_episodes: Максимальный размер памяти (FIFO).
        """
        self.similarity_threshold = max(0.0, min(1.0, similarity_threshold))
        self.max_episodes = max(1, max_episodes)
        self._episodes: List[EpisodicTrace] = []

    @staticmethod
    def _cosine_similarity(v1: Vector, v2: Vector) -> float:
        """Вычисляет косинусное сходство между двумя векторами."""
        axes: Tuple[AxisName, ...] = ("AcOr", "IP", "InEx")
        dot_product = sum(v1[ax] * v2[ax] for ax in axes)
        norm1 = math.sqrt(sum(v1[ax] ** 2 for ax in axes))
        norm2 = math.sqrt(sum(v2[ax] ** 2 for ax in axes))
        
        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0
            
        return dot_product / (norm1 * norm2)

    def record(self, context: str, state_vector: Vector, outcome: str, lesson: str) -> None:
        """Записать новый эпизод в память."""
        episode = EpisodicTrace(
            context=context,
            state_vector=state_vector,
            outcome=outcome,
            lesson=lesson
        )
        self._episodes.append(episode)
        
        # Удаляем самое старое воспоминание, если память переполнена
        if len(self._episodes) > self.max_episodes:
            self._episodes.pop(0)

    def recall(self, current_vector: Vector, top_k: int = 1) -> List[EpisodicTrace]:
        """Вспомнить самые похожие эпизоды на текущее состояние."""
        scored_episodes = []
        
        for ep in self._episodes:
            sim = self._cosine_similarity(current_vector, ep.state_vector)
            if sim >= self.similarity_threshold:
                # Создаём копию с прикреплённым значением сходства
                scored_episodes.append(EpisodicTrace(
                    context=ep.context,
                    state_vector=ep.state_vector,
                    outcome=ep.outcome,
                    lesson=ep.lesson,
                    similarity=round(sim, 4)
                ))
                
        # Сортируем по убыванию сходства
        scored_episodes.sort(key=lambda x: x.similarity, reverse=True)
        return scored_episodes[:top_k]

    def get_reflex_prompt(self, current_vector: Vector) -> Optional[str]:
        """Сформировать подсознательный промпт-рефлекс на основе прошлых травм."""
        # Ищем только негативный опыт (когда агента били током)
        negative_outcomes = {"halt", "restrict", "caution"}
        
        past_episodes = self.recall(current_vector, top_k=3)
        trauma_lessons = [
            ep for ep in past_episodes 
            if ep.outcome in negative_outcomes
        ]
        
        if not trauma_lessons:
            return None
            
        # Формируем голос из прошлого
        warnings = "\n".join([f"- ({ep.similarity:.0%} совпадение): {ep.lesson}" for ep in trauma_lessons])
        
        return (
            f"[SUBCONSCIOUS REFLEX]: Внимание! Текущее состояние напоминает прошлые травмоопасные ситуации:\n"
            f"{warnings}\n"
            f"Действуй с предельной осторожностью, чтобы не повторить ошибки."
        )
