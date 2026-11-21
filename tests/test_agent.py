"""Pruebas de las conexiones del agente.

TestModel es un modelo simulado que llama a todas las herramientas registradas y devuelve
una respuesta ficticia sin llamar a un LLM real. Permite comprobar «si las herramientas
están registradas, se llaman y devuelven resultados al modelo» sin clave API ni consumo de cuota.
"""

import json

from pydantic_ai import DeferredToolRequests
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel

from app.agent import agent

BASE_TOOLS = {"search_materials"}


def _parts(result, kind):
    return [p for m in result.all_messages() for p in m.parts if isinstance(p, kind)]


def test_base_tools_are_registered_and_called(monkeypatch):
    monkeypatch.setattr("app.retrieval.search", lambda *args, **kwargs: [])
    model = TestModel()
    with agent.override(model=model):
        result = agent.run_sync("¿Qué es LoRA?")

    offered = {t.name for t in model.last_model_request_parameters.function_tools}
    assert BASE_TOOLS <= offered  # Comprueba la inclusión para admitir herramientas añadidas en el ejercicio

    called = {p.tool_name for p in _parts(result, ToolCallPart)}
    assert BASE_TOOLS <= called
    # Las herramientas que requieren aprobación (requires_approval=True) esperan sin ejecutarse y no tienen valor de retorno
    waiting = len(result.output.approvals) if isinstance(result.output, DeferredToolRequests) else 0
    assert len(_parts(result, ToolReturnPart)) + waiting == len(_parts(result, ToolCallPart))
    assert result.output


def test_material_result_reaches_the_model(monkeypatch):
    hit = {"page_id": "lec02-main-p052", "lecture": 2, "page": 52, "content": "Los pesos originales se mantienen fijos"}
    monkeypatch.setattr("app.retrieval.search", lambda *args, **kwargs: [hit])
    model = TestModel(call_tools=["search_materials"])
    with agent.override(model=model):
        result = agent.run_sync("¿Qué es RAG?")
    returns = _parts(result, ToolReturnPart)
    assert returns and returns[0].tool_name == "search_materials"
    assert json.loads(returns[0].content)["results"] == [hit]
