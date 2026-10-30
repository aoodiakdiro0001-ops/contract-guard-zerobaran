"""
طبقة استخراج النصوص القانونية - حزمة المحللات
المؤلف: Baran Avisat
"""

from .pdf_parser import PDFParser
from .docx_parser import DocxParser
from .contract_segmenter import ContractSegmenter

__all__ = ["PDFParser", "DocxParser", "ContractSegmenter"]
