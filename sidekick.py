"""The Sidekick: a create_agent worker wrapped in a homemade evaluator loop.

The worker is a single create_agent (Layer 3). Around it we run our own loop that checks
the worker's answer against the user's success criteria, and either accepts it, sends it
back for another attempt, or returns to the user with a question. Middleware gives the
worker a plan it shares with the UI, guardrails for PII and runaway costs, and a pause
for human approval before sensitive actions.
"""

import os
import time
import uuid
from datetime import datetime

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain.agents import create_agent
from langchain.agents.middleware import (
    AgentMiddleware,
    HumanInTheLoopMiddleware,
    PIIMiddleware,
    TodoListMiddleware,
)
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.errors import GraphBubbleUp
from langgraph.types import Command

from model_config import build_models, build_structured_evaluator
from sidekick_tools import get_all_tools

load_dotenv(override=True)

HERE = os.path.dirname(os.path.abspath(__file__))
SANDBOX = os.path.join(HERE, "sandbox")
def safe_error_detail(error: Exception) -> str:
    """Keep a compact diagnostic in the terminal without leaking configured keys."""
    detail = str(error)
    for name in ("GEMINI_API_KEY", "GROQ_API_KEY", "OPENROUTER_API_KEY", "SERPER_API_KEY"):
        if secret := os.getenv(name):
            detail = detail.replace(secret, "[redacted]")
    return " ".join(detail.split())[:300]


def is_rate_limit_error(error: Exception) -> bool:
    """Recognize rate-limit responses without coupling Sidekick to one SDK."""
    detail = str(error).lower()
    error_name = type(error).__name__.lower()
    return (
        getattr(error, "status_code", None) == 429
        or getattr(error, "code", None) == 429
        or "ratelimit" in error_name
        or "rate limit" in detail
        or "resource_exhausted" in detail
        or "quota" in detail
    )


def cross_provider_messages(messages: list) -> list:
    """Remove provider-native reasoning metadata before a fallback model sees it.

    Tool-call IDs and text remain intact, so the agent continues the same graph state.
    """
    normalized = []
    for message in messages:
        if not isinstance(message, AIMessage):
            normalized.append(message)
            continue
        additional = {
            key: value
            for key, value in message.additional_kwargs.items()
            if key not in {"raw_tool_call_parts", "reasoning", "reasoning_content", "thought"}
        }
        content = message.content
        if isinstance(content, list):
            content = [
                block
                for block in content
                if not (isinstance(block, dict) and block.get("type") in {"reasoning", "thinking"})
            ]
        normalized.append(
            message.model_copy(
                update={"content": content, "additional_kwargs": additional, "response_metadata": {}}
            )
        )
    return normalized


def initial_plan(language: str) -> list[dict[str, str]]:
    """Provide a visible plan even if the model declines the optional todo tool."""
    if language == "Español":
        items = (
            "Analizar la solicitud y los criterios de éxito",
            "Investigar la información o ejecutar las acciones necesarias",
            "Sintetizar los resultados y preparar la respuesta",
            "Verificar que la respuesta cumpla los criterios",
        )
    else:
        items = (
            "Analyze the request and success criteria",
            "Research information or perform the required actions",
            "Synthesize the results and prepare the response",
            "Verify that the response meets the success criteria",
        )
    return [
        {"content": item, "status": "in_progress" if index == 0 else "pending"}
        for index, item in enumerate(items)
    ]


def complete_plan(todos: list[dict[str, str]]) -> list[dict[str, str]]:
    return [{**todo, "status": "completed"} for todo in todos]


def move_to_review(todos: list[dict[str, str]]) -> list[dict[str, str]]:
    """Show that execution ended and Sidekick is checking its result."""
    if not todos:
        return todos
    updated = [{**todo} for todo in todos]
    for todo in updated[:-1]:
        todo["status"] = "completed"
    updated[-1]["status"] = "in_progress"
    return updated


class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(description="Whether the success criteria have been met")
    user_input_needed: bool = Field(
        description="True if the assistant has a question, needs clarification, or is stuck and needs the user"
    )


WORKER_PROMPT = """You are Sidekick, a capable personal assistant who completes tasks for the user.
You have a real web browser, a sandbox filesystem, web search, Wikipedia, and the ability to send push notifications.
When you use the browser, navigate to a page and read it with a snapshot rather than clicking around unnecessarily.
Dismiss cookie banners and popups yourself by clicking in the browser. If you reach something only a human can do,
like logging in, a captcha, or two-factor authentication, use the request_human_help tool to tell the user exactly
what to do in your browser window, then carry on once they have done it.
For flight searches, use Google Flights in your browser: go straight to https://www.google.com/travel/flights?q=...
with a natural language query like "flights from New York to London leaving 14 July returning 21 July".
Keep working on the task until the success criteria are met, or until you genuinely need to ask the user a question.
If you have a question, ask it plainly. When you are finished, give your final answer clearly,
saying what you did, what you produced, and what you found."""


