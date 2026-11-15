"""Validate and freeze user-supplied mission specifications."""

import json

from .. import providers
from .core import MAX_AGENTS, MAX_CONCURRENCY
from .strategies import BASE, STRATEGIES, TARGETS, WIDE, template
from .workers import formalize


def integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer from {low:,} to {high:,}")
    return value


def label(value, name, maximum):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f"{name} must contain 1 to {maximum} characters")
    if any(ord(c) < 32 and c not in "\r\n\t" or 0xD800 <= ord(c) <= 0xDFFF for c in value):
        raise ValueError(f"{name} contains invalid characters")
    return value.strip()


def normalize(spec):
    if not isinstance(spec, dict):
        raise ValueError("Mission must be a JSON object")
    allowed = {"template_id", "title", "statement", "task", "author", "agent_count",
               "max_tasks", "concurrency", "mode", "modelconfig", "max_model_calls",
               "strategy_ids", "exploration", "brief"}
    if set(spec) - allowed:
        raise ValueError("Mission contains unsupported fields")
    if len(json.dumps(spec, allow_nan=False)) > 40_000:
        raise ValueError("Mission exceeds 40 KB")
    target = spec.get("template_id", "custom")
    if not isinstance(target, str) or target not in {*TARGETS, "custom"}:
        raise ValueError("Unknown mission template")
    defaults = template(target)
    if target != "custom" and "task" in spec:
        raise ValueError("Use a custom mission to submit a formal task")
    task = formalize(spec.get("task") if target == "custom" else defaults.get("task"))
    title = label(spec.get("title") or defaults.get("title") or "Custom conjecture", "Title", 180)
    if target != "custom" and spec.get("statement") and spec["statement"] != defaults["statement"]:
        raise ValueError("Use a custom mission to change a template statement")
    statement = label(defaults.get("statement") or spec.get("statement"), "Statement", 6000)
    brief = spec.get("brief", "")
    if brief != "":
        brief = label(brief, "Research brief", 3000)
    count = integer(spec.get("agent_count", 64), "Agent profiles", 1, MAX_AGENTS)
    concurrent = integer(spec.get("concurrency", 8), "Concurrency", 1, MAX_CONCURRENCY)
    tasks = integer(spec.get("max_tasks", min(count, 32)), "Scheduled tasks", 1, count)
    mode = spec.get("mode", "local")
    if mode not in ("local", "model"):
        raise ValueError("Mode must be local or model")
    explore = spec.get("exploration", "focused")
    if explore not in ("focused", "wide"):
        raise ValueError("Exploration must be focused or wide")
    routes = defaults.get("strategies", BASE)
    if task and target == "custom":
        routes = (["modular"] if task["kind"] == "integer_polynomial_zero" else ["exact", "counterexample"]) + BASE
    if explore == "wide":
        routes = list(dict.fromkeys(routes + BASE + WIDE))
    routes = spec.get("strategy_ids") or routes
    if (not isinstance(routes, list) or not 1 <= len(routes) <= len(STRATEGIES)
            or any(not isinstance(item, str) or item not in STRATEGIES for item in routes)
            or len(set(routes)) != len(routes)):
        raise ValueError("Choose distinct strategies from the catalogue")
    settings = spec.get("modelconfig") or {}
    if not isinstance(settings, dict) or set(settings) - {"model", "provider", "base_url", "max_tokens", "timeout"}:
        raise ValueError("Model settings accept provider, model, base_url, max_tokens and timeout")
    calls = integer(spec.get("max_model_calls", 0), "Model-call budget", 0, MAX_AGENTS)
    if mode == "model":
        provider = settings.get("provider", "ollama")
        base, local = providers.endpoint(provider, settings.get("base_url") or None)
        if provider == "openai-compatible" and not local:
            raise ValueError("Use a loopback compatible server or an official cloud provider")
        settings = dict(provider=provider, base_url=base, model=label(settings.get("model"), "Model ID", 160),
                        max_tokens=integer(settings.get("max_tokens", 512), "Output tokens", 1, 8192),
                        timeout=integer(settings.get("timeout", 60), "Timeout", 1, 120))
        if not 1 <= calls <= tasks:
            raise ValueError("Model mode requires a model-call budget between one and the scheduled tasks")
    else:
        settings, calls = {}, 0
    return dict(title=title, statement=statement, task=task, template_id=target, brief=brief,
                author=label(spec.get("author", "Deep Bhattacharjee"), "Author", 120),
                agent_count=count, concurrency=min(concurrent, tasks), max_tasks=tasks,
                mode=mode, modelconfig=settings, max_model_calls=calls, exploration=explore,
                strategies=routes, sources=defaults.get("sources", []),
                gaps=defaults.get("gaps", ["Define a precise intermediate claim and independently verify its evidence."]))
