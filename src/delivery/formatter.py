"""
============================================================
محرّك تنسيق التقارير القانونية
يحوّل ناتج التحليل إلى رسائل منظمة على تليجرام أو نصوص للعرض

المؤلف: Baran Avisat
============================================================
"""

from typing import Dict, Any, List
from datetime import datetime


class ReportFormatter:
    """تنسيق تقارير المخاطر القانونية للعرض."""

    RISK_EMOJI = {
        "عالية": "🔴",
        "متوسطة": "🟠",
        "منخفضة": "🟡",
        "آمن": "🟢",
        "غير محدد": "⚪",
    }

    @classmethod
    def to_telegram_message(cls, report: Dict[str, Any]) -> str:
        """تحويل التقرير إلى رسالة تليجرام منظمة."""
        overall = report.get("overall_assessment", {})
        clauses = report.get("clause_risks", [])
        verdict = overall.get("overall_verdict", "غير محدد")
        score = overall.get("overall_risk_score", "—")
        title = report.get("contract_title", "عقد بدون عنوان")

        lines: List[str] = []
        lines.append("⚖️ ═══════════════════════════")
        lines.append("⚖️ تقرير الفحص القانوني (أوّلي)")
        lines.append("⚖️ ليس استشارة قانونية — راجع محامياً مُرخَّصاً")
        lines.append("⚖️ ═══════════════════════════")
        lines.append(f"📋 العقد: {title}")
        lines.append(f"📊 البنود المحلّلة: {report.get('clauses_analyzed', 0)}")
        lines.append(f"📝 الحكم النهائي: {verdict}")
        lines.append(f"🔢 درجة الخطر: {score} / 100")
        lines.append("")

        # أكبر 3 مخاطر
        top_risks = overall.get("top_3_risks", [])
        if top_risks:
            lines.append("⚠️ أكبر المخاطر المرصودة:")
            for i, risk in enumerate(top_risks, 1):
                lines.append(f"   {i}. {risk}")
            lines.append("")

        # بنود عالية المخاطر
        high_risks = [
            c for c in clauses
            if c.get("risk_level", "").lower() in ("عالية", "high")
        ]
        if high_risks:
            lines.append("🔴 بنود عالية المخاطر:")
            for c in high_risks:
                lines.append(f"   • البند {c.get('clause_number', '?')}: {c.get('risk_summary', '')}")
                rec = c.get("recommendation", "")
                if rec:
                    lines.append(f"     💡 {rec[:200]}")
            lines.append("")

        # أولويات التفاوض
        priorities = overall.get("negotiation_priorities", [])
        if priorities:
            lines.append("🎯 أولويات التفاوض:")
            for i, p in enumerate(priorities, 1):
                lines.append(f"   {i}. {p}")
            lines.append("")

        # التوصية النهائية
        final_rec = overall.get("final_recommendation", "")
        if final_rec:
            lines.append("📌 التوصية النهائية:")
            # تقسيم التوصية إذا كانت طويلة
            for i in range(0, len(final_rec), 800):
                lines.append(final_rec[i:i + 800])
            lines.append("")

        # البنود المفقودة
        missing = overall.get("missing_clauses", [])
        if missing:
            lines.append("📝 بنود مفقودة يُنصح بإضافتها:")
            for m in missing:
                lines.append(f"   • {m}")
            lines.append("")

        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"🕒 تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("🛡️ Contract-Guard ZeroBaran")
        lines.append("👤 المؤلف: Baran Avisat")

        message = "\n".join(lines)

        # تليجرام يحدّ الرسالة بـ 4096 حرفاً
        if len(message) > 4096:
            message = message[:4090] + "\n…[مُختصر]"
        return message

    @classmethod
    def to_markdown_report(cls, report: Dict[str, Any]) -> str:
        """تحويل التقرير إلى تنسيق Markdown كامل."""
        overall = report.get("overall_assessment", {})
        clauses = report.get("clause_risks", [])
        title = report.get("contract_title", "عقد بدون عنوان")

        lines: List[str] = []
        lines.append(f"# ⚖️ تقرير الفحص القانوني: {title}\n")
        lines.append(f"> **تاريخ التقرير:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        lines.append(f"> **المؤلف:** Baran Avisat | Contract-Guard ZeroBaran\n")
        lines.append("> ⚠️ **هذا التقرير فحص أوّلي — ليس استشارة قانونية، ولا يُغني عن رأي محامٍ مُرخَّص.**\n")
        lines.append("---\n")

        lines.append("## 📊 التقييم الشامل\n")
        lines.append(f"- **الحكم النهائي:** {overall.get('overall_verdict', 'غير محدد')}")
        lines.append(f"- **درجة الخطر:** {overall.get('overall_risk_score', '—')} / 100")
        lines.append(f"- **عدد البنود المحلّلة:** {report.get('clauses_analyzed', 0)}\n")

        top_risks = overall.get("top_3_risks", [])
        if top_risks:
            lines.append("### ⚠️ أكبر المخاطر\n")
            for i, r in enumerate(top_risks, 1):
                lines.append(f"{i}. {r}")
            lines.append("")

        lines.append("## 📋 تفصيل البنود\n")
        for c in clauses:
            emoji = cls.RISK_EMOJI.get(
                c.get("risk_level", ""), "⚪"
            )
            lines.append(f"### {emoji} البند {c.get('clause_number', '?')}: {c.get('clause_title', '')}")
            lines.append(f"**مستوى الخطر:** {c.get('risk_level', 'غير محدد')}\n")
            lines.append(f"**الملخص:** {c.get('risk_summary', '')}\n")

            factors = c.get("risk_factors", [])
            if factors:
                lines.append("**عوامل الخطر:**")
                for f in factors:
                    lines.append(f"- {f}")
                lines.append("")

            rec = c.get("recommendation", "")
            if rec:
                lines.append(f"**💡 التوصية:** {rec}\n")

            alt = c.get("alternative_drafting", "")
            if alt and "لا حاجة" not in alt:
                lines.append(f"**✍️ الصياغة البديلة:**\n> {alt}\n")
            lines.append("---\n")

        final_rec = overall.get("final_recommendation", "")
        if final_rec:
            lines.append("## 📌 التوصية النهائية\n")
            lines.append(final_rec)
            lines.append("")

        missing = overall.get("missing_clauses", [])
        if missing:
            lines.append("\n## 📝 بنود مفقودة يُنصح بإضافتها\n")
            for m in missing:
                lines.append(f"- {m}")

        lines.append("\n---")
        lines.append("\n* Contract-Guard ZeroBaran — مؤلف: Baran Avisat | Baranavisat@gmail.com*")
        return "\n".join(lines)

    @classmethod
    def to_short_summary(cls, report: Dict[str, Any]) -> str:
        """ملخص قصير مناسب للإشعارات السريعة."""
        overall = report.get("overall_assessment", {})
        return (
            f"⚖️ {report.get('contract_title', 'عقد')}: "
            f"{overall.get('overall_verdict', 'غير محدد')} "
            f"(الخطر: {overall.get('overall_risk_score', '—')}/100) "
            f"— {report.get('clauses_analyzed', 0)} بند محلّل"
            f" — فحص أوّلي، ليس استشارة قانونية"
        )