class TolerateToolErrors(AgentMiddleware):
    """Hand tool failures back to the model as a message so it can recover, rather than
    crashing the run. Tools that touch the outside world, like a browser, fail now and then."""

    async def awrap_tool_call(self, request, handler):
        try:
            return await handler(request)
        except Exception as error:
            return ToolMessage(
                content=f"That tool call failed: {error}. Try another approach.",
                tool_call_id=request.tool_call["id"],
            )


class StickyModelFallbackMiddleware(AgentMiddleware):
    """Keep the provider that successfully takes over for the current task.

    LangChain's built-in fallback retries one model call, then starts from the
    primary provider again on the next tool-loop step. This middleware preserves
    the successful provider for the rest of a task, so its conversation and tool
    context continue without unnecessary cross-provider conversion.
    """

    def __init__(
        self, primary: BaseChatModel, *fallbacks: BaseChatModel, provider_names: tuple[str, ...] | None = None
    ) -> None:
        super().__init__()
        models = (primary, *fallbacks)
        names = provider_names or tuple(f"provider_{index}" for index in range(len(models)))
        if len(names) != len(models):
            raise ValueError("provider_names must match the configured models")
        self.models = tuple(zip(names, models, strict=True))
        self.active_model: BaseChatModel | None = None
        self.active_provider: str | None = None
        self.rate_limited_providers: set[str] = set()

    def reset(self) -> None:
        """Start the next user task with the configured primary provider."""
        self.active_model = None
        self.active_provider = None
        self.rate_limited_providers.clear()

    async def awrap_model_call(self, request, handler):
        available = [(name, model) for name, model in self.models if name not in self.rate_limited_providers]
        candidates = (
            [(self.active_provider, self.active_model)]
            + [(name, model) for name, model in available if model is not self.active_model]
            if self.active_model is not None and self.active_provider not in self.rate_limited_providers
            else available
        )
        last_error: Exception | None = None
        for provider, model in candidates:
            try:
                model_request = request.override(model=model)
                if self.active_provider is not None and provider != self.active_provider:
                    model_request = request.override(model=model, messages=cross_provider_messages(request.messages))
                print(f"[models] trying {provider}", flush=True)
                response = await handler(model_request)
                self.active_model = model
                self.active_provider = provider
                print(f"[models] using {provider}", flush=True)
                return response
            except GraphBubbleUp:
                raise
            except Exception as error:
                last_error = error
                if is_rate_limit_error(error):
                    self.rate_limited_providers.add(provider)
                    print(f"[models] {provider} rate-limited; skipping it for this task", flush=True)
                else:
                    print(f"[models] {provider} failed ({type(error).__name__}); trying next", flush=True)
        assert last_error is not None
        raise last_error


class Sidekick:
    def __init__(self):
        self.sidekick_id = str(uuid.uuid4())
        self.memory = InMemorySaver()
        self.tools = None
        self.sessions = None
        self.worker = None
        self.evaluator = None
        self.task = ""
        self.success_criteria = ""
        self.attempts = 0
        self.paused = False
        self.pending_actions = 0
        self.todos = []
        self.language = "English"
        self.fallback_middleware = None
        self.activity = "idle"
        self.started_at: float | None = None
        self.last_error = ""

    async def setup(self):
        os.makedirs(SANDBOX, exist_ok=True)
        self.tools, self.sessions = await get_all_tools(SANDBOX)
        models = build_models()
        middleware = [
            TolerateToolErrors(),
            TodoListMiddleware(),
            PIIMiddleware("email"),
            PIIMiddleware("credit_card", apply_to_tool_results=True),
            HumanInTheLoopMiddleware(
                interrupt_on={"send_push_notification": True, "request_human_help": True}
            ),
        ]
        if models.fallbacks:
            self.fallback_middleware = StickyModelFallbackMiddleware(
                models.primary, *models.fallbacks, provider_names=models.labels
            )
            middleware.insert(1, self.fallback_middleware)
        self.worker = create_agent(
            model=models.primary,
            tools=self.tools,
            system_prompt=f"{WORKER_PROMPT}\nToday is {datetime.now():%A %d %B %Y}.",
            middleware=middleware,
            checkpointer=self.memory,
        )
        self.evaluator = build_structured_evaluator(EvaluatorOutput)
        self.providers = models.providers

    async def evaluate(
        self, message: str, success_criteria: str, last_reply: str, tools_used: list[str]
    ) -> EvaluatorOutput:
        prompt = f"""You decide whether an assistant has met the success criteria for a task.

The user's request was:
{message}

The success criteria are:
{success_criteria}

The tools the assistant called while working, in order:
{", ".join(tools_used) or "none"}

The assistant's most recent reply was:
{last_reply}

Decide whether the success criteria are met, using the tool calls as evidence of what was actually done.
Also decide whether the assistant needs more input from the user, either because it asked a question,
needs clarification, or seems stuck. Give brief, concrete feedback in {self.language}."""
        return await self.evaluator.ainvoke(prompt)

    async def run_turn(
        self, message: str, success_criteria: str, history: list, language: str = "English"
    ) -> list:
        """Run one worker turn and report an evaluator verdict without repeating the task.

        A human approval pauses this turn; resume() then continues the same graph state.
        """
        self.task = message
        if self.fallback_middleware:
            self.fallback_middleware.reset()
        self.language = language if language in {"Español", "English"} else "English"
        self.success_criteria = success_criteria or (
            "La respuesta debe ser clara, correcta y completa"
            if self.language == "Español"
            else "The answer should be clear, correct and complete"
        )
        self.attempts = 0
        self.todos = initial_plan(self.language)
        self.activity = "planning"
        self.started_at = time.monotonic()
        self.last_error = ""
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"{message}\n\nThe success criteria for this task are: {self.success_criteria}"
                        f"\nReply in {self.language} unless the user explicitly requests another language."
                    ),
                }
            ]
        }
        return await self._run_with_budget(payload, history + [{"role": "user", "content": message}])

    async def resume(self, history: list) -> list:
        """Approve the actions the worker paused on, and continue the turn."""
        payload = Command(resume={"decisions": [{"type": "approve"}] * self.pending_actions})
        self.activity = "working"
        self.started_at = time.monotonic()
        return await self._run_with_budget(payload, history)

    async def _run_with_budget(self, payload, history: list) -> list:
        """Return a recoverable response if an agent, provider, or tool fails."""
        try:
            return await self._advance(payload, history)
        except Exception as error:
            self.activity = "failed"
            self.last_error = type(error).__name__
            print(f"[sidekick] task stopped ({self.last_error}): {safe_error_detail(error)}", flush=True)
            message = (
                "No pude completar la tarea por un problema de proveedor o herramienta. "
                "Podés reintentarla; Sidekick conservará el contexto mostrado."
                if self.language == "Español"
                else "I could not complete the task because a provider or tool failed. "
                "You can retry it; Sidekick keeps the displayed context."
            )
            return history + [{"role": "assistant", "content": message}]
        finally:
            if not self.paused:
                self.started_at = None

    async def _advance(self, payload, history: list) -> list:
        config = {"configurable": {"thread_id": self.sidekick_id}}
        while True:
            result = None
            async for result in self.worker.astream(payload, config=config, stream_mode="values"):
                # TodoListMiddleware leaves this field empty until the model calls
                # write_todos. Preserve our visible plan in that common case.
                if agent_todos := result.get("todos"):
                    self.todos = agent_todos
                last_message = result.get("messages", [])[-1] if result.get("messages") else None
                tool_calls = getattr(last_message, "tool_calls", None) or []
                if tool_calls:
                    self.activity = f"tool:{tool_calls[0]['name']}"

            if "__interrupt__" in result:
                actions = result["__interrupt__"][0].value["action_requests"]
                self.paused = True
                self.activity = "awaiting_approval"
                self.pending_actions = len(actions)
                described = "\n".join(action["description"] for action in actions)
                prefix = "Esperando tu aprobación:" if self.language == "Español" else "Waiting for your approval:"
                return history + [{"role": "assistant", "content": f"{prefix}\n{described}"}]

            self.paused = False
            reply = result["messages"][-1].content
            self.activity = "reviewing"
            self.todos = move_to_review(self.todos)
            tools_used = [
                call["name"] for m in result["messages"] for call in (getattr(m, "tool_calls", None) or [])
            ]
            self.attempts += 1
            verdict = await self.evaluate(self.task, self.success_criteria, reply, tools_used)
            self.todos = complete_plan(self.todos)
            self.activity = "complete"
            return history + [
                {"role": "assistant", "content": reply},
                {"role": "assistant", "content": f"{'Evaluador' if self.language == 'Español' else 'Evaluator'}: {verdict.feedback}"},
            ]

    def cleanup(self):
        """Shut down the MCP servers; the browser window closes."""
        if self.sessions:
            self.sessions.stop()
