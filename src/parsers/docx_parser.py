"""
============================================================
محرك استخراج النصوص من ملفات Word (.docx) باستخدام python-docx
يحافظ على بنية الفقرات والجداول

المؤلف: Baran Avisat
============================================================
"""

from pathlib import Path
from typing import List, Dict, Any

from docx import Document


class DocxParser:
    """محلل ملفات Word القانونية."""

    SUPPORTED_EXTENSIONS = {".docx", ".doc"}

    @staticmethod
    def can_handle(file_path: Path) -> bool:
        return file_path.suffix.lower() in DocxParser.SUPPORTED_EXTENSIONS

    @staticmethod
    def extract(file_path: str | Path) -> Dict[str, Any]:
        """استخراج النص الكامل من ملف Word مع الجداول."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"الملف غير موجود: {file_path}")

        doc = Document(str(file_path))

        # استخراج الفقرات
        paragraphs: List[str] = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                style = para.style.name.lower() if para.style else ""
                if "heading" in style:
                    paragraphs.append(f"\n## {text}\n")
                else:
                    paragraphs.append(text)

        # استخراج الجداول
        tables_text: List[str] = []
        for table in doc.tables:
            rows = []
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells]
                rows.append(" | ".join(cells))
            if rows:
                tables_text.append("\n[جدول]\n" + "\n".join(rows))

        full_text = "\n\n".join(paragraphs)
        if tables_text:
            full_text += "\n\n" + "\n\n".join(tables_text)

        metadata = {
            "title": file_path.stem,
            "author": "",
            "subject": "",
            "creator": "python-docx",
            "page_count": len(paragraphs),
            "file_size_bytes": file_path.stat().st_size,
            "source_file": file_path.name,
            "tables_count": len(doc.tables),
        }

        return {
            "text": full_text,
            "pages": [full_text],
            "metadata": metadata,
            "page_count": 1,
        }
