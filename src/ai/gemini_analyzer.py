"""
============================================================
محرك التحليل القانوني عبر Google Gemini API
الطبقة المجانية من Google AI Studio

المؤلف: Baran Avisat
============================================================
"""

import json
import re
import logging
from typing import List, Dict, Any, Optional

from ..config import settings
from .prompts import LegalPrompts, ClauseRisk

logger = logging.getLogger(__name__)


class GeminiAnalyzer:
    """العقل القانوني الذكي المعتمد على Google Gemini."""

    MODEL_NAME = "gemini-1.5-flash"  # الأسرع في الطبقة المجانية

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.gemini_api_key
        self._model = None
        self._init_model()

    def _init_model(self):
        """تهيئة نموذج Gemini."""
        if not self.api_key:
            logger.warning("لم يُضبط مفتاح Gemini API. المحرك غير جاهز.")
            return
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel(self.MODEL_NAME)
            logger.info("تم تهيئة نموذج Gemini بنجاح: %s", self.MODEL_NAME)
        except Exception as exc:
            logger.error("فشل تهيئة Gemini: %s", exc)
            self._model = None

    @property
    def is_ready(self) -> bool:
        return self._model is not None

    def _call_gemini(self, prompt: str, temperature: float = 0.3) -> str:
        """استدعاء Gemini مع معالجة الأخطاء."""
        if not self.is_ready:
            raise RuntimeError("محرك Gemini غير جاهز. تحقق من المفتاح.")
        try:
            response = self._model.generate_content(
                prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": 2048,
                },
            )
            return response.text.strip()
        except Exception as exc:
            logger.error("خطأ في استدعاء Gemini: %s", exc)
            raise

    @staticmethod
    def _parse_json_response(raw: str) -> Dict[str, Any]:
        """استخراج JSON من نص قد يحتوي على شفرات markdown."""
        # إزالة علامات markdown إن وُجدت
        cleaned = re.sub(r"```(?:json)?\s*", "", raw)
        cleaned = cleaned.replace("```", "").strip()
        # محاولة العثور على أول قوس JSON
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        if start == -1 or end == 0:
            logger.error("تعذّر تحليل JSON من الاستجابة: %s", raw[:200])
            return {}
        try:
            return json.loads(cleaned[start:end])
        except json.JSONDecodeError as exc:
            logger.error("JSON غير صالح: %s", exc)
            return {}

    def analyze_clause(
        self,
        clause_number: str,
        clause_text: str,
        strictness: str = None,
    ) -> ClauseRisk:
        """تحليل بند قانوني واحد وإرجاع تقييم المخاطر."""
        strictness = strictness or settings.analysis_strictness
        prompt = LegalPrompts.analysis_prompt(
            clause_text=clause_text,
            clause_number=clause_number,
            strictness=strictness,
            language=settings.report_language,
        )

        try:
            raw = self._call_gemini(prompt)
            data = self._parse_json_response(raw)
            return ClauseRisk(
                clause_number=data.get("clause_number", clause_number),
                clause_title=data.get("clause_title", ""),
                risk_level=data.get("risk_level", "غير محدد"),
                risk_summary=data.get("risk_summary", "تعذّر التحليل"),
                risk_factors=data.get("risk_factors", []),
                recommendation=data.get("recommendation", ""),
                alternative_drafting=data.get("alternative_drafting", ""),
            )
        except Exception as exc:
            logger.error("فشل تحليل البند %s: %s", clause_number, exc)
            return ClauseRisk(
                clause_number=clause_number,
                clause_title="",
                risk_level="غير محدد",
                risk_summary=f"تعذّر التحليل: {exc}",
                risk_factors=[],
                recommendation="أعد المحاولة أو راجع البند يدوياً.",
                alternative_drafting="",
            )

    def analyze_contract(
        self,
        contract_title: str,
        clauses: List[Dict[str, Any]],
        strictness: str = None,
    ) -> Dict[str, Any]:
        """تحليل عقد كامل بنداً ببند ثم إصدار تقييم شامل."""
        if not clauses:
            return {"error": "لا توجد بنود لتحليلها"}

        clause_risks: List[ClauseRisk] = []
        for clause in clauses:
            risk = self.analyze_clause(
                clause_number=str(clause.get("number", clause.get("index", "?"))),
                clause_text=clause.get("text", ""),
                strictness=strictness,
            )
            clause_risks.append(risk)

        # التقييم الشامل
        overall = self._overall_assessment(contract_title, clause_risks)

        return {
            "contract_title": contract_title,
            "clauses_analyzed": len(clause_risks),
            "clause_risks": [c.to_dict() for c in clause_risks],
            "overall_assessment": overall,
        }

    def _overall_assessment(
        self,
        contract_title: str,
        clause_risks: List[ClauseRisk],
    ) -> Dict[str, Any]:
        """إصدار تقييم شامل بناءً على تحليل البنود."""
        summaries = [
            {
                "clause_number": c.clause_number,
                "risk_level": c.risk_level,
                "risk_summary": c.risk_summary,
            }
            for c in clause_risks
        ]
        prompt = LegalPrompts.overall_assessment_prompt(
            contract_title=contract_title,
            clauses_summaries=summaries,
            language=settings.report_language,
        )

        try:
            raw = self._call_gemini(prompt, temperature=0.4)
            return self._parse_json_response(raw)
        except Exception as exc:
            logger.error("فشل التقييم الشامل: %s", exc)
            return {
                "overall_verdict": "تعذّر التقييم الشامل",
                "overall_risk_score": "—",
                "top_3_risks": [],
                "negotiation_priorities": [],
                "final_recommendation": f"حدث خطأ: {exc}",
                "missing_clauses": [],
            }

    def generate_contract(
        self,
        contract_type: str,
        parties: Dict[str, str],
        terms: Dict[str, Any],
    ) -> str:
        """توليد مسودة اتفاقية قانونية محكمة."""
        prompt = LegalPrompts.contract_generation_prompt(
            contract_type=contract_type,
            parties=parties,
            terms=terms,
            language=settings.report_language,
        )
        return self._call_gemini(prompt, temperature=0.5)
