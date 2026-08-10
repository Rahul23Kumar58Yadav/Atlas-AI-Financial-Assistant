"""
Thin wrapper around the LLM provider. Agents/onboarding/briefing never
call Groq, Gemini, or Anthropic directly - they only call this file's
complete()/complete_with_tool_loop(), which is exactly what makes this
swap possible without touching any other file in the project.

Defaults to Groq because it has a genuinely free tier with the simplest
possible signup (no cloud console, no IAM). Set AI_PROVIDER=gemini or
AI_PROVIDER=anthropic in .env to switch providers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.config.settings import get_settings

settings = get_settings()


@dataclass
class LLMResponse:
    text: str
    tool_calls: list[dict[str, Any]]
    raw: Any


class LLMClient:
    """
    Provider-agnostic facade. `model` param is accepted for backward
    compatibility with callers that used to pass an Anthropic model name;
    it's ignored unless the active provider is Anthropic.
    """

    def __init__(self, model: str | None = None):
        self._anthropic_model = model or settings.anthropic_model
        self.provider = settings.ai_provider

    async def complete(
        self,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        if self.provider == "groq":
            return await self._complete_groq(system, messages, tools, max_tokens)
        if self.provider == "gemini":
            return await self._complete_gemini(system, messages, tools, max_tokens)
        return await self._complete_anthropic(system, messages, tools, max_tokens)

    async def complete_with_tool_loop(
        self,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        tool_executor,
        max_tokens: int = 1024,
        max_iterations: int = 5,
    ) -> str:
        if self.provider == "groq":
            return await self._tool_loop_groq(system, messages, tools, tool_executor, max_tokens, max_iterations)
        if self.provider == "gemini":
            return await self._tool_loop_gemini(system, messages, tools, tool_executor, max_tokens, max_iterations)
        return await self._tool_loop_anthropic(system, messages, tools, tool_executor, max_tokens, max_iterations)

    # ------------------------------------------------------------------
    # Groq implementation (OpenAI-compatible API - simplest signup, no
    # cloud console/IAM required, just an email+password account)
    # ------------------------------------------------------------------

    def _groq_client(self):
        from openai import AsyncOpenAI

        return AsyncOpenAI(api_key=settings.groq_api_key, base_url="https://api.groq.com/openai/v1")

    def _groq_tools(self, tools: list[dict[str, Any]] | None):
        if not tools:
            return None
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("input_schema"),
                },
            }
            for tool in tools
        ]

    def _groq_messages(self, system: str, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Converts our Anthropic-shaped message list into OpenAI/Groq's
        chat format. Tool results are folded into plain user-role text
        rather than a strict "tool" role message — OpenAI's API requires
        a tool message to reference a preceding assistant message's
        tool_calls array by id, which our internal shape doesn't
        reconstruct across turns. Plain text is less "protocol correct"
        but avoids a real risk of the API rejecting the request outright.
        """
        converted = [{"role": "system", "content": system}]

        for msg in messages:
            content = msg["content"]

            if isinstance(content, str):
                converted.append({"role": msg["role"], "content": content})
            elif isinstance(content, list):
                text_parts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        text_parts.append(str(block.get("content", "")))
                    elif isinstance(block, dict) and "text" in block:
                        text_parts.append(block["text"])
                converted.append({"role": "user", "content": "\n".join(text_parts)})
        return converted

    async def _complete_groq(
        self, system: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None, max_tokens: int
    ) -> LLMResponse:
        client = self._groq_client()
        response = await client.chat.completions.create(
            model=settings.groq_model,
            messages=self._groq_messages(system, messages),
            tools=self._groq_tools(tools),
            max_tokens=max_tokens,
        )

        message = response.choices[0].message
        text = message.content or ""
        tool_calls = []
        if message.tool_calls:
            import json

            for call in message.tool_calls:
                tool_calls.append(
                    {
                        "id": call.id,
                        "name": call.function.name,
                        "input": json.loads(call.function.arguments) if call.function.arguments else {},
                    }
                )

        return LLMResponse(text=text, tool_calls=tool_calls, raw=response)

    async def _tool_loop_groq(
        self, system, messages, tools, tool_executor, max_tokens, max_iterations
    ) -> str:
        conversation = list(messages)

        for _ in range(max_iterations):
            result = await self._complete_groq(system, conversation, tools, max_tokens)

            if not result.tool_calls:
                return result.text

            conversation.append({"role": "assistant", "content": result.text or "(calling tool)"})

            for call in result.tool_calls:
                output = await tool_executor(call["name"], call["input"])
                conversation.append(
                    {"role": "user", "content": [{"type": "tool_result", "tool_use_id": call["id"], "content": str(output)}]}
                )

        return "I wasn't able to finish that research in time - want me to narrow the scope?"

    # ------------------------------------------------------------------
    # Gemini implementation (google-genai SDK)
    # ------------------------------------------------------------------

    def _gemini_client(self):
        from google import genai

        return genai.Client(api_key=settings.gemini_api_key)

    def _gemini_tools(self, tools: list[dict[str, Any]] | None):
        if not tools:
            return None
        from google.genai import types

        declarations = [
            types.FunctionDeclaration(
                name=tool["name"],
                description=tool.get("description", ""),
                parameters=tool.get("input_schema"),
            )
            for tool in tools
        ]
        return [types.Tool(function_declarations=declarations)]

    def _gemini_contents(self, messages: list[dict[str, Any]]):
        from google.genai import types

        contents = []
        for msg in messages:
            role = "model" if msg["role"] == "assistant" else "user"
            content = msg["content"]

            if isinstance(content, str):
                parts = [types.Part.from_text(text=content)]
            elif isinstance(content, list):
                parts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        parts.append(types.Part.from_text(text=str(block.get("content", ""))))
                    elif isinstance(block, dict) and "text" in block:
                        parts.append(types.Part.from_text(text=block["text"]))
                    else:
                        parts.append(types.Part.from_text(text=str(block)))
            else:
                parts = [types.Part.from_text(text=str(content))]

            contents.append(types.Content(role=role, parts=parts))
        return contents

    async def _complete_gemini(
        self, system: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None, max_tokens: int
    ) -> LLMResponse:
        from google.genai import types

        client = self._gemini_client()
        config = types.GenerateContentConfig(
            system_instruction=system,
            tools=self._gemini_tools(tools),
            max_output_tokens=max_tokens,
        )

        response = await client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=self._gemini_contents(messages),
            config=config,
        )

        text_parts = []
        tool_calls = []
        candidate_parts = response.candidates[0].content.parts if response.candidates else []
        for part in candidate_parts:
            if getattr(part, "text", None):
                text_parts.append(part.text)
            if getattr(part, "function_call", None):
                tool_calls.append(
                    {
                        "id": part.function_call.name,
                        "name": part.function_call.name,
                        "input": dict(part.function_call.args) if part.function_call.args else {},
                    }
                )

        return LLMResponse(text="\n".join(text_parts), tool_calls=tool_calls, raw=response)

    async def _tool_loop_gemini(
        self, system, messages, tools, tool_executor, max_tokens, max_iterations
    ) -> str:
        conversation = list(messages)

        for _ in range(max_iterations):
            result = await self._complete_gemini(system, conversation, tools, max_tokens)

            if not result.tool_calls:
                return result.text

            conversation.append({"role": "assistant", "content": result.text or "(calling tool)"})

            tool_outputs = []
            for call in result.tool_calls:
                output = await tool_executor(call["name"], call["input"])
                tool_outputs.append(f"Result of {call['name']}: {output}")
            conversation.append({"role": "user", "content": "\n".join(tool_outputs)})

        return "I wasn't able to finish that research in time - want me to narrow the scope?"

    # ------------------------------------------------------------------
    # Anthropic implementation (unchanged behavior, kept as a fallback)
    # ------------------------------------------------------------------

    async def _complete_anthropic(
        self, system: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None, max_tokens: int
    ) -> LLMResponse:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        response = await client.messages.create(
            model=self._anthropic_model,
            system=system,
            messages=messages,
            tools=tools or [],
            max_tokens=max_tokens,
        )

        text_parts = [block.text for block in response.content if block.type == "text"]
        tool_calls = [
            {"id": block.id, "name": block.name, "input": block.input}
            for block in response.content
            if block.type == "tool_use"
        ]
        return LLMResponse(text="\n".join(text_parts), tool_calls=tool_calls, raw=response)

    async def _tool_loop_anthropic(
        self, system, messages, tools, tool_executor, max_tokens, max_iterations
    ) -> str:
        conversation = list(messages)

        for _ in range(max_iterations):
            result = await self._complete_anthropic(system, conversation, tools, max_tokens)

            if not result.tool_calls:
                return result.text

            conversation.append({"role": "assistant", "content": result.raw.content})

            tool_results = []
            for call in result.tool_calls:
                output = await tool_executor(call["name"], call["input"])
                tool_results.append({"type": "tool_result", "tool_use_id": call["id"], "content": str(output)})
            conversation.append({"role": "user", "content": tool_results})

        return "I wasn't able to finish that research in time - want me to narrow the scope?"