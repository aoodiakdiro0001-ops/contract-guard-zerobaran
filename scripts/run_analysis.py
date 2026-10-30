#!/usr/bin/env python3
"""
============================================================
سكريبت تشغيل التحليل من سطر الأوامر
يدعم: تحليل ملف، تحليل نص، فحص المواعيد النهائية، فحص العقود الجديدة

المؤلف: Baran Avisat
============================================================
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# إضافة جذر المشروع
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import settings
from src.orchestrator import Orchestrator
from src.delivery.formatter import ReportFormatter


def setup_logging(debug: bool = False):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )


def cmd_analyze_file(args):
    """تحليل ملف عقد واحد."""
    orch = Orchestrator()
    report = orch.analyze_file(
        args.file,
        notify=not args.no_notify,
        save_report=True,
    )
    print("\n" + "=" * 60)
    print(ReportFormatter.to_short_summary(report))
    print("=" * 60)


def cmd_analyze_text(args):
    """تحليل نص مباشر."""
    text = args.text
    if not text and args.text_file:
        text = Path(args.text_file).read_text(encoding="utf-8")
    if not text:
        print("❌ يجب توفير نص أو ملف نصي.")
        sys.exit(1)

    orch = Orchestrator()
    report = orch.analyze_text(text, title=args.title, notify=not args.no_notify)
    print(ReportFormatter.to_short_summary(report))


def cmd_check_deadlines(args):
    """فحص المواعيد النهائية."""
    orch = Orchestrator()
    count = orch.check_deadlines()
    print(f"✅ تم إرسال {count} إشعار موعد نهائي.")


def cmd_check_new(args):
    """فحص العقود الجديدة في مجلد الاستلام."""
    inbox = settings.uploads_dir
    if not inbox.exists():
        print("📭 مجلد الاستلام فارغ.")
        return

    new_files = list(inbox.glob("*.pdf")) + list(inbox.glob("*.docx"))
    if not new_files:
        print("📭 لا توجد عقود جديدة.")
        return

    orch = Orchestrator()
    for f in new_files:
        print(f"\n📋 معالجة: {f.name}")
        try:
            report = orch.analyze_file(f, notify=True, save_report=True)
            print(ReportFormatter.to_short_summary(report))
        except Exception as e:
            print(f"❌ فشل: {e}")


def cmd_status(args):
    """عرض حالة النظام."""
    print(settings.summary())


def main():
    parser = argparse.ArgumentParser(
        description="🛡️ Contract-Guard ZeroBaran - أداة سطر الأوامر",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
أمثلة:
  python scripts/run_analysis.py file contract.pdf
  python scripts/run_analysis.py text --text-file contract.txt
  python scripts/run_analysis.py --check-deadlines
  python scripts/run_analysis.py --check-new
  python scripts/run_analysis.py --status

المؤلف: Baran Avisat (Baranavisat@gmail.com)
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="الأوامر المتاحة")

    # تحليل ملف
    p_file = subparsers.add_parser("file", help="تحليل ملف عقد")
    p_file.add_argument("file", help="مسار ملف العقد (PDF/DOCX)")
    p_file.add_argument("--no-notify", action="store_true", help="عدم الإرسال لتليجرام")
    p_file.set_defaults(func=cmd_analyze_file)

    # تحليل نص
    p_text = subparsers.add_parser("text", help="تحليل نص مباشر")
    p_text.add_argument("--text", help="نص العقد")
    p_text.add_argument("--text-file", help="ملف نصي يحتوي العقد")
    p_text.add_argument("--title", default="عقد منصوص", help="عنوان العقد")
    p_text.add_argument("--no-notify", action="store_true")
    p_text.set_defaults(func=cmd_analyze_text)

    # اختصارات سريعة
    parser.add_argument("--check-deadlines", action="store_true", help="فحص المواعيد النهائية")
    parser.add_argument("--check-new", action="store_true", help="فحص عقود جديدة")
    parser.add_argument("--status", action="store_true", help="حالة النظام")
    parser.add_argument("--debug", action="store_true", help="تفعيل السجل التفصيلي")

    args = parser.parse_args()

    setup_logging(args.debug)

    # اختصارات
    if args.check_deadlines:
        cmd_check_deadlines(args)
        return
    if args.check_new:
        cmd_check_new(args)
        return
    if args.status:
        cmd_status(args)
        return

    if not args.command:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
