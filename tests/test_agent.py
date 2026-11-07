"""Pruebas de las conexiones del agente.

TestModel es un modelo simulado que llama a todas las herramientas registradas y devuelve
una respuesta ficticia sin llamar a un LLM real. Permite comprobar «si las herramientas
están registradas, se llaman y devuelven resultados al modelo» sin clave API ni consumo de cuota.
"""

from pydantic_ai import DeferredToolRequests
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel

from app.agent import agent

BASE_TOOLS = {"search_glossary", "get_lecture_summary"}


def _parts(result, kind):
    return [p for m in result.all_messages() for p in m.parts if isinstance(p, kind)]


def test_base_tools_are_registered_and_called():
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


def test_glossary_result_reaches_the_model():
    model = TestModel(call_tools=["search_glossary"])
    with agent.override(model=model):
        result = agent.run_sync("¿Qué es RAG?")
    returns = _parts(result, ToolReturnPart)
    assert returns and returns[0].tool_name == "search_glossary"
