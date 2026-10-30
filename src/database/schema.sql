-- ============================================================
-- Contract-Guard ZeroBaran - مخطط قاعدة بيانات Supabase
-- المؤلف: Baran Avisat (Baranavisat@gmail.com)
-- الترخيص: CC BY-NC 4.0
-- ============================================================
-- نفّذ هذا الملف في محرر SQL الخاص بـ Supabase (SQL Editor)
-- لإنشاء الجداول الثلاثة: contracts, risk_reports, deadlines
-- ============================================================

-- ===== 1. جدول العقود =====
CREATE TABLE IF NOT EXISTS public.contracts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title           TEXT NOT NULL,
    source_file     TEXT NOT NULL,
    raw_text        TEXT,
    metadata        JSONB DEFAULT '{}'::jsonb,
    status          TEXT DEFAULT 'قيد المراجعة'
                    CHECK (status IN ('قيد المراجعة', 'مقبولة', 'تحتاج تعديل', 'مرفوضة', 'موقعة')),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE public.contracts IS
'جدول العقود المؤرشفة في نظام Contract-Guard ZeroBaran';

-- ===== 2. جدول تقارير المخاطر =====
CREATE TABLE IF NOT EXISTS public.risk_reports (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id         UUID REFERENCES public.contracts(id) ON DELETE CASCADE,
    clauses_analyzed    INTEGER DEFAULT 0,
    overall_verdict     TEXT,
    overall_risk_score  TEXT,
    full_report         JSONB DEFAULT '{}'::jsonb,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_risk_reports_contract
    ON public.risk_reports(contract_id);

COMMENT ON TABLE public.risk_reports IS
'تقارير المخاطر القانونية المرتبطة بكل عقد';

-- ===== 3. جدول المواعيد النهائية =====
CREATE TABLE IF NOT EXISTS public.deadlines (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id     UUID REFERENCES public.contracts(id) ON DELETE CASCADE,
    title           TEXT NOT NULL,
    due_date        TIMESTAMPTZ NOT NULL,
    description     TEXT,
    notified        BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_deadlines_due_date
    ON public.deadlines(due_date);

CREATE INDEX IF NOT EXISTS idx_deadlines_notified
    ON public.deadlines(notified);

COMMENT ON TABLE public.deadlines IS
'المواعيد النهائية لمراجعة أو تجديد العقود';

-- ===== 4. تفعيل Row Level Security (اختياري للأمان) =====
ALTER TABLE public.contracts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.risk_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.deadlines ENABLE ROW LEVEL SECURITY;

-- السماح بالوصول للمستخدم المُصادَق عليه (أو تعطيل RLS للتطوير)
CREATE POLICY "Public access for development" ON public.contracts
    FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Public access for development" ON public.risk_reports
    FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Public access for development" ON public.deadlines
    FOR ALL USING (true) WITH CHECK (true);

-- ===== 5. دالة تحديث updated_at تلقائياً =====
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_contracts_updated_at ON public.contracts;
CREATE TRIGGER trigger_contracts_updated_at
    BEFORE UPDATE ON public.contracts
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

-- ============================================================
-- ملاحظة: في بيئة الإنتاج، قيّد سياسات RLS على المستخدمين المصرّح لهم فقط.
-- ============================================================
