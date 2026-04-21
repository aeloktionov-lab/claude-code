"""Base agent class with streaming, tool use, and prompt caching."""
import json
from abc import ABC, abstractmethod
from typing import Any

import anthropic

import config
from utils.display import console, print_info


class BaseAgent(ABC):
    """
    Base class for all CROID agents.

    Each subclass defines:
    - name: display name shown in the UI
    - system_prompt: large stable prompt cached via prompt caching
    - tools: list of tool definitions for structured output capture
    - run(context): execute the agent and return structured results
    """

    def __init__(self, client: anthropic.Anthropic) -> None:
        self.client = client

    # ── Abstract interface ────────────────────────────────────────────────

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable agent name in Russian."""

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Large stable system prompt (>1024 tokens) — cached on first call."""

    @property
    @abstractmethod
    def tools(self) -> list[dict]:
        """Anthropic tool definitions for structured output capture."""

    @abstractmethod
    def run(self, context: dict) -> dict:
        """Execute agent logic and return structured results."""

    # ── Internal helpers ──────────────────────────────────────────────────

    def _cached_system(self) -> list[dict]:
        """Wrap system prompt with ephemeral cache_control for prompt caching."""
        return [
            {
                "type": "text",
                "text": self.system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ]

    def _run_loop(self, messages: list[dict]) -> tuple[str, dict]:
        """
        Stream the agent response, handle tool calls, and collect all tool inputs.

        Returns:
            (final_text, tool_calls_by_name)
            where tool_calls_by_name maps tool name -> list of input dicts
        """
        tool_store: dict[str, list[dict]] = {}
        final_text = ""

        while True:
            # Stream the response, showing thinking as it arrives
            with self.client.messages.stream(
                model=config.MODEL,
                max_tokens=config.MAX_TOKENS,
                system=self._cached_system(),
                tools=self.tools,
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    print(text, end="", flush=True)
                response = stream.get_final_message()

            messages.append({"role": "assistant", "content": response.content})

            # Extract final text if present
            for block in response.content:
                if hasattr(block, "text"):
                    final_text = block.text

            if response.stop_reason == "end_turn":
                break

            if response.stop_reason != "tool_use":
                break

            # Collect tool inputs and reply with acknowledgements
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_store.setdefault(block.name, []).append(block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps({"ok": True}),
                    })

            if not tool_results:
                break

            messages.append({"role": "user", "content": tool_results})
            print_info(f"  [{self.name}] инструменты вызваны: {[b.name for b in response.content if b.type == 'tool_use']}")

        return final_text, tool_store

    def _build_user_message(self, context: dict) -> str:
        """Serialize context dict into a formatted user message."""
        lines = []
        for key, value in context.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{key}:\n{json.dumps(value, ensure_ascii=False, indent=2)}")
            else:
                lines.append(f"{key}: {value}")
        return "\n\n".join(lines)
