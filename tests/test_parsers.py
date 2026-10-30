"""
============================================================
اختبارات وحدة محللات العقود
المؤلف: Baran Avisat
============================================================
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.parsers.contract_segmenter import ContractSegmenter
from src.delivery.formatter import ReportFormatter


SAMPLE_CONTRACT = """
المادة 1: التعريفات
يُقصد بـ "الطرف الأول" الشركة الموقّعة على هذا العقد، وبـ "الطرف الثاني" المقاول المستلم للخدمة.

المادة 2: نطاق العمل
يلتزم الطرف الثاني بتقديم خدمات التطوير البرمجي وفقاً للمواصفات المرفقة.

المادة 3: الأتعاب المالية
تُحدد الأتعاب الإجمالية بمبلغ 100,000 دولار، تُدفع على أربع دفعات ربعية.
في حال التأخير في أي دفعة لمدة يوم واحد، يُلزم الطرف الثاني بغرامة قدرها 50% من قيمة الدفعة.

المادة 4: السرية
يلتزم الطرفان بالحفاظ على سرية جميع المعلومات المتبادلة لمدة 5 سنوات بعد انتهاء العقد.

المادة 5: الملكية الفكرية
تنتقل جميع حقوق الملكية الفكرية الناتجة عن هذا العقد تلقائياً للطرف الأول دون أي مقابل إضافي.

المادة 6: الإنهاء
يجوز لأي طرف إنهاء العقد بإشعار خطي مدته 30 يوماً. في حال الإنهاء المبكر من الطرف الثاني، يلتزم بدفع تعويض قدره 200% من قيمة العقد المتبقية.

المادة 7: التحكيم
يُحل أي نزاع عبر التحكيم الإلزامي وفق قوانين دولة الإمارات.
"""


def test_segmenter_arabic():
    """اختبار تقسيم عقد عربي إلى بنود."""
    clauses = ContractSegmenter.segment(SAMPLE_CONTRACT)
    assert len(clauses) >= 5, f"متوقع 5+ بنود، حصلنا على {len(clauses)}"
    print(f"✅ تم استخراج {len(clauses)} بند من العقد العربي")

    # فحص البند الثالث (الأتعاب) - يجب أن يكتشف فيه كلمات خطر
    risk_clauses = [c for c in clauses if c.risk_flags]
    assert len(risk_clauses) >= 3, "متوقع كشف مخاطر في 3+ بنود"
    print(f"✅ تم كشف إشارات خطر في {len(risk_clauses)} بند")

    # طباعة البنود
    for c in clauses:
        flags = ", ".join(c.risk_flags) if c.risk_flags else "لا يوجد"
        print(f"   البند {c.number}: {c.title[:50]}... | خطر: {flags}")


def test_risk_keywords():
    """اختبار كشف الكلمات المفتاحية الخطرة."""
    flags = ContractSegmenter._detect_risk_keywords(
        "هذا البند يتضمن غرامة مالية وشرط سرية وتنازل عن حقوق الملكية الفكرية مع شرط تحكيم إلزامي"
    )
    assert len(flags) >= 3, f"متوقع 3+ إشارات، حصلنا على {flags}"
    print(f"✅ تم كشف {len(flags)} إشارات خطر: {flags}")


def test_formatter_short():
    """اختبار تنسيق الملخص القصير."""
    report = {
        "contract_title": "عقد اختبار",
        "clauses_analyzed": 7,
        "overall_assessment": {
            "overall_verdict": "يحب تعديلات",
            "overall_risk_score": "65",
        },
    }
    summary = ReportFormatter.to_short_summary(report)
    assert "عقد اختبار" in summary
    assert "65" in summary
    print(f"✅ الملخص القصير: {summary}")


def test_formatter_markdown():
    """اختبار تنسيق تقرير Markdown."""
    report = {
        "contract_title": "عقد اختبار",
        "clauses_analyzed": 2,
        "clause_risks": [
            {
                "clause_number": "1",
                "clause_title": "التعريفات",
                "risk_level": "آمن",
                "risk_summary": "بند تعريفي آمن",
                "risk_factors": [],
                "recommendation": "لا حاجة لتعديل",
                "alternative_drafting": "لا حاجة لتعديل",
            },
            {
                "clause_number": "3",
                "clause_title": "الأتعاب",
                "risk_level": "عالية",
                "risk_summary": "غرامة مبالغ فيها",
                "risk_factors": ["غرامة 50%", "لا فترة سماح"],
                "recommendation": "تعديل البند",
                "alternative_drafting": "تطبق الغرامة بعد 5 أيام سماح",
            },
        ],
        "overall_assessment": {
            "overall_verdict": "يحتاج تعديلات جوهرية",
            "overall_risk_score": "65",
            "top_3_risks": ["غرامة مبالغ فيها", "تعويض إنهاء 200%"],
            "negotiation_priorities": ["تعديل غرامة التأخير", "تخفيض تعويض الإنهاء"],
            "final_recommendation": "فاوض على تعديل البنود 3 و 6.",
            "missing_clauses": ["بند القوة القاهرة"],
        },
    }

    md = ReportFormatter.to_markdown_report(report)
    assert "عقد اختبار" in md
    assert "عالية" in md
    assert "غرامة" in md
    print(f"✅ تم توليد تقرير Markdown بطول {len(md)} حرف")


def test_formatter_telegram():
    """اختبار تنسيق رسالة تليجرام."""
    report = {
        "contract_title": "عقد اختبار",
        "clauses_analyzed": 1,
        "clause_risks": [
            {
                "clause_number": "3",
                "risk_level": "عالية",
                "risk_summary": "غرامة مبالغ فيها",
                "recommendation": "عدّل البند",
            }
        ],
        "overall_assessment": {
            "overall_verdict": "يحتاج تعديل",
            "overall_risk_score": "70",
            "top_3_risks": ["غرامة مبالغ فيها"],
            "final_recommendation": "فاوض على التعديل.",
        },
    }

    msg = ReportFormatter.to_telegram_message(report)
    assert "⚖️" in msg
    assert "عقد اختبار" in msg
    assert len(msg) <= 4096
    print(f"✅ رسالة تليجرام بطول {len(msg)} حرف (ضمن الحد)")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 اختبارات Contract-Guard ZeroBaran")
    print("=" * 60)
    print()

    tests = [
        ("تقسيم العقد العربي", test_segmenter_arabic),
        ("كشف الكلمات المفتاحية", test_risk_keywords),
        ("تنسيق الملخص القصير", test_formatter_short),
        ("تنسيق تقرير Markdown", test_formatter_markdown),
        ("تنسيق رسالة تليجرام", test_formatter_telegram),
    ]

    passed = 0
    failed = 0
    for name, test in tests:
        print(f"\n🔍 {name}...")
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ فشل: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"📊 النتيجة: {passed} نجح، {failed} فشل")
    print("=" * 60)
    sys.exit(0 if failed == 0 else 1)
