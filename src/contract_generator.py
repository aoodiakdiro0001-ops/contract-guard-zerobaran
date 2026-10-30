"""
============================================================
مولّد مسودات الاتفاقيات القانونية المحكمة
يستخدم العقل القانوني الذكي لإنتاج عقود متوازنة جاهزة للتوقيع

المؤلف: Baran Avisat
============================================================
"""

import logging
from typing import Dict, Any, Optional

from .config import settings
from .ai.gemini_analyzer import GeminiAnalyzer
from .ai.groq_analyzer import GroqAnalyzer

logger = logging.getLogger(__name__)


class ContractGenerator:
    """مولّد مسودات الاتفاقيات القانونية."""

    # قوالب أنواع العقود المدعومة
    CONTRACT_TYPES = {
        "nda": "اتفاقية عدم إفصاح (NDA)",
        "employment": "عقد عمل",
        "partnership": "اتفاقية شراكة",
        "freelance": "عقد عمل حر (Freelance)",
        "service": "اتفاقية تقديم خدمات",
        "tos": "شروط الخدمة (Terms of Service)",
        "custom": "عقد مخصّص",
    }

    def __init__(self):
        self._analyzer = None

    def _get_analyzer(self):
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
            raise RuntimeError("لا يوجد مزود ذكاء اصطناعي جاهز.")
        return self._analyzer

    def generate(
        self,
        contract_type: str,
        parties: Dict[str, str],
        terms: Dict[str, Any],
    ) -> str:
        """
        توليد مسودة اتفاقية قانونية كاملة.

        Args:
            contract_type: نوع العقد (nda, employment, partnership...)
            parties: قاموس الأطراف {role: name}
            terms: شروط العقد {key: value}

        Returns:
            نص المسودة القانونية جاهز للتوقيع.
        """
        analyzer = self._get_analyzer()

        type_label = self.CONTRACT_TYPES.get(
            contract_type, contract_type
        )
        logger.info("📝 توليد مسودة: %s", type_label)

        draft = analyzer.generate_contract(
            contract_type=type_label,
            parties=parties,
            terms=terms,
        )

        # إضافة ترويسة الملكية
        header = (
            "# مسودة قانونية مُولّدة بواسطة Contract-Guard ZeroBaran\n"
            f"# نوع الاتفاقية: {type_label}\n"
            f"# المؤلف: Baran Avisat | Baranavisat@gmail.com\n"
            "# ⚠️ هذه مسودة أولية. يُنصح بمراجعتها من قبل مستشار قانوني قبل التوقيع.\n"
            "# ============================================================\n\n"
        )
        return header + draft

    def generate_nda(
        self,
        disclosing_party: str,
        receiving_party: str,
        purpose: str,
        duration_months: int = 24,
    ) -> str:
        """توليد سريع لاتفاقية عدم إفصاح."""
        return self.generate(
            contract_type="nda",
            parties={
                "الطرف المُفصِح (Disclosing Party)": disclosing_party,
                "الطرف المُستقبِل (Receiving Party)": receiving_party,
            },
            terms={
                "الغرض من الإفصاح": purpose,
                "مدة الالتزام بالسرية": f"{duration_months} شهراً",
                "الولاية القانونية": "يحددها الأطراف",
            },
        )

    def generate_employment(
        self,
        employer: str,
        employee: str,
        position: str,
        salary: str,
        start_date: str,
    ) -> str:
        """توليد سريع لعقد عمل."""
        return self.generate(
            contract_type="employment",
            parties={
                "صاحب العمل (Employer)": employer,
                "الموظف (Employee)": employee,
            },
            terms={
                "المسمى الوظيفي": position,
                "الراتب": salary,
                "تاريخ بدء العمل": start_date,
                "ساعات العمل": "وفق نظام الشركة",
                "فترة الإشعار": "30 يوماً",
            },
        )

    def generate_partnership(
        self,
        partner_a: str,
        partner_b: str,
        business: str,
        profit_split: str,
    ) -> str:
        """توليد سريع لاتفاقية شراكة."""
        return self.generate(
            contract_type="partnership",
            parties={
                "الشريك الأول": partner_a,
                "الشريك الثاني": partner_b,
            },
            terms={
                "نوع النشاط": business,
                "تقسيم الأرباح": profit_split,
                "مدة الشراكة": "غير محددة ما لم يُتفق على إنهاء",
                "آلية حل النزاعات": "تحكيم ملزم",
            },
        )
