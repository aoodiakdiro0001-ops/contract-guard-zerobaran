"""
============================================================
محرك استخراج النصوص من ملفات PDF باستخدام PyMuPDF
يقرأ المستند صفحة بصفحة ويحافظ على ترقيم الفقرات

المؤلف: Baran Avisat
============================================================
"""

from pathlib import Path
from typing import List, Dict, Any

import fitz  # PyMuPDF


class PDFParser:
    """محلل ملفات PDF القانونية بدقة عالية."""

    SUPPORTED_EXTENSIONS = {".pdf"}

    @staticmethod
    def can_handle(file_path: Path) -> bool:
        return file_path.suffix.lower() in PDFParser.SUPPORTED_EXTENSIONS

    @staticmethod
    def extract(file_path: str | Path) -> Dict[str, Any]:
        """
        استخراج النص الكامل من ملف PDF.

        Returns:
            قاموس يحتوي على:
            - text: النص الكامل
            - pages: قائمة نصوص الصفحات
            - metadata: البيانات الوصفية للملف
            - page_count: عدد الصفحات
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"الملف غير موجود: {file_path}")

        doc = fitz.open(str(file_path))
        try:
            pages: List[str] = []
            for page in doc:
                pages.append(page.get_text("text"))

            full_text = "\n\n".join(pages)

            metadata = {
                "title": doc.metadata.get("title", "") or file_path.stem,
                "author": doc.metadata.get("author", ""),
                "subject": doc.metadata.get("subject", ""),
                "creator": doc.metadata.get("creator", ""),
                "page_count": doc.page_count,
                "file_size_bytes": file_path.stat().st_size,
                "source_file": file_path.name,
            }

            return {
                "text": full_text,
                "pages": pages,
                "metadata": metadata,
                "page_count": doc.page_count,
            }
        finally:
            doc.close()
