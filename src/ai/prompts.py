"""
============================================================
مكتبة بروتوكولات التحليل القانوني والـ Prompts الهندسية
تحتوي على التعليمات الدقيقة التي تُغذّي العقل القانوني الذكي

المؤلف: Baran Avisat
============================================================
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Any


class RiskLevel(str, Enum):
    """مستويات تصنيف المخاطر القانونية."""
    HIGH = "عالية"
    MEDIUM = "متوسطة"
    LOW = "منخفضة"
    SAFE = "آمن"

    @property
    def emoji(self) -> str:
        return {
            "عالية": "🔴",
            "متوسطة": "🟠",
            "منخفضة": "🟡",
            "آمن": "🟢",
        }[self.value]


@dataclass
class ClauseRisk:
    """تقييم مخاطر بند واحد."""
    clause_number: str
    clause_title: str
    risk_level: str
    risk_summary: str
    risk_factors: List[str]
    recommendation: str
    alternative_drafting: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "clause_number": self.clause_number,
            "clause_title": self.clause_title,
            "risk_level": self.risk_level,
            "risk_summary": self.risk_summary,
            "risk_factors": self.risk_factors,
            "recommendation": self.recommendation,
            "alternative_drafting": self.alternative_drafting,
        }


class LegalPrompts:
    """مكتبة التعليمات القانونية الموجّهة للذكاء الاصطناعي."""

    SYSTEM_ROLE = (
        "أنت خبير قانوني بارز ومستشار عقود دولي يتمتع بـ 30 عاماً من الخبرة في "
        "صياغة العقود التجارية، اتفاقيات عدم الإفصاح (NDA)، عقود العمل، "
        "اتفاقيات الشراكة، وشروط الخدمة. مهمتك تحليل البنود القانونية بدقة، "
        "كشف الشروط المجحفة والفخاخ الخفية، وتقديم صياغات بديلة آمنة تحمي "
        "مصالح موكلك. تتعامل مع العقود باللغتين العربية والإنجليزية."
    )

    @classmethod
    def analysis_prompt(
        cls,
        clause_text: str,
        clause_number: str,
        strictness: str = "balanced",
        language: str = "ar",
    ) -> str:
        """صياغة تعليمة تحليل بند قانوني واحد."""
        strictness_rules = {
            "lenient": "اعتبر الخطر منخفضاً ما لم يكن البند واضح الضرر.",
            "balanced": "حلّل بموضوعية متوازنة، لا تتشدد ولا تتهاون.",
            "strict": "اعتبر أي بند غير واضح أو غير متماثل خطراً جسيماً حتى يثبت العكس.",
        }

        lang_instruction = {
            "ar": "اكتب تقييمك باللغة العربية الفصحى.",
            "en": "Write your assessment in formal English.",
            "mixed": "اكتب ملخصاً بالعربية والتفاصيل التقنية بالإنجليزية.",
        }.get(language, "اكتب تقييمك باللغة العربية الفصحى.")

        return f"""{cls.SYSTEM_ROLE}

حلّل البند القانوني التالي كخبير قانوني.

معيار الصرامة: {strictness_rules.get(strictness, strictness_rules["balanced"])}

رقم البند: {clause_number}
نص البند:
\"\"\"
{clause_text}
\"\"\"

مطلوب منك إرجاع النتيجة بصيغة JSON صالحة فقط (بدون نص إضافي قبل أو بعد) بالشكل التالي:
{{
  "clause_number": "{clause_number}",
  "clause_title": "عنصر مختصر للبند",
  "risk_level": "عالية | متوسطة | منخفضة | آمن",
  "risk_summary": "ملخص في جملة أو جملتين يشرح طبيعة الخطر أو يؤكد السلامة",
  "risk_factors": ["عامل خطر 1", "عامل خطر 2"],
  "recommendation": "توصية عملية واضحة (اقبل / عدّل / ارفض) مع التبرير",
  "alternative_drafting": "صياغة بديلة آمنة تحمي مصالحنا، أو 'لا حاجة لتعديل' إن كان البند آمناً"
}}

{lang_instruction}
"""

    @classmethod
    def overall_assessment_prompt(
        cls,
        contract_title: str,
        clauses_summaries: List[Dict[str, Any]],
        language: str = "ar",
    ) -> str:
        """صياغة تعليمة التقييم الشامل للعقد كاملاً."""
        summaries_text = "\n".join(
            f"- البند {c.get('clause_number', '?')}: {c.get('risk_level', '?')} - {c.get('risk_summary', '')}"
            for c in clauses_summaries
        )

        lang_instruction = {
            "ar": "اكتب تقييمك بالعربية الفصحى.",
            "en": "Write in English.",
            "mixed": "اكتب الملخص بالعربية والتفاصيل بالإنجليزية.",
        }.get(language, "اكتب تقييمك بالعربية الفصحى.")

        return f"""{cls.SYSTEM_ROLE}

لقد حللت بنود العقد التالي: "{contract_title}"
ملخص بنود العقد:
{summaries_text}

قدّم الآن تقييماً شاملاً للعقد كاملاً بصيغة JSON فقط:
{{
  "overall_verdict": "آمن للتوقيع | يحتاج تعديلات جوهرية | يُرفض التوقيع",
  "overall_risk_score": "رقم من 0 (آمن تماماً) إلى 100 (خطر جسيم)",
  "top_3_risks": ["الخطر الأكبر", "الخطر الثاني", "الخطر الثالث"],
  "negotiation_priorities": ["الأولوية الأولى للتفاوض", "الثانية", "الثالثة"],
  "final_recommendation": "توصية نهائية في فقرة (3-5 جمل) تحدد ما إذا كان يجب التوقيع أو التفاوض أو الرفض",
  "missing_clauses": ["أي بنود مهمة مفقودة يجب إضافتها"]
}}

{lang_instruction}
"""

    @classmethod
    def contract_generation_prompt(
        cls,
        contract_type: str,
        parties: Dict[str, str],
        terms: Dict[str, Any],
        language: str = "ar",
    ) -> str:
        """صياغة تعليمة توليد مسودة اتفاقية قانونية محكمة."""
        parties_text = "\n".join(
            f"- {role}: {name}" for role, name in parties.items()
        )
        terms_text = "\n".join(
            f"- {k}: {v}" for k, v in terms.items()
        )

        return f"""{cls.SYSTEM_ROLE}

صُغ مسودة اتفاقية قانونية محكمة ومتوازنة تحمي جميع الأطراف.

نوع الاتفاقية: {contract_type}
الأطراف:
{parties_text}

الشروط الأساسية:
{terms_text}

متطلبات الصياغة:
1. اكتب مقدمة واضحة تحدد الأطراف والتاريخ.
2. استخدم بنوداً مرقمة ومنظمة (التعريفات، الالتزامات، السرية، الملكية الفكرية، المسؤولية، الإنهاء، التحكيم، أحكام عامة).
3. اجعل البنود متوازنة لا تميل لطرف على حساب آخر.
4. أضف بند تحكيم واضح وبند إنهاء منصف.
5. اختم بمكان وتاريخ التوقيع.

اكتب المسودة كاملة وجاهزة للتوقيع.
"""
