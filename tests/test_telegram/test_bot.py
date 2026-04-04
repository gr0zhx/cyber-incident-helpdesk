"""Unit tests for Telegram bot handlers."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.telegram.bot import (
    start_handler,
    help_handler,
    report_start_handler,
    report_receive_handler,
    cancel_handler,
    status_handler,
    unknown_handler,
    build_bot_application,
    WAITING_REPORT,
)
from telegram.ext import ConversationHandler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_update(text: str = "", username: str = "testuser", user_id: int = 12345) -> MagicMock:
    """Buat mock Update PTB."""
    update = MagicMock()
    update.effective_user.id = user_id
    update.effective_user.full_name = "Test User"
    update.effective_user.username = username
    update.message.text = text
    update.message.reply_text = AsyncMock()
    update.message.delete = AsyncMock()
    return update


def _make_context(bot_data: dict | None = None) -> MagicMock:
    context = MagicMock()
    context.bot_data = bot_data or {}
    context.bot.send_message = AsyncMock()
    context.args = []
    return context


def _make_pipeline_result(
    intent: str = "report_incident",
    incident_type: str = "Phishing",
    severity: str = "Tinggi",
    ticket_id: str = "TICKET-2026-0001",
    requires_clarification: bool = False,
    clarification_message: str = "",
) -> dict:
    return {
        "intent": intent,
        "incident_type": incident_type,
        "severity": severity,
        "confidence_score": 0.92,
        "ticket_id": ticket_id,
        "ticket_status": "PENDING_REVIEW",
        "escalation_level": "Mendesak",
        "mitigation_recommendation": "1. Jangan klik link. 2. Laporkan ke IT.",
        "requires_clarification": requires_clarification,
        "clarification_message": clarification_message,
        "reporter_name": "Test User",
        "sanitized_input": "Email phishing dari CEO palsu.",
        "raw_input": "Email phishing dari CEO palsu.",
        "timestamp_received": "2026-04-04T10:00:00+00:00",
        "notification_sent": True,
        "citations": [],
        "agent_trace": [],
        "processing_errors": [],
    }


# ---------------------------------------------------------------------------
# /start handler
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_start_handler_replies():
    update = _make_update()
    context = _make_context()
    await start_handler(update, context)
    update.message.reply_text.assert_called_once()
    call_text = update.message.reply_text.call_args[0][0]
    assert "Helpdesk" in call_text
    assert "/report" in call_text


# ---------------------------------------------------------------------------
# /help handler
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_help_handler_replies():
    update = _make_update()
    context = _make_context()
    await help_handler(update, context)
    update.message.reply_text.assert_called_once()
    call_text = update.message.reply_text.call_args[0][0]
    assert "/report" in call_text
    assert "/status" in call_text


# ---------------------------------------------------------------------------
# /report flow
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_report_start_returns_waiting_state():
    update = _make_update()
    context = _make_context()
    result = await report_start_handler(update, context)
    assert result == WAITING_REPORT
    update.message.reply_text.assert_called_once()


@pytest.mark.asyncio
async def test_report_receive_no_pipeline_replies_error():
    """Jika pipeline tidak tersedia, bot harus membalas dengan pesan error."""
    update = _make_update("Email phishing dari CEO.")
    context = _make_context(bot_data={})  # tidak ada graph/orchestrator
    result = await report_receive_handler(update, context)
    assert result == ConversationHandler.END
    update.message.reply_text.assert_called()
    call_text = update.message.reply_text.call_args[0][0]
    assert "tidak tersedia" in call_text.lower() or "coba" in call_text.lower()


@pytest.mark.asyncio
async def test_report_receive_full_pipeline_success():
    """Alur normal: graph.ainvoke berhasil → kirim konfirmasi ke pelapor."""
    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(return_value=_make_pipeline_result())

    mock_orchestrator = MagicMock()
    mock_orchestrator.initialize_state = MagicMock(return_value={"raw_input": "test"})

    update = _make_update("Saya klik link phishing.")
    context = _make_context(bot_data={
        "helpdesk_graph": mock_graph,
        "orchestrator": mock_orchestrator,
    })

    result = await report_receive_handler(update, context)
    assert result == ConversationHandler.END
    mock_graph.ainvoke.assert_called_once()
    # Pelapor harus mendapat balasan
    update.message.reply_text.assert_called()


@pytest.mark.asyncio
async def test_report_receive_needs_clarification():
    """Jika pipeline minta klarifikasi, kirim pesan klarifikasi ke pelapor."""
    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(return_value=_make_pipeline_result(
        requires_clarification=True,
        clarification_message="Mohon jelaskan lebih detail.",
    ))
    mock_orchestrator = MagicMock()
    mock_orchestrator.initialize_state = MagicMock(return_value={})

    update = _make_update("Ada yang aneh.")
    context = _make_context(bot_data={
        "helpdesk_graph": mock_graph,
        "orchestrator": mock_orchestrator,
    })

    result = await report_receive_handler(update, context)
    assert result == ConversationHandler.END
    call_text = update.message.reply_text.call_args[0][0]
    assert "Mohon jelaskan" in call_text


@pytest.mark.asyncio
async def test_report_receive_pipeline_exception_handled():
    """Jika pipeline throw exception, bot tidak crash dan membalas error."""
    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(side_effect=RuntimeError("LLM timeout"))
    mock_orchestrator = MagicMock()
    mock_orchestrator.initialize_state = MagicMock(return_value={})

    update = _make_update("Laporan insiden.")
    context = _make_context(bot_data={
        "helpdesk_graph": mock_graph,
        "orchestrator": mock_orchestrator,
    })

    result = await report_receive_handler(update, context)
    assert result == ConversationHandler.END
    update.message.reply_text.assert_called()


@pytest.mark.asyncio
async def test_report_csirt_notification_sent_when_chat_id_set():
    """Jika CSIRT_CHAT_ID di-set, notifikasi dikirim ke grup CSIRT."""
    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(return_value=_make_pipeline_result())
    mock_orchestrator = MagicMock()
    mock_orchestrator.initialize_state = MagicMock(return_value={})

    update = _make_update("Saya klik link phishing.")
    context = _make_context(bot_data={
        "helpdesk_graph": mock_graph,
        "orchestrator": mock_orchestrator,
    })

    with patch.dict("os.environ", {"CSIRT_CHAT_ID": "999888"}):
        await report_receive_handler(update, context)

    context.bot.send_message.assert_called_once()
    call_kwargs = context.bot.send_message.call_args
    assert call_kwargs[1]["chat_id"] == "999888" or call_kwargs[0][0] == "999888"


@pytest.mark.asyncio
async def test_report_csirt_notification_not_sent_when_no_chat_id():
    """Jika CSIRT_CHAT_ID tidak di-set, notifikasi tidak dikirim."""
    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(return_value=_make_pipeline_result())
    mock_orchestrator = MagicMock()
    mock_orchestrator.initialize_state = MagicMock(return_value={})

    update = _make_update("Saya klik link phishing.")
    context = _make_context(bot_data={
        "helpdesk_graph": mock_graph,
        "orchestrator": mock_orchestrator,
    })

    with patch.dict("os.environ", {}, clear=False):
        import os
        os.environ.pop("CSIRT_CHAT_ID", None)
        await report_receive_handler(update, context)

    context.bot.send_message.assert_not_called()


# ---------------------------------------------------------------------------
# /cancel handler
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cancel_handler_ends_conversation():
    update = _make_update()
    context = _make_context()
    result = await cancel_handler(update, context)
    assert result == ConversationHandler.END
    update.message.reply_text.assert_called_once()


# ---------------------------------------------------------------------------
# /status handler
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_status_no_args_shows_usage():
    update = _make_update()
    context = _make_context()
    context.args = []
    await status_handler(update, context)
    call_text = update.message.reply_text.call_args[0][0]
    assert "/status" in call_text


@pytest.mark.asyncio
async def test_status_no_repo_returns_fallback_message():
    update = _make_update()
    context = _make_context(bot_data={"ticket_repository": None})
    context.args = ["TICKET-2026-0001"]
    await status_handler(update, context)
    update.message.reply_text.assert_called_once()


@pytest.mark.asyncio
async def test_status_ticket_found():
    mock_ticket = MagicMock()
    mock_ticket.status = "PENDING_REVIEW"
    mock_ticket.escalation_level = "Mendesak"
    mock_ticket.created_at = None

    mock_repo = MagicMock()
    mock_repo.get_by_ticket_id = MagicMock(return_value=mock_ticket)

    update = _make_update()
    context = _make_context(bot_data={"ticket_repository": mock_repo})
    context.args = ["TICKET-2026-0001"]

    await status_handler(update, context)
    call_text = update.message.reply_text.call_args[0][0]
    assert "PENDING_REVIEW" in call_text


@pytest.mark.asyncio
async def test_status_ticket_not_found():
    mock_repo = MagicMock()
    mock_repo.get_by_ticket_id = MagicMock(return_value=None)

    update = _make_update()
    context = _make_context(bot_data={"ticket_repository": mock_repo})
    context.args = ["TICKET-XXXX-9999"]

    await status_handler(update, context)
    call_text = update.message.reply_text.call_args[0][0]
    assert "tidak ditemukan" in call_text.lower()


# ---------------------------------------------------------------------------
# unknown handler
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_unknown_handler_suggests_commands():
    update = _make_update("halo ini apa")
    context = _make_context()
    await unknown_handler(update, context)
    call_text = update.message.reply_text.call_args[0][0]
    assert "/report" in call_text or "/help" in call_text


# ---------------------------------------------------------------------------
# build_bot_application
# ---------------------------------------------------------------------------

def test_build_bot_application_registers_handlers():
    """build_bot_application harus terdaftar dengan handler yang benar."""
    mock_graph = MagicMock()
    mock_orchestrator = MagicMock()

    with patch("app.telegram.bot.Application") as mock_app_class:
        mock_builder = MagicMock()
        mock_app_class.builder.return_value = mock_builder
        mock_builder.token.return_value = mock_builder
        mock_app = MagicMock()
        mock_app.bot_data = {}
        mock_builder.build.return_value = mock_app

        app = build_bot_application(
            token="fake-token",
            helpdesk_graph=mock_graph,
            orchestrator=mock_orchestrator,
        )

        assert app.bot_data["helpdesk_graph"] is mock_graph
        assert app.bot_data["orchestrator"] is mock_orchestrator
        assert mock_app.add_handler.call_count >= 4  # start, help, status, conv, unknown
