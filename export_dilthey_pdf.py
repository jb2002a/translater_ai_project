"""
Wilhelm Dilthey, Einleitung in die Geisteswissenschaften PDF 내보내기.
프로젝트 루트에서 실행: python export_dilthey_pdf.py
"""
from pathlib import Path

from main.export import DiltheyEinleitungPdfExport

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent
    db_path = project_root / "philosophy_translation.db"
    out_path = project_root / "Dilthey_Einleitung_Geisteswissenschaften.pdf"

    exporter = DiltheyEinleitungPdfExport(str(db_path))
    path = exporter.run(str(out_path))
    print(f"PDF 생성 완료: {path}")
