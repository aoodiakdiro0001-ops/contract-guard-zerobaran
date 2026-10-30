"""
============================================================
محرك تقسيم العقد إلى بنود وفصول قانونية مستقلة
يستخدم أنماطاً منتظمة لاستخراج كل بند على حدة ليُحلَّل بدقة

المؤلف: Baran Avisat
============================================================
"""

import re
from typing import List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class Clause:
    """بند قانوني واحد."""
    number: str = ""
    title: str = ""
    text: str = ""
    section: str = ""
    index: int = 0
    word_count: int = 0
    risk_flags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "number": self.number,
            "title": self.title,
            "text": self.text,
            "section": self.section,
            "index": self.index,
            "word_count": self.word_count,
            "risk_flags": self.risk_flags,
        }


class ContractSegmenter:
    """يقسم نص العقد الخام إلى بنود قانونية منظمة."""

    # أنماط ترقيم البنود القانونية الشائعة
    PATTERNS = [
        # البند الأول، المادة (4)، Clause 5، Article 3
        r"(?:المادة|البند|الفقرة)\s*[\(\[]?\s*(\d+)\s*[\)\]]?\s*[:\-–]?\s*(.+?)(?=(?:المادة|البند|الفقرة)\s*[\(\[]?\s*\d|$)",
        r"(?:Article|Clause|Section|Paragraph)\s*(\d+)[:\-\.]?\s*(.+?)(?=(?:Article|Clause|Section|Paragraph)\s*\d|$)",
        r"^\s*(\d+)[\.\)\-]\s+(.+?)(?=^\s*\d+[\.\)\-]|\Z)",
        # 4.1.2 نمط هرمي
        r"^(\d+\.\d+(?:\.\d+)?)\s+(.+?)(?=^\d+\.\d+|\Z)",
    ]

    # كلمات مفتاحية للكشف المبدئي عن المخاطر
    RISK_KEYWORDS = {
        "غرامة": "غرامة مالية محتملة",
        "penalty": "غرامة مالية محتملة",
        "تعويض": "التزام تعويضي",
        "indemnif": "التزام تعويضي",
        "حصري": "قيد حصري",
        "exclusive": "قيد حصري",
        "غير قابل للإنهاء": "تقييد الإنهاء",
        "irrevocable": "غير قابل للتراجع",
        "التنازل عن": "تنازل عن حقوق",
        "waive": "تنازل عن حقوق",
        "ملكية فكرية": "حقوق الملكية الفكرية",
        "intellectual property": "حقوق الملكية الفكرية",
        "سرية": "التزام بالسرية",
        "confidential": "التزام بالسرية",
        "تلقائي": "تجديد تلقائي",
        "auto-renew": "تجديد تلقائي",
        "arbitration": "تحكيم إلزامي",
        "تحكيم": "تحكيم إلزامي",
        "non-compete": "منع منافسة",
        "منافسة": "منع منافسة",
    }

    @classmethod
    def segment(cls, text: str) -> List[Clause]:
        """تقسيم نص العقد الكامل إلى بنود مستقلة."""
        if not text or not text.strip():
            return []

        # تنظيف النص
        cleaned = re.sub(r"\r\n", "\n", text)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

        clauses: List[Clause] = []
        current_section = ""
        clause_index = 0

        # محاولة النمط العربي أولاً
        ar_pattern = re.compile(
            r"(?:المادة|البند|الفقرة)\s*[\(\[]?\s*(\d+)\s*[\)\]]?\s*[:\-–]?\s*",
            re.IGNORECASE,
        )
        ar_matches = list(ar_pattern.finditer(cleaned))

        if len(ar_matches) >= 2:
            for i, match in enumerate(ar_matches):
                start = match.end()
                end = ar_matches[i + 1].start() if i + 1 < len(ar_matches) else len(cleaned)
                number = match.group(1)
                clause_text = cleaned[start:end].strip()
                if len(clause_text) < 15:
                    continue

                title = cls._extract_title(clause_text)
                clause_index += 1
                clause = Clause(
                    number=number,
                    title=title,
                    text=clause_text,
                    section=current_section,
                    index=clause_index,
                    word_count=len(clause_text.split()),
                    risk_flags=cls._detect_risk_keywords(clause_text),
                )
                clauses.append(clause)
        else:
            # النمط الرقمي: 1. 2. 3. أو 1) 2) 3)
            num_pattern = re.compile(
                r"(?m)^\s*(\d+)[\.\)\-]\s+(.+?)(?=^\s*\d+[\.\)\-]|\Z)",
                re.DOTALL,
            )
            for i, match in enumerate(num_pattern.finditer(cleaned)):
                number = match.group(1)
                clause_text = match.group(2).strip()
                if len(clause_text) < 15:
                    continue

                title = cls._extract_title(clause_text)
                clause_index += 1
                clause = Clause(
                    number=number,
                    title=title,
                    text=clause_text,
                    section=current_section,
                    index=clause_index,
                    word_count=len(clause_text.split()),
                    risk_flags=cls._detect_risk_keywords(clause_text),
                )
                clauses.append(clause)

        # احتياط: إذا لم يُعثر على بنود، قسّم حسب الفقرات
        if not clauses:
            paragraphs = [p.strip() for p in cleaned.split("\n\n") if p.strip() and len(p.strip()) > 30]
            for i, para in enumerate(paragraphs, 1):
                clause_index += 1
                clauses.append(Clause(
                    number=str(i),
                    title=cls._extract_title(para),
                    text=para,
                    section="",
                    index=clause_index,
                    word_count=len(para.split()),
                    risk_flags=cls._detect_risk_keywords(para),
                ))

        return clauses

    @classmethod
    def _extract_title(cls, text: str) -> str:
        """استخراج عنوان البند من أول سطر أو جملة."""
        first_line = text.split("\n")[0].strip()
        first_sentence = re.split(r"[.؟!\n]", first_line)[0].strip()
        if len(first_sentence) > 80:
            return first_sentence[:80] + "..."
        return first_sentence or "(بند بدون عنوان)"

    @classmethod
    def _detect_risk_keywords(cls, text: str) -> List[str]:
        """كشف أولي للكلمات المفتاحية الخطرة في البند."""
        text_lower = text.lower()
        flags: List[str] = []
        for keyword, label in cls.RISK_KEYWORDS.items():
            if keyword.lower() in text_lower:
                flags.append(label)
        return flags

    @classmethod
    def to_dict_list(cls, clauses: List[Clause]) -> List[Dict[str, Any]]:
        return [c.to_dict() for c in clauses]
