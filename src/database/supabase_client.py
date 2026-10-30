"""
============================================================
عميل Supabase - طبقة الأرشفة السحابية المجانية
يخزّن العقود المؤرشفة، تقارير المخاطر، وسجلات الاتفاقيات

المؤلف: Baran Avisat
============================================================
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from ..config import settings

logger = logging.getLogger(__name__)


class SupabaseClient:
    """عميل قاعدة بيانات Supabase لأرشفة العقود والتقارير."""

    def __init__(
        self,
        url: Optional[str] = None,
        key: Optional[str] = None,
    ):
        self.url = url or settings.supabase_url
        self.key = key or settings.supabase_key
        self._client = None
        self._init_client()

    def _init_client(self):
        if not self.url or not self.key:
            logger.warning("إعدادات Supabase ناقصة. وضع التخزين المحلي مُفعّل.")
            return
        try:
            from supabase import create_client
            self._client = create_client(self.url, self.key)
            logger.info("تم الاتصال بـ Supabase بنجاح.")
        except Exception as exc:
            logger.error("فشل الاتصال بـ Supabase: %s", exc)
            self._client = None

    @property
    def is_ready(self) -> bool:
        return self._client is not None

    # ===== العقود =====
    def save_contract(
        self,
        title: str,
        source_file: str,
        raw_text: str,
        metadata: Dict[str, Any],
    ) -> Optional[str]:
        """حفظ عقد جديد في قاعدة البيانات."""
        if not self.is_ready:
            logger.warning("Supabase غير جاهز. لم يُحفظ العقد.")
            return None
        payload = {
            "title": title,
            "source_file": source_file,
            "raw_text": raw_text,
            "metadata": json.dumps(metadata, ensure_ascii=False),
            "status": "قيد المراجعة",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            result = self._client.table("contracts").insert(payload).execute()
            if result.data:
                contract_id = result.data[0]["id"]
                logger.info("تم حفظ العقد برقم: %s", contract_id)
                return contract_id
        except Exception as exc:
            logger.error("فشل حفظ العقد: %s", exc)
        return None

    def update_contract_status(
        self,
        contract_id: str,
        status: str,
    ) -> bool:
        """تحديث حالة العقد (مقبولة، تحتاج تعديل، مرفوضة)."""
        if not self.is_ready:
            return False
        try:
            self._client.table("contracts").update({
                "status": status,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }).eq("id", contract_id).execute()
            return True
        except Exception as exc:
            logger.error("فشل تحديث حالة العقد: %s", exc)
            return False

    def list_contracts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """جلب قائمة العقود المؤرشفة."""
        if not self.is_ready:
            return []
        try:
            result = (
                self._client.table("contracts")
                .select("id, title, source_file, status, created_at")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data or []
        except Exception as exc:
            logger.error("فشل جلب قائمة العقود: %s", exc)
            return []

    # ===== تقارير المخاطر =====
    def save_risk_report(
        self,
        contract_id: str,
        report: Dict[str, Any],
    ) -> Optional[str]:
        """حفظ تقرير المخاطر المرتبط بعقد."""
        if not self.is_ready:
            return None
        payload = {
            "contract_id": contract_id,
            "clauses_analyzed": report.get("clauses_analyzed", 0),
            "overall_verdict": report.get("overall_assessment", {}).get(
                "overall_verdict", "غير محدد"
            ),
            "overall_risk_score": report.get("overall_assessment", {}).get(
                "overall_risk_score", "—"
            ),
            "full_report": json.dumps(report, ensure_ascii=False),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            result = (
                self._client.table("risk_reports").insert(payload).execute()
            )
            if result.data:
                return result.data[0]["id"]
        except Exception as exc:
            logger.error("فشل حفظ تقرير المخاطر: %s", exc)
        return None

    def get_risk_report(self, contract_id: str) -> Optional[Dict[str, Any]]:
        """جلب تقرير المخاطر لعقد معين."""
        if not self.is_ready:
            return None
        try:
            result = (
                self._client.table("risk_reports")
                .select("*")
                .eq("contract_id", contract_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            if result.data:
                return result.data[0]
        except Exception as exc:
            logger.error("فشل جلب التقرير: %s", exc)
        return None

    # ===== المواعيد النهائية =====
    def save_deadline(
        self,
        contract_id: str,
        title: str,
        due_date: str,
        description: str = "",
    ) -> Optional[str]:
        """تسجيل موعد نهائي لمراجعة أو تجديد عقد."""
        if not self.is_ready:
            return None
        payload = {
            "contract_id": contract_id,
            "title": title,
            "due_date": due_date,
            "description": description,
            "notified": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            result = (
                self._client.table("deadlines").insert(payload).execute()
            )
            if result.data:
                return result.data[0]["id"]
        except Exception as exc:
            logger.error("فشل تسجيل الموعد النهائي: %s", exc)
        return None

    def get_upcoming_deadlines(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """جلب المواعيد النهائية القادمة خلال N يوماً."""
        if not self.is_ready:
            return []
        try:
            from datetime import timedelta
            now = datetime.now(timezone.utc)
            future = now + timedelta(days=days_ahead)
            result = (
                self._client.table("deadlines")
                .select("id, contract_id, title, due_date, description, notified")
                .gte("due_date", now.isoformat())
                .lte("due_date", future.isoformat())
                .eq("notified", False)
                .execute()
            )
            return result.data or []
        except Exception as exc:
            logger.error("فشل جلب المواعيد: %s", exc)
            return []

    def mark_deadline_notified(self, deadline_id: str) -> bool:
        if not self.is_ready:
            return False
        try:
            self._client.table("deadlines").update({"notified": True}).eq(
                "id", deadline_id
            ).execute()
            return True
        except Exception as exc:
            logger.error("فشل تحديث حالة الإشعار: %s", exc)
            return False
