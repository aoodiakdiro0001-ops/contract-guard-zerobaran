"""
============================================================
المنسّق الرئيسي - العقل الذي يربط جميع الطبقات
ينفّذ دورة التحليل الكاملة: استلام → استخراج → تقسيم → تحليل → أرشفة → تسليم

المؤلف: Baran Avisat
============================================================"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from .config import settings
from .parsers.pdf_parser import PDFParser
from .parsers.docx_parser import DocxParser
from .parsers.contract_segmenter import ContractSegmenter
from .ai.gemini_analyzer import GeminiAnalyzer
from .ai.groq_analyzer import GroqAnalyzer
from .database.supabase_client import SupabaseClient
from .delivery.telegram_bot import TelegramNotifier
from .delivery.formatter import ReportFormatter

logger = logging.getLogger(__name__)


class Orchestrator:
    """المنسّق الرئيسي - يدير دورة حياة تحليل العقد الكاملة."""

    def __init__(self):
        self.db = SupabaseClient() if settings.is_supabase_ready else None
        self.notifier = TelegramNotifier() if settings.is_telegram_ready else None
        self._analyzer = None

    def _get_analyzer(self):
        """اختيار المحرك النشط."""
        if self._analyzer is not None:
            return self._analyzer

        if settings.ai_provider == "gemini" and settings.is_gemini_ready:
            self._analyzer = GeminiAnalyzer()
        elif settings.ai_provider == "groq" and settings.is_groq_ready:
            self._analyzer = GroqAnalyzer()
        elif settings.is_gemini_ready:
            self._analyzer = GeminiAnalyzer()
        elif settings.is_groq_ready:
            self._analyzer = GroqAnalyzer()
        else:
            raise RuntimeError(
                "لا يوجد مزود ذكاء اصطناعي جاهز. "
                "تحقق من GEMINI_API_KEY أو GROQ_API_KEY في ملف .env"
            )
        return self._analyzer

    def analyze_file(
        self,
        file_path: str | Path,
        notify: bool = True,
        save_report: bool = True,
    ) -> Dict[str, Any]:
        """
        التحليل الكامل لملف عقد.

        Args:
            file_path: مسار ملف العقد (PDF أو DOCX)
            notify: إرسال التقرير عبر تليجرام
            save_report: حفظ التقرير في ملف محلي

        Returns:
            قاموس التقرير الكامل.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"الملف غير موجود: {file_path}")

        logger.info("=" * 60)
        logger.info("🚀 بدء تحليل العقد: %s", file_path.name)
        logger.info("=" * 60)

        # ===== الطبقة 1: الاستخراج =====
        parsed = self._extract(file_path)
        logger.info("📄 الطبقة 1: تم استخراج %d صفحة", parsed["page_count"])

        # ===== الطبقة 2: التقسيم إلى بنود =====
        clauses = ContractSegmenter.segment(parsed["text"])
        clauses_dicts = ContractSegmenter.to_dict_list(clauses)
        logger.info("✂️ الطبقة 2: تم استخراج %d بند قانوني", len(clauses_dicts))

        # ===== الطبقة 3: التحليل الذكي =====
        analyzer = self._get_analyzer()
        contract_title = parsed["metadata"].get("title", file_path.stem)
        report = analyzer.analyze_contract(
            contract_title=contract_title,
            clauses=clauses_dicts,
        )
        report["metadata"] = parsed["metadata"]
        report["analyzed_at"] = datetime.now().isoformat()
        logger.info("🧠 الطبقة 3: اكتمل التحليل القانوني")

        # ===== الطبقة 4: الأرشفة =====
        if self.db:
            contract_id = self.db.save_contract(
                title=contract_title,
                source_file=file_path.name,
                raw_text=parsed["text"],
                metadata=parsed["metadata"],
            )
            if contract_id:
                self.db.save_risk_report(contract_id, report)
                report["contract_id"] = contract_id
                logger.info("💾 الطبقة 4: تمت الأرشفة في Supabase")

        # ===== التسليم عبر تليجرام =====
        if notify and self.notifier:
            message = ReportFormatter.to_telegram_message(report)
            self.notifier.send_message_sync(message)
            logger.info("📤 تم إرسال التقرير إلى تليجرام")

        # ===== حفظ التقرير محلياً =====
        if save_report:
            self._save_local_report(report, file_path.stem)
            logger.info("📁 تم حفظ التقرير محلياً")

        logger.info("=" * 60)
        logger.info("✅ اكتمل التحليل بنجاح")
        logger.info("=" * 60)

        return report

    def analyze_text(
        self,
        text: str,
        title: str = "عقد منصوص مباشرة",
        notify: bool = False,
    ) -> Dict[str, Any]:
        """تحليل نص عقد مباشر دون ملف."""
        clauses = ContractSegmenter.segment(text)
        clauses_dicts = ContractSegmenter.to_dict_list(clauses)

        analyzer = self._get_analyzer()
        report = analyzer.analyze_contract(
            contract_title=title,
            clauses=clauses_dicts,
        )
        report["analyzed_at"] = datetime.now().isoformat()

        if notify and self.notifier:
            message = ReportFormatter.to_telegram_message(report)
            self.notifier.send_message_sync(message)

        return report

    def _extract(self, file_path: Path) -> Dict[str, Any]:
        """استخراج النص حسب نوع الملف."""
        if PDFParser.can_handle(file_path):
            return PDFParser.extract(file_path)
        if DocxParser.can_handle(file_path):
            return DocxParser.extract(file_path)
        raise ValueError(
            f"صيغة غير مدعومة: {file_path.suffix}. المدعوم: PDF, DOCX"
        )

    def _save_local_report(self, report: Dict[str, Any], stem: str):
        """حفظ التقرير بصيغتي JSON و Markdown."""
        # JSON
        json_path = settings.output_dir / f"{stem}_تقرير.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # Markdown
        md_path = settings.output_dir / f"{stem}_تقرير.md"
        md_content = ReportFormatter.to_markdown_report(report)
        md_path.write_text(md_content, encoding="utf-8")

    def check_deadlines(self) -> int:
        """فحص المواعيد النهائية القادمة وإرسال إشعارات."""
        if not self.db or not self.notifier:
            return 0

        deadlines = self.db.get_upcoming_deadlines(days_ahead=7)
        count = 0
        for d in deadlines:
            message = (
                f"⏰ تذكير بموعد نهائي!\n\n"
                f"📋 {d.get('title', 'موعد')}\n"
                f"📅 التاريخ: {d.get('due_date', '')}\n"
                f"📝 {d.get('description', '')}\n\n"
                f"🛡️ Contract-Guard ZeroBaran"
            )
            if self.notifier.send_message_sync(message):
                self.db.mark_deadline_notified(d["id"])
                count += 1

        return count


# نقطة دخول للاستخدام المباشر
def main():
    """تشغيل سريع من سطر الأوامر."""
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    if len(sys.argv) < 2:
        print("الاستخدام: python -m src.orchestrator <مسار_الملف>")
        print("مثال: python -m src.orchestrator data/contract.pdf")
        return

    file_path = sys.argv[1]
    orch = Orchestrator()
    report = orch.analyze_file(file_path)
    print(ReportFormatter.to_short_summary(report))


if __name__ == "__main__":
    main()
