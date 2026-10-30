#!/usr/bin/env python3
"""
============================================================
سكريبت فحص المواعيد النهائية المستقل
يُستدعى من GitHub Actions لإرسال التذكيرات

المؤلف: Baran Avisat
============================================================
"""

import sys
import logging
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import settings
from src.orchestrator import Orchestrator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)


def main():
    if not settings.is_supabase_ready:
        print("❌ Supabase غير مُعد. لا يمكن فحص المواعيد.")
        sys.exit(1)

    if not settings.is_telegram_ready:
        print("❌ تليجرام غير مُعد. لا يمكن إرسال التذكيرات.")
        sys.exit(1)

    orch = Orchestrator()
    count = orch.check_deadlines()

    if count == 0:
        print("✅ لا توجد مواعيد نهائية خلال الأسبوع القادم.")
    else:
        print(f"✅ تم إرسال {count} تذكير بنجاح.")


if __name__ == "__main__":
    main()
