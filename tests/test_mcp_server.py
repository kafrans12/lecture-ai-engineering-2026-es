"""Lecture 06: pruebas de conexión entre servidor y cliente MCP (sin LLM ni clave API).

Inicia realmente el servidor glossary de app/mcp_servers.json (stdio) y usa TestModel
para comprobar «si las herramientas se exponen mediante MCP, se llaman y devuelven resultados».
"""

import json

from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel

from app.agent import MCP_CONFIG, build_mcp_agent

GLOSSARY_TOOL = "glossary_search_glossary"  # Lleva como prefijo el nombre del servidor "glossary" de la configuración


def _glossary_only_config(tmp_path):
    """Usa solo el servidor glossary de la configuración (no inicia servidores externos como fetch añadidos en el ejercicio)."""
    config = json.loads(MCP_CONFIG.read_text(encoding="utf-8"))
    assert "glossary" in config["mcpServers"], "Se necesita el servidor glossary en app/mcp_servers.json"
    path = tmp_path / "mcp_servers.json"
    path.write_text(
        json.dumps({"mcpServers": {"glossary": config["mcpServers"]["glossary"]}}), encoding="utf-8"
    )
    return path


def _parts(result, kind):
    return [p for m in result.all_messages() for p in m.parts if isinstance(p, kind)]


def test_glossary_server_exposes_search_tool(tmp_path):
    model = TestModel(call_tools=[])
    build_mcp_agent(_glossary_only_config(tmp_path)).run_sync("Lista de herramientas", model=model)

    offered = {t.name for t in model.last_model_request_parameters.function_tools}
    assert GLOSSARY_TOOL in offered  # Comprueba la inclusión para admitir herramientas añadidas en el ejercicio


def test_glossary_result_comes_back_through_mcp(tmp_path):
    model = TestModel(call_tools=[GLOSSARY_TOOL])
    result = build_mcp_agent(_glossary_only_config(tmp_path)).run_sync("¿Qué es LoRA?", model=model)

    assert [p.tool_name for p in _parts(result, ToolCallPart)] == [GLOSSARY_TOOL]
    returns = _parts(result, ToolReturnPart)
    assert returns and returns[0].tool_name == GLOSSARY_TOOL
    assert str(returns[0].content).strip()  # Se devuelve el resultado de búsqueda (o «No se ha encontrado»)
    assert result.output
