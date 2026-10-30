"""
============================================================
محرك التحليل القانوني عبر Groq API (بديل مجاني سريع)
يدعم نماذج Llama و Mixtral بسرعة فائقة

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


class GroqAnalyzer:
    """العقل القانوني الذكي المعتمد على Groq (سريع جداً)."""

    MODEL_NAME = "llama-3.3-70b-versatile"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.groq_api_key
        self._client = None
        self._init_client()

    def _init_client(self):
        if not self.api_key:
            logger.warning("لم يُضبط مفتاح Groq API. المحرك غير جاهز.")
            return
        try:
            from groq import Groq
            self._client = Groq(api_key=self.api_key)
            logger.info("تم تهيئة عميل Groq بنجاح.")
        except Exception as exc:
            logger.error("فشل تهيئة Groq: %s", exc)
            self._client = None

    @property
    def is_ready(self) -> bool:
        return self._client is not None

    def _call_groq(self, prompt: str, temperature: float = 0.3) -> str:
        if not self.is_ready:
            raise RuntimeError("محرك Groq غير جاهز. تحقق من المفتاح.")
        try:
            response = self._client.chat.completions.create(
                model=self.MODEL_NAME,
                messages=[
                    {"role": "system", "content": LegalPrompts.SYSTEM_ROLE},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=2048,
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:
            logger.error("خطأ في استدعاء Groq: %s", exc)
            raise

    @staticmethod
    def _parse_json_response(raw: str) -> Dict[str, Any]:
        cleaned = re.sub(r"```(?:json)?\s*", "", raw)
        cleaned = cleaned.replace("```", "").strip()
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        if start == -1 or end == 0:
            return {}
        try:
            return json.loads(cleaned[start:end])
        except json.JSONDecodeError:
            return {}

    def analyze_clause(
        self,
        clause_number: str,
        clause_text: str,
        strictness: str = None,
    ) -> ClauseRisk:
        strictness = strictness or settings.analysis_strictness
        prompt = LegalPrompts.analysis_prompt(
            clause_text=clause_text,
            clause_number=clause_number,
            strictness=strictness,
            language=settings.report_language,
        )
        try:
            raw = self._call_groq(prompt)
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
            raw = self._call_groq(prompt, temperature=0.4)
            overall = self._parse_json_response(raw)
        except Exception as exc:
            overall = {
                "overall_verdict": "تعذّر التقييم",
                "overall_risk_score": "—",
                "final_recommendation": str(exc),
            }

        return {
            "contract_title": contract_title,
            "clauses_analyzed": len(clause_risks),
            "clause_risks": [c.to_dict() for c in clause_risks],
            "overall_assessment": overall,
        }

    def generate_contract(
        self,
        contract_type: str,
        parties: Dict[str, str],
        terms: Dict[str, Any],
    ) -> str:
        prompt = LegalPrompts.contract_generation_prompt(
            contract_type=contract_type,
            parties=parties,
            terms=terms,
            language=settings.report_language,
        )
        return self._call_groq(prompt, temperature=0.5)
