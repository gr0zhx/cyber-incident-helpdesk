"""Bot Telegram helpdesk keamanan siber — antarmuka utama untuk pelapor."""
import logging
import os
import uuid
from typing import Any

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.constants import STATUS_LABEL_TELEGRAM
from app.telegram.templates import format_csirt_alert, format_reporter_confirmation

logger = logging.getLogger(__name__)

# Conversation states
WAITING_REPORT = 0

# Env vars / fallback config
_ADMIN_CHAT_ID_ENV = "CSIRT_CHAT_ID"
_ADMIN_CHAT_ID_FALLBACK = "-1003971618295"


def _get_admin_chat_id() -> str | None:
    # Return None when env var is not explicitly set so tests can assert
    # "no chat id" behavior. The fallback ID is only for production/runtime
    # scenarios and should be provided via environment in deployments.
    val = os.getenv(_ADMIN_CHAT_ID_ENV)
    if val:
        return val
    return None


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler /start — pesan selamat datang."""
    await update.message.reply_text(
        "Selamat datang di Helpdesk Keamanan Siber Pusdatin Kementan! 🛡️\n\n"
        "Gunakan perintah berikut:\n"
        "• /report — Laporkan insiden keamanan siber\n"
        "• /status <ticket_id> — Cek status tiket\n"
        "• /help — Panduan penggunaan\n\n"
        "Tim CSIRT siap membantu Anda."
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler /help — panduan penggunaan."""
    await update.message.reply_text(
        "📋 Panduan Helpdesk Keamanan Siber\n\n"
        "1. Ketik /report lalu kirim deskripsi insiden yang Anda alami.\n"
        "   Contoh: 'Saya menerima email mencurigakan dari CEO'\n\n"
        "2. Sistem akan menganalisis laporan dan memberikan:\n"
        "   • Jenis insiden & tingkat keparahan\n"
        "   • Langkah mitigasi awal\n"
        "   • Nomor tiket untuk tindak lanjut\n\n"
        "3. Gunakan /status TICKET-XXXX-XXXX untuk cek status tiket.\n\n"
        "⚠️ Untuk situasi darurat, hubungi tim CSIRT langsung."
    )


async def report_start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handler /report — mulai flow pelaporan insiden."""
    await update.message.reply_text(
        "Silakan jelaskan insiden keamanan siber yang Anda alami.\n\n"
        "Deskripsikan secara singkat: apa yang terjadi, kapan, dan dampaknya.\n"
        "Ketik /cancel untuk membatalkan."
    )
    return WAITING_REPORT


async def report_receive_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Terima deskripsi insiden dari pengguna dan jalankan pipeline."""
    user = update.effective_user
    text = update.message.text

    # Ambil graph & orchestrator dari bot_data (diinjeksi saat startup)
    graph = context.bot_data.get("helpdesk_graph")
    orchestrator = context.bot_data.get("orchestrator")

    if not graph or not orchestrator:
        logger.error("Pipeline tidak terinisialisasi di bot_data")
        await update.message.reply_text(
            "Sistem sedang tidak tersedia. Silakan coba lagi nanti atau hubungi tim CSIRT langsung."
        )
        return ConversationHandler.END

    # Kirim pesan "sedang diproses"
    processing_msg = await update.message.reply_text("⏳ Memproses laporan Anda...")

    try:
        session_id = str(uuid.uuid4())
        state = orchestrator.initialize_state(
            raw_input=text,
            reporter_id=str(user.id),
            reporter_name=user.full_name or "",
            reporter_contact=f"@{user.username}" if user.username else str(user.id),
            session_id=session_id,
        )

        result = await graph.ainvoke(state)

        # Hapus pesan "sedang diproses"
        await processing_msg.delete()

        await _send_result(update, context, result)

    except Exception as exc:
        logger.exception("Error memproses laporan dari user %s: %s", user.id, exc)
        await processing_msg.delete()
        await update.message.reply_text(
            "Terjadi kesalahan saat memproses laporan Anda. "
            "Silakan coba lagi atau hubungi tim CSIRT secara langsung."
        )

    return ConversationHandler.END


