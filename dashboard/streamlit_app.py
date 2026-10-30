"""
============================================================
لوحة تحكم Contract-Guard ZeroBaran - واجهة ويب تفاعلية
تتيح رفع العقود، عرض التقارير، توليد المسودات، وإدارة الأرشيف

المؤلف: Baran Avisat
============================================================
"""

import sys
import json
import logging
from pathlib import Path

# إضافة جذر المشروع إلى المسار
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st
from src.config import settings
from src.parsers.pdf_parser import PDFParser
from src.parsers.docx_parser import DocxParser
from src.parsers.contract_segmenter import ContractSegmenter
from src.ai.gemini_analyzer import GeminiAnalyzer
from src.ai.groq_analyzer import GroqAnalyzer
from src.database.supabase_client import SupabaseClient
from src.delivery.formatter import ReportFormatter
from src.contract_generator import ContractGenerator

logger = logging.getLogger(__name__)

# ===== إعدادات الصفحة =====
st.set_page_config(
    page_title="Contract-Guard ZeroBaran",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ===== التنسيقات العامة =====
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a237e 0%, #0d47a1 50%, #01579b 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
    }
    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }
    .stat-card {
        background: #f8f9fa;
        padding: 1.2rem;
        border-radius: 10px;
        border-right: 4px solid #1a237e;
        text-align: center;
    }
    .stat-card h3 {
        margin: 0;
        color: #1a237e;
        font-size: 2rem;
    }
    .stat-card p {
        margin: 0.3rem 0 0 0;
        color: #666;
        font-size: 0.9rem;
    }
    .risk-high { color: #d32f2f; font-weight: bold; }
    .risk-medium { color: #f57c00; font-weight: bold; }
    .risk-low { color: #fbc02d; font-weight: bold; }
    .risk-safe { color: #388e3c; font-weight: bold; }
    .footer {
        text-align: center;
        padding: 1.5rem;
        color: #666;
        border-top: 1px solid #eee;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)


# ===== الرأس =====
st.markdown("""
<div class="main-header">
    <h1>🛡️ Contract-Guard ZeroBaran</h1>
    <p>المنظومة الذاتية الذكية لتحليل العقود، كشف المخاطر، وتوليد الاتفاقيات القانونية</p>
    <p style="font-size: 0.85rem; margin-top: 0.5rem;">المؤلف: Baran Avisat | Baranavisat@gmail.com</p>
</div>
""", unsafe_allow_html=True)


# ===== الشريط الجانبي =====
st.sidebar.title("🧭 القائمة الرئيسية")
page = st.sidebar.radio(
    "اختر القسم:",
    [
        "📊 لوحة المعلومات",
        "⚖️ تحليل عقد",
        "📝 توليد مسودة",
        "🗄️ أرشيف العقود",
        "⚙️ الإعدادات",
    ]
)

# حالة الجلسة
if "last_report" not in st.session_state:
    st.session_state.last_report = None


def get_analyzer():
    """الحصول على المحرك النشط."""
    if settings.ai_provider == "gemini" and settings.is_gemini_ready:
        return GeminiAnalyzer()
    if settings.ai_provider == "groq" and settings.is_groq_ready:
        return GroqAnalyzer()
    if settings.is_gemini_ready:
        return GeminiAnalyzer()
    if settings.is_groq_ready:
        return GroqAnalyzer()
    return None


# ============================================================
# الصفحة 1: لوحة المعلومات
# ============================================================
if page == "📊 لوحة المعلومات":
    st.header("📊 لوحة المعلومات")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown('<div class="stat-card"><h3>🟢</h3><p>Gemini API</p></div>', unsafe_allow_html=True)
        st.write("جاهز" if settings.is_gemini_ready else "غير جاهز")
    with col2:
        st.markdown('<div class="stat-card"><h3>⚡</h3><p>Groq API</p></div>', unsafe_allow_html=True)
        st.write("جاهز" if settings.is_groq_ready else "غير جاهز")
    with col3:
        st.markdown('<div class="stat-card"><h3>🗄️</h3><p>Supabase</p></div>', unsafe_allow_html=True)
        st.write("جاهز" if settings.is_supabase_ready else "غير جاهز")
    with col4:
        st.markdown('<div class="stat-card"><h3>📤</h3><p>تليجرام</p></div>', unsafe_allow_html=True)
        st.write("جاهز" if settings.is_telegram_ready else "غير جاهز")

    st.divider()

    st.subheader("📋 حالة النظام التفصيلية")
    st.code(settings.summary(), language="text")

    st.divider()

    st.subheader("📖 عن النظام")
    st.markdown("""
    **Contract-Guard ZeroBaran** هو نظام ذكي متكامل ومستقل لقراءة العقود القانونية
    (NDAs، عقود العمل، اتفاقيات الشراكة، أو شروط الخدمة)، فحص بنودها بدقة لاستخراج
    المخاطر والثغرات الخفية، مقارنتها بالمعايير العادلة، وتوليد مسودات اتفاقيات
    قانونية محكمة.

    ### 🛠️ الموارد المجانية المستخدمة:
    | المكون | التقنية | الدور |
    |--------|---------|------|
    | محرك الجدولة | GitHub Actions | تنفيذ المعالجة المجدولة |
    | استخراج النصوص | PyMuPDF / python-docx | تفكيك المستندات |
    | العقل القانوني | Google Gemini / Groq | تحليل البنود وكشف المخاطر |
    | قاعدة البيانات | Supabase (PostgreSQL) | أرشفة العقود والتقارير |
    | واجهة التسليم | Telegram Bot / Streamlit | الاستلام والتسليم الفوري |
    """)

    st.divider()
    st.subheader("🔐 لماذا هذا النظام؟")
    st.markdown("""
    - **💰 توفير مال فلكي**: لا حاجة لمحامين مدفوعين لكل اتفاقية.
    - **⚠️ كشف مبكر للفخاخ**: يمنع توقيع عقود فيها غرامات خفية أو شروط مجحفة.
    - **🔒 السيادة والسرية**: بياناتك تُعالج في بيئتك الخاصة.
    """)


# ============================================================
# الصفحة 2: تحليل عقد
# ============================================================
elif page == "⚖️ تحليل عقد":
    st.header("⚖️ تحليل عقد قانوني")

    st.markdown("ارفع ملف العقد (PDF أو Word) أو الصق نصه مباشرة لتحليله فوراً.")

    tab1, tab2 = st.tabs(["📁 رفع ملف", "✍️ لصق نص"])

    with tab1:
        uploaded = st.file_uploader(
            "اختر ملف العقد:",
            type=["pdf", "docx"],
            help="الصيغ المدعومة: PDF, DOCX"
        )
        if uploaded is not None:
            # حفظ الملف مؤقتاً
            tmp_path = settings.uploads_dir / uploaded.name
            with open(tmp_path, "wb") as f:
                f.write(uploaded.getbuffer())

            st.success(f"✅ تم استلام الملف: {uploaded.name} ({uploaded.size} بايت)")

            if st.button("🚀 ابدأ التحليل", key="analyze_file"):
                analyzer = get_analyzer()
                if not analyzer:
                    st.error("❌ لا يوجد مزود ذكاء اصطناعي جاهز. تحقق من الإعدادات.")
                else:
                    with st.spinner("⏳ جارٍ التحليل... قد يستغرق دقائق..."):
                        try:
                            # الاستخراج
                            if PDFParser.can_handle(tmp_path):
                                parsed = PDFParser.extract(tmp_path)
                            else:
                                parsed = DocxParser.extract(tmp_path)

                            # التقسيم
                            clauses = ContractSegmenter.segment(parsed["text"])
                            clauses_dicts = ContractSegmenter.to_dict_list(clauses)

                            # التحليل
                            contract_title = parsed["metadata"].get("title", tmp_path.stem)
                            report = analyzer.analyze_contract(
                                contract_title=contract_title,
                                clauses=clauses_dicts,
                            )
                            report["metadata"] = parsed["metadata"]
                            st.session_state.last_report = report

                            # أرشفة
                            if settings.is_supabase_ready:
                                db = SupabaseClient()
                                cid = db.save_contract(
                                    title=contract_title,
                                    source_file=uploaded.name,
                                    raw_text=parsed["text"],
                                    metadata=parsed["metadata"],
                                )
                                if cid:
                                    db.save_risk_report(cid, report)

                            st.success("✅ اكتمل التحليل بنجاح!")
                        except Exception as e:
                            st.error(f"❌ خطأ: {e}")

    with tab2:
        text_input = st.text_area(
            "الصق نص العقد هنا:",
            height=300,
            placeholder="الصق النص الكامل للعقد..."
        )
        if st.button("🚀 حلّل النص", key="analyze_text"):
            if len(text_input.strip()) < 50:
                st.warning("⚠️ النص قصير جداً.")
            else:
                analyzer = get_analyzer()
                if not analyzer:
                    st.error("❌ لا يوجد مزود ذكاء اصطناعي جاهز.")
                else:
                    with st.spinner("⏳ جارٍ التحليل..."):
                        try:
                            clauses = ContractSegmenter.segment(text_input)
                            clauses_dicts = ContractSegmenter.to_dict_list(clauses)
                            report = analyzer.analyze_contract(
                                contract_title="عقد منصوص مباشرة",
                                clauses=clauses_dicts,
                            )
                            st.session_state.last_report = report
                            st.success("✅ اكتمل التحليل!")
                        except Exception as e:
                            st.error(f"❌ خطأ: {e}")

    # عرض التقرير
    if st.session_state.last_report:
        st.divider()
        st.header("📋 تقرير التحليل")
        report = st.session_state.last_report
        overall = report.get("overall_assessment", {})

        col1, col2, col3 = st.columns(3)
        with col1:
            verdict = overall.get("overall_verdict", "غير محدد")
            st.metric("الحكم النهائي", verdict)
        with col2:
            score = overall.get("overall_risk_score", "—")
            st.metric("درجة الخطر", f"{score}/100")
        with col3:
            st.metric("البنود المحلّلة", report.get("clauses_analyzed", 0))

        # أكبر المخاطر
        top_risks = overall.get("top_3_risks", [])
        if top_risks:
            st.subheader("⚠️ أكبر المخاطر المرصودة")
            for i, r in enumerate(top_risks, 1):
                st.markdown(f"**{i}.** {r}")

        # تفصيل البنود
        clauses = report.get("clause_risks", [])
        if clauses:
            st.subheader("📋 تفصيل البنود")
            for c in clauses:
                risk = c.get("risk_level", "")
                if "عال" in risk or "high" in risk.lower():
                    icon = "🔴"
                elif "متوس" in risk or "medium" in risk.lower():
                    icon = "🟠"
                elif "منخف" in risk or "low" in risk.lower():
                    icon = "🟡"
                else:
                    icon = "🟢"

                with st.expander(f"{icon} البند {c.get('clause_number', '?')}: {c.get('clause_title', '')}"):
                    st.markdown(f"**مستوى الخطر:** {risk}")
                    st.markdown(f"**الملخص:** {c.get('risk_summary', '')}")

                    factors = c.get("risk_factors", [])
                    if factors:
                        st.markdown("**عوامل الخطر:**")
                        for f in factors:
                            st.markdown(f"- {f}")

                    rec = c.get("recommendation", "")
                    if rec:
                        st.info(f"💡 التوصية: {rec}")

                    alt = c.get("alternative_drafting", "")
                    if alt and "لا حاجة" not in alt:
                        st.code(alt, language="text")

        # التوصية النهائية
        final = overall.get("final_recommendation", "")
        if final:
            st.subheader("📌 التوصية النهائية")
            st.info(final)

        # بنود مفقودة
        missing = overall.get("missing_clauses", [])
        if missing:
            st.subheader("📝 بنود مفقودة يُنصح بإضافتها")
            for m in missing:
                st.markdown(f"- {m}")

        # تنزيل التقرير
        st.divider()
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            md_report = ReportFormatter.to_markdown_report(report)
            st.download_button(
                "📥 تنزيل التقرير (Markdown)",
                data=md_report.encode("utf-8"),
                file_name="contract_guard_report.md",
                mime="text/markdown",
            )
        with col_dl2:
            json_report = json.dumps(report, ensure_ascii=False, indent=2)
            st.download_button(
                "📥 تنزيل التقرير (JSON)",
                data=json_report.encode("utf-8"),
                file_name="contract_guard_report.json",
                mime="application/json",
            )


# ============================================================
# الصفحة 3: توليد مسودة
# ============================================================
elif page == "📝 توليد مسودة":
    st.header("📝 توليد مسودة اتفاقية قانونية")

    st.markdown("اختر نوع الاتفاقية واملأ البيانات لتوليد مسودة محكمة ومتوازنة.")

    contract_type = st.selectbox(
        "نوع الاتفاقية:",
        list(ContractGenerator.CONTRACT_TYPES.keys()),
        format_func=lambda x: ContractGenerator.CONTRACT_TYPES[x],
    )

    st.subheader("📋 بيانات الأطراف")
    col_a, col_b = st.columns(2)
    with col_a:
        party_a_role = st.text_input("دور الطرف الأول:", value="الطرف الأول")
        party_a_name = st.text_input("اسم الطرف الأول:", placeholder="مثال: شركة الأفق للتقنية")
    with col_b:
        party_b_role = st.text_input("دور الطرف الثاني:", value="الطرف الثاني")
        party_b_name = st.text_input("اسم الطرف الثاني:", placeholder="مثال: مؤسسة النور التجارية")

    st.subheader("📝 الشروط الأساسية")
    terms_text = st.text_area(
        "اكتب الشروط (كل سطر = شرط بالصيغة: المفتاح: القيمة):",
        height=150,
        placeholder="الغرض: تطوير تطبيق ويب\nالمدة: 6 أشهر\nالقيمة: 50,000 دولار\nالتحكيم: محكمة دبي",
    )

    if st.button("✨ توليد المسودة"):
        analyzer = get_analyzer()
        if not analyzer:
            st.error("❌ لا يوجد مزود ذكاء اصطناعي جاهز.")
        elif not party_a_name or not party_b_name:
            st.warning("⚠️ يرجى إدخال أسماء الأطراف.")
        else:
            # بناء قاموس الشروط
            terms = {}
            for line in terms_text.strip().split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    terms[k.strip()] = v.strip()

            parties = {
                party_a_role: party_a_name,
                party_b_role: party_b_name,
            }

            with st.spinner("⏳ جارٍ توليد المسودة..."):
                try:
                    generator = ContractGenerator()
                    draft = generator.generate(
                        contract_type=contract_type,
                        parties=parties,
                        terms=terms,
                    )
                    st.success("✅ تم توليد المسودة بنجاح!")
                    st.text_area(" المسودة القانونية:", value=draft, height=600)

                    st.download_button(
                        "📥 تنزيل المسودة",
                        data=draft.encode("utf-8"),
                        file_name=f"{contract_type}_draft.txt",
                        mime="text/plain",
                    )
                except Exception as e:
                    st.error(f"❌ خطأ: {e}")


# ============================================================
# الصفحة 4: أرشيف العقود
# ============================================================
elif page == "🗄️ أرشيف العقود":
    st.header("🗄️ أرشيف العقود")

    if not settings.is_supabase_ready:
        st.warning("⚠️ Supabase غير مُعد. فعّله لعرض الأرشيف.")
    else:
        db = SupabaseClient()
        contracts = db.list_contracts(limit=100)

        if not contracts:
            st.info("📭 لا توجد عقود مؤرشفة بعد.")
        else:
            st.write(f"**عدد العقود:** {len(contracts)}")
            for c in contracts:
                with st.expander(f"📄 {c.get('title', 'بدون عنوان')} — {c.get('status', '')}"):
                    st.markdown(f"**الملف:** {c.get('source_file', '')}")
                    st.markdown(f"**الحالة:** {c.get('status', '')}")
                    st.markdown(f"**التاريخ:** {c.get('created_at', '')[:19]}")
                    contract_id = c.get("id")

                    # جلب التقرير
                    report = db.get_risk_report(contract_id)
                    if report:
                        st.markdown(f"**الحكم:** {report.get('overall_verdict', '')}")
                        st.markdown(f"**درجة الخطر:** {report.get('overall_risk_score', '')}/100")
                        st.markdown(f"**البنود المحلّلة:** {report.get('clauses_analyzed', 0)}")

                        # تحديث الحالة
                        new_status = st.selectbox(
                            "تحديث الحالة:",
                            ["قيد المراجعة", "مقبولة", "تحتاج تعديل", "مرفوضة", "موقعة"],
                            key=f"status_{contract_id}",
                        )
                        if st.button("💾 حفظ الحالة", key=f"save_{contract_id}"):
                            db.update_contract_status(contract_id, new_status)
                            st.success("✅ تم تحديث الحالة!")
                            st.rerun()


# ============================================================
# الصفحة 5: الإعدادات
# ============================================================
elif page == "⚙️ الإعدادات":
    st.header("⚙️ الإعدادات")

    st.subheader("📊 حالة المزودات")
    st.code(settings.summary(), language="text")

    st.subheader("🔧 متغيرات البيئة المتوقعة")
    st.markdown("""
    أنشئ ملف `.env` في جذر المشروع يحتوي على:

    ```env
    # محرك الذكاء الاصطناعي
    GEMINI_API_KEY=your_key
    GROQ_API_KEY=your_key
    AI_PROVIDER=gemini

    # قاعدة البيانات
    SUPABASE_URL=https://your-project.supabase.co
    SUPABASE_KEY=your_key

    # تليجرام
    TELEGRAM_BOT_TOKEN=your_token
    TELEGRAM_CHAT_ID=your_id

    # عام
    ANALYSIS_STRICTNESS=balanced
    REPORT_LANGUAGE=ar
    ```
    """)

    st.divider()
    st.subheader("🔑 كيفية الحصول على المفاتيح المجانية")
    st.markdown("""
    | الخدمة | رابط الحصول المجاني | الطبقة المجانية |
    |--------|---------------------|-----------------|
    | Google Gemini | [aistudio.google.com](https://aistudio.google.com/app/apikey) | 15 طلب/دقيقة |
    | Groq API | [console.groq.com](https://console.groq.com/keys) | مجانية بسخاء |
    | Supabase | [supabase.com](https://supabase.com) | 500MB قاعدة بيانات |
    | Telegram Bot | [@BotFather](https://t.me/BotFather) | غير محدود |
    """)


# ===== التذييل =====
st.markdown("""
<div class="footer">
    <p>🛡️ <strong>Contract-Guard ZeroBaran</strong> — المنظومة الذاتية الذكية لتحليل العقود</p>
    <p>المؤلف: <strong>Baran Avisat</strong> | 📧 Baranavisat@gmail.com | 📱 +90 531 326 3722</p>
    <p>الترخيص: CC BY-NC 4.0 — للاستخدام التجاري تواصل مع المؤلف</p>
</div>
""", unsafe_allow_html=True)
