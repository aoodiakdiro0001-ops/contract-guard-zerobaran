"""
============================================================
Contract-Guard ZeroBaran - مركز الإعدادات
يدير جميع متغيرات البيئة والإعدادات الافتراضية

المؤلف: Baran Avisat
============================================================
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv

# تحميل ملف .env إن وُجد
load_dotenv()


@dataclass
class Settings:
    """إعدادات النظام الموحدة."""

    # ===== العقل القانوني الذكي =====
    gemini_api_key: str = field(
        default_factory=lambda: os.getenv("GEMINI_API_KEY", "")
    )
    groq_api_key: str = field(
        default_factory=lambda: os.getenv("GROQ_API_KEY", "")
    )
    ai_provider: str = field(
        default_factory=lambda: os.getenv("AI_PROVIDER", "gemini").lower()
    )
    analysis_strictness: str = field(
        default_factory=lambda: os.getenv(
            "ANALYSIS_STRICTNESS", "balanced"
        ).lower()
    )
    report_language: str = field(
        default_factory=lambda: os.getenv("REPORT_LANGUAGE", "ar").lower()
    )
    max_clauses_per_batch: int = field(
        default_factory=lambda: int(os.getenv("MAX_CLAUSES_PER_BATCH", "20"))
    )

    # ===== قاعدة البيانات =====
    supabase_url: str = field(
        default_factory=lambda: os.getenv("SUPABASE_URL", "")
    )
    supabase_key: str = field(
        default_factory=lambda: os.getenv("SUPABASE_KEY", "")
    )

    # ===== بوت تليجرام =====
    telegram_bot_token: str = field(
        default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", "")
    )
    telegram_chat_id: str = field(
        default_factory=lambda: os.getenv("TELEGRAM_CHAT_ID", "")
    )

    # ===== مسارات النظام =====
    base_dir: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent.parent
    )
    data_dir: Path = field(init=False)
    output_dir: Path = field(init=False)
    uploads_dir: Path = field(init=False)

    # ===== عام =====
    debug: bool = field(
        default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true"
    )

    def __post_init__(self):
        """تهيئة المسارات وإنشاء المجلدات."""
        self.data_dir = self.base_dir / "data"
        self.output_dir = self.base_dir / "output"
        self.uploads_dir = self.data_dir / "uploads"
        for d in (self.data_dir, self.output_dir, self.uploads_dir):
            d.mkdir(parents=True, exist_ok=True)

    # ----- فحوصات الجاهزية -----
    @property
    def is_gemini_ready(self) -> bool:
        return bool(self.gemini_api_key)

    @property
    def is_groq_ready(self) -> bool:
        return bool(self.groq_api_key)

    @property
    def is_supabase_ready(self) -> bool:
        return bool(self.supabase_url and self.supabase_key)

    @property
    def is_telegram_ready(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_chat_id)

    @property
    def is_ai_ready(self) -> bool:
        if self.ai_provider == "gemini":
            return self.is_gemini_ready
        if self.ai_provider == "groq":
            return self.is_groq_ready
        return self.is_gemini_ready or self.is_groq_ready

    def summary(self) -> str:
        """ملخص حالة الإعدادات لأغراض التشخيص."""
        return (
            "===== حالة نظام Contract-Guard ZeroBaran =====\n"
            f"  المزود الذكي    : {self.ai_provider}\n"
            f"  Gemini جاهز     : {'نعم' if self.is_gemini_ready else 'لا'}\n"
            f"  Groq جاهز       : {'نعم' if self.is_groq_ready else 'لا'}\n"
            f"  Supabase جاهز   : {'نعم' if self.is_supabase_ready else 'لا'}\n"
            f"  تليجرام جاهز    : {'نعم' if self.is_telegram_ready else 'لا'}\n"
            f"  مستوى الصرامة   : {self.analysis_strictness}\n"
            f"  لغة التقارير    : {self.report_language}\n"
            f"  تصحيح الأخطاء   : {'مفعّل' if self.debug else 'معطّل'}\n"
            "=============================================="
        )


# نسخة مفردة (Singleton) للاستخدام في كل الوحدات
settings = Settings()
