from unittest.mock import patch

from pydantic_ai.messages import ToolCallPart

from app.agent import process_approvals


def test_rejected_tool_is_blocked_even_if_arguments_change():
    """Una herramienta rechazada no debe insistir con otros argumentos."""

    first_call = ToolCallPart(
        tool_name="save_learning_log",
        args={
            "topic": "HITL",
            "notes": "Aprendí sobre aprobación humana",
        },
        tool_call_id="call-001",
    )

    second_call = ToolCallPart(
        tool_name="save_learning_log",
        args={
            "topic": "Lecture 03",
            "notes": "Aprendí cómo funciona la aprobación humana",
        },
        tool_call_id="call-002",
    )

    rejected_tools = set()

    with patch("builtins.input", return_value="n") as mock_input:
        first_decisions = process_approvals(
            type("Requests", (), {"approvals": [first_call]})(),
            rejected_tools,
        )

        second_decisions = process_approvals(
            type("Requests", (), {"approvals": [second_call]})(),
            rejected_tools,
        )

    assert first_decisions == {"call-001": False}
    assert second_decisions == {"call-002": False}

    # Solamente se solicita autorización en el primer intento.
    assert mock_input.call_count == 1

    # La herramienta permanece bloqueada.
    assert rejected_tools == {"save_learning_log"}