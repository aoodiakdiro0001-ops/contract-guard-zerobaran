"""
============================================================
بوت تليجرام - قناة الاستقبال والتسليم الفوري
يستقبل ملفات العقود ويُرسل تقارير المخاطر القانونية فوراً

المؤلف: Baran Avisat
============================================================
"""

import os
import logging
import asyncio
from pathlib import Path
from typing import Optional

from ..config import settings
from ..parsers.pdf_parser import PDFParser
from ..parsers.docx_parser import DocxParser
from ..parsers.contract_segmenter import ContractSegmenter
from ..ai.gemini_analyzer import GeminiAnalyzer
from ..ai.groq_analyzer import GroqAnalyzer
from ..database.supabase_client import SupabaseClient
from .formatter import ReportFormatter

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """إرسال الإشعارات والتقارير عبر تليجرام."""

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
    ):
        self.bot_token = bot_token or settings.telegram_bot_token
        self.chat_id = chat_id or settings.telegram_chat_id

    async def send_message(self, text: str) -> bool:
        """إرسال رسالة نصية عبر البوت."""
        if not self.bot_token or not self.chat_id:
            logger.warning("إعدادات تليجرام ناقصة.")
            return False
        try:
            from telegram import Bot
            bot = Bot(token=self.bot_token)
            # تقسيم الرسائل الطويلة
            for i in range(0, len(text), 4096):
                await bot.send_message(
                    chat_id=self.chat_id,
                    text=text[i:i + 4096],
                    parse_mode=None,
                )
            return True
        except Exception as exc:
            logger.error("فشل إرسال رسالة تليجرام: %s", exc)
            return False

    def send_message_sync(self, text: str) -> bool:
        """نسخة متزامنة من الإرسال."""
        try:
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(self.send_message(text))
            finally:
                loop.close()
        except Exception as exc:
            logger.error("فشل الإرسال المتزامن: %s", exc)
            return False


def get_analyzer():
    """اختيار المحرك المنشط حسب الإعدادات."""
    provider = settings.ai_provider
    if provider == "gemini" and settings.is_gemini_ready:
        return GeminiAnalyzer()
    if provider == "groq" and settings.is_groq_ready:
        return GroqAnalyzer()
    # احتياط: استخدم أي مزود متاح
    if settings.is_gemini_ready:
        return GeminiAnalyzer()
    if settings.is_groq_ready:
        return GroqAnalyzer()
    raise RuntimeError("لا يوجد مزود ذكاء اصطناعي جاهز. تحقق من المفاتيح.")