async def _send_result(
    update: Update, context: ContextTypes.DEFAULT_TYPE, result: dict[str, Any]
) -> None:
    """Kirim hasil pipeline ke pelapor dan (jika ada) ke grup CSIRT."""
    requires_clarification = result.get("requires_clarification", False)
    clarification_message = result.get("clarification_message", "")

    if requires_clarification and clarification_message:
        await update.message.reply_text(clarification_message)
        return

    # Respons ke pelapor
    ticket_id = result.get("ticket_id") or "DALAM PROSES"
    incident_type = result.get("incident_type") or "Tidak terklasifikasi"
    severity = result.get("severity") or "Tidak diketahui"
    confidence = result.get("confidence_score", 0.0)
    mitigation = result.get("mitigation_recommendation") or "Hubungi tim CSIRT secara langsung."

    reporter_msg = format_reporter_confirmation(
        ticket_id=ticket_id,
        incident_type=incident_type,
        severity=severity,
        confidence=confidence,
        mitigation_steps=mitigation,
    )
    await update.message.reply_text(reporter_msg)

    # Kirim alert ke grup CSIRT jika ada chat ID
    csirt_chat_id = _get_admin_chat_id()
    if csirt_chat_id:
        try:
            csirt_msg = format_csirt_alert(
                ticket_id=ticket_id,
                incident_type=incident_type,
                severity=severity,
                reporter_name=result.get("reporter_name") or "Tidak diketahui",
                timestamp=result.get("timestamp_received", ""),
                description_short=result.get("sanitized_input") or result.get("raw_input", ""),
                mitigation_short=mitigation,
            )
            await context.bot.send_message(chat_id=csirt_chat_id, text=csirt_msg)
        except Exception as exc:
            logger.warning("Gagal kirim alert ke CSIRT: %s", exc)


async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handler /cancel — batalkan flow yang sedang berjalan."""
    await update.message.reply_text("Pelaporan dibatalkan. Ketik /report untuk memulai lagi.")
    return ConversationHandler.END


async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler /status <ticket_id> — tampilkan status tiket."""
    args = context.args
    if not args:
        await update.message.reply_text(
            "Gunakan: /status <ticket_id>\nContoh: /status TICKET-2026-0001"
        )
        return

    ticket_id = args[0].upper()
    ticket_repo = context.bot_data.get("ticket_repository")

    if not ticket_repo:
        await update.message.reply_text(
            f"Tiket {ticket_id} sedang diperiksa. "
            "Fitur pengecekan status otomatis belum tersedia. "
            "Silakan hubungi tim CSIRT untuk informasi lebih lanjut."
        )
        return

    try:
        ticket = ticket_repo.get_ticket_by_id(ticket_id)
        if ticket:
            status_label = STATUS_LABEL_TELEGRAM.get(ticket.status, ticket.status)
            created = str(ticket.created_at)[:19] if ticket.created_at else "-"
            updated = str(ticket.updated_at)[:19] if ticket.updated_at else "-"
            assigned = ticket.assigned_to or "Belum ditugaskan"

            await update.message.reply_text(
                f"📋 Status Tiket: {ticket_id}\n\n"
                f"Status   : {status_label}\n"
                f"Jenis    : {ticket.incident_type}\n"
                f"Keparahan: {ticket.severity}\n"
                f"Ditugaskan: {assigned}\n"
                f"Dibuat   : {created}\n"
                f"Diperbarui: {updated}"
            )
        else:
            await update.message.reply_text(
                f"Tiket {ticket_id} tidak ditemukan. Pastikan nomor tiket benar.\n"
                f"Contoh format: /status TICKET-2026-0001"
            )
    except Exception as exc:
        logger.exception("Error mengambil tiket %s: %s", ticket_id, exc)
        await update.message.reply_text("Gagal mengambil informasi tiket. Coba lagi nanti.")


async def unknown_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk pesan di luar conversation — arahkan ke /help."""
    await update.message.reply_text(
        "Ketik /report untuk melaporkan insiden, atau /help untuk bantuan."
    )


# ---------------------------------------------------------------------------
# Bot builder
# ---------------------------------------------------------------------------

def build_bot_application(
    token: str,
    helpdesk_graph: Any,
    orchestrator: Any,
    ticket_repository: Any = None,
) -> Application:
    """Build Application PTB dengan semua handler terdaftar.

    Args:
        token: TELEGRAM_BOT_TOKEN
        helpdesk_graph: LangGraph compiled graph
        orchestrator: OrchestratorAgent (untuk initialize_state)
        ticket_repository: TicketRepository opsional (untuk /status)
    """
    app = Application.builder().token(token).build()

    # Injeksi dependensi via bot_data
    app.bot_data["helpdesk_graph"] = helpdesk_graph
    app.bot_data["orchestrator"] = orchestrator
    app.bot_data["ticket_repository"] = ticket_repository

    # ConversationHandler untuk flow /report
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("report", report_start_handler)],
        states={
            WAITING_REPORT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, report_receive_handler),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_handler)],
    )

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("status", status_handler))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_handler))

    return app
