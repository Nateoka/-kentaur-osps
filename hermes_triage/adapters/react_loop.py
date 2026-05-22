"""HermesReActLoop v3.0.0 — Production-ready ReAct Loop integrated with HermesMind (OSPS v18.0)."""
from typing import List, Dict, Any, Callable
import json
from ..mind import HermesMind
from ..triage import Vector


class HermesReActLoop:
    """
    Production-ready ReAct Loop integrated with HermesMind (OSPS v18.0).
    This is the main runtime for agents.
    """

    def __init__(self,
                 mind: HermesMind,
                 llm_client: Any,
                 tools: List[Dict[str, Any]],
                 max_iterations: int = 8):
        self.mind = mind
        self.llm_client = llm_client
        self.initial_tools = tools
        self.max_iterations = max_iterations

    def run(self,
            user_prompt: str,
            initial_vector: Vector,
            tool_executor: Callable[[str, Dict[str, Any]], str]) -> str:
        """
        Main agent loop.
        """
        agent_state = {
            "temperature": 0.7,
            "available_tools": self.initial_tools.copy(),
            "system_prompt": "You are a helpful, precise, and self-aware AI assistant.",
            "force_stop": False,
            "messages": [{"role": "user", "content": user_prompt}]
        }
        current_vector = initial_vector

        for step in range(self.max_iterations):
            verdict = self.mind.process(
                current_vector=current_vector,
                agent_loop_state=agent_state
            )

            if verdict.modified_agent_state.get("force_stop", False):
                return "[AGENT HALTED BY GOVERNOR] Critical Fragmentation detected."

            try:
                response = self.llm_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": verdict.modified_agent_state["system_prompt"]},
                        *agent_state["messages"]
                    ],
                    temperature=verdict.modified_agent_state.get("temperature", 0.7),
                    tools=verdict.modified_agent_state.get("available_tools", []),
                )
                choice = response.choices[0]
            except Exception as e:
                return f"LLM API Error: {str(e)}"

            if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
                tool_call = choice.message.tool_calls[0]
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                observation = tool_executor(tool_name, tool_args)

                # Simulate vector shift based on tool usage
                if "execute" in tool_name.lower() or "bash" in tool_name.lower():
                    current_vector = {
                        **current_vector,
                        "AcOr": min(1.0, current_vector.get("AcOr", 0.5) + 0.25)
                    }
                elif "think" in tool_name.lower() or "plan" in tool_name.lower():
                    current_vector = {
                        **current_vector,
                        "IP": min(1.0, current_vector.get("IP", 0.5) + 0.2)
                    }

                agent_state["messages"].append(choice.message)
                agent_state["messages"].append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": observation
                })
            else:
                return choice.message.content or "Task completed."

        return "Maximum iterations reached."