def process_document(file_path: str | Path) -> dict:
    """
    المعالجة الكاملة لمستند قانوني:
    1. الاستخراج
    2. التقسيم إلى بنود
    3. التحليل الذكي
    4. الأرشفة
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"الملف غير موجود: {file_path}")

    logger.info("📂 بدء معالجة: %s", file_path.name)

    # 1. الاستخراج
    if PDFParser.can_handle(file_path):
        parsed = PDFParser.extract(file_path)
    elif DocxParser.can_handle(file_path):
        parsed = DocxParser.extract(file_path)
    else:
        raise ValueError(f"صيغة غير مدعومة: {file_path.suffix}")

    logger.info("📄 تم استخراج %d صفحة", parsed["page_count"])

    # 2. التقسيم إلى بنود
    clauses = ContractSegmenter.segment(parsed["text"])
    clauses_dicts = ContractSegmenter.to_dict_list(clauses)
    logger.info("✂️ تم استخراج %d بند قانوني", len(clauses_dicts))

    # 3. التحليل الذكي
    analyzer = get_analyzer()
    contract_title = parsed["metadata"].get("title", file_path.stem)
    report = analyzer.analyze_contract(
        contract_title=contract_title,
        clauses=clauses_dicts,
    )
    report["metadata"] = parsed["metadata"]
    logger.info("🧠 اكتمل التحليل القانوني")

    # 4. الأرشفة في Supabase (اختياري)
    if settings.is_supabase_ready:
        db = SupabaseClient()
        contract_id = db.save_contract(
            title=contract_title,
            source_file=file_path.name,
            raw_text=parsed["text"],
            metadata=parsed["metadata"],
        )
        if contract_id:
            db.save_risk_report(contract_id, report)
            report["contract_id"] = contract_id
            logger.info("💾 تمت الأرشفة في Supabase")

    return report


def run_bot():
    """تشغيل بوت تليجرام في وضع الاستماع المستمر."""
    if not settings.is_telegram_ready:
        logger.error("تليجرام غير جاهز. تحقق من TELEGRAM_BOT_TOKEN و TELEGRAM_CHAT_ID")
        return

    from telegram import Update
    from telegram.ext import (
        ApplicationBuilder,
        CommandHandler,
        MessageHandler,
        filters,
        ContextTypes,
    )

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🛡️ مرحباً بك في Contract-Guard ZeroBaran!\n\n"
            "أرسل لي ملف عقد (PDF أو Word) وسأحلّل لك المخاطر القانونية فوراً.\n\n"
            "الأوامر المتاحة:\n"
            "/start - هذه الرسالة\n"
            "/status - حالة النظام\n"
            "/help - المساعدة\n\n"
            "👤 المؤلف: Baran Avisat"
        )

    async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(settings.summary())

    async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "📋 كيفية الاستخدام:\n\n"
            "1. أرسل ملف العقد بصيغة PDF أو DOCX\n"
            "2. انتظر دقائق حتى يكتمل التحليل\n"
            "3. ستستلم تقرير المخاطر القانونية الكامل\n\n"
            "🔒 جميع البيانات تُعالج بسرية تامة.\n"
            "👤 Baran Avisat | Baranavisat@gmail.com"
        )

    async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """استقبال ملف العقد ومعالجته."""
        doc = update.message.document
        if not doc:
            return

        await update.message.reply_text(
            f"📥 تم استلام الملف: {doc.file_name}\n⏳ جارٍ التحليل..."
        )

        # تنزيل الملف
        file = await doc.get_file()
        download_path = settings.uploads_dir / doc.file_name
        await file.download_to_drive(str(download_path))

        try:
            # المعالجة الكاملة
            report = process_document(download_path)

            # تنسيق التقرير وإرساله
            message = ReportFormatter.to_telegram_message(report)
            await update.message.reply_text(message)

            # إرسال تقرير Markdown كملف
            md_report = ReportFormatter.to_markdown_report(report)
            md_path = settings.output_dir / f"{Path(doc.file_name).stem}_تقرير.md"
            md_path.write_text(md_report, encoding="utf-8")
            with open(md_path, "rb") as f:
                await update.message.reply_document(
                    document=f,
                    filename=md_path.name,
                    caption="📋 التقرير التفصيلي الكامل",
                )

        except Exception as exc:
            logger.error("فشل المعالجة: %s", exc, exc_info=True)
            await update.message.reply_text(
                f"❌ حدث خطأ أثناء المعالجة: {exc}\n"
                "يرجى التأكد من صحة الملف والمحاولة مجدداً."
            )

    async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """استقبال نص عقد مباشرة."""
        text = update.message.text
        if len(text) < 50:
            await update.message.reply_text(
                "⚠️ النص قصير جداً. الصق نص عقد كامل (50 حرفاً على الأقل)."
            )
            return

        await update.message.reply_text("⏳ جارٍ تحليل النص...")

        try:
            clauses = ContractSegmenter.segment(text)
            clauses_dicts = ContractSegmenter.to_dict_list(clauses)

            analyzer = get_analyzer()
            report = analyzer.analyze_contract(
                contract_title="عقد منقول مباشرة",
                clauses=clauses_dicts,
            )

            message = ReportFormatter.to_telegram_message(report)
            await update.message.reply_text(message)
        except Exception as exc:
            await update.message.reply_text(f"❌ خطأ: {exc}")

    # بناء التطبيق وتشغيله
    app = ApplicationBuilder().token(settings.telegram_bot_token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, handle_text
    ))

    logger.info("🚀 بوت Contract-Guard ZeroBaran يعمل الآن...")
    app.run_polling()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_bot()
