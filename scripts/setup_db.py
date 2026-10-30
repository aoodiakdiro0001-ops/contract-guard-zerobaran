#!/usr/bin/env python3
"""
============================================================
سكريبت إعداد قاعدة بيانات Supabase
ينشئ الجداول الثلاثة: contracts, risk_reports, deadlines

المؤلف: Baran Avisat
============================================================
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import settings


def main():
    schema_path = ROOT / "src" / "database" / "schema.sql"
    if not schema_path.exists():
        print(f"❌ ملف المخطط غير موجود: {schema_path}")
        sys.exit(1)

    schema_sql = schema_path.read_text(encoding="utf-8")

    if not settings.is_supabase_ready:
        print("❌ Supabase غير مُعد. تحقق من SUPABASE_URL و SUPABASE_KEY في .env")
        print()
        print("📋 إليك مخطط SQL لتشغيله يدوياً في محرر Supabase SQL:")
        print("=" * 60)
        print(schema_sql)
        sys.exit(0)

    print("🔗 جارٍ الاتصال بـ Supabase...")
    try:
        from supabase import create_client
        client = create_client(settings.supabase_url, settings.supabase_key)
        print("✅ تم الاتصال بنجاح.")
        print()
        print("⚠️ لتشغيل المخطط، انسخ الكود التالي والصقه في:")
        print("   Supabase Dashboard → SQL Editor → New Query")
        print()
        print("=" * 60)
        print(schema_sql)
        print("=" * 60)
        print()
        print("بعد تنفيذ المخطط، سيكون النظام جاهزاً للأرشفة.")
    except Exception as e:
        print(f"❌ فشل الاتصال: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
