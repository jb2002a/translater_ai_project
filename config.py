"""
OS별 기본 경로 설정.
- Windows: D: 드라이브 → D:\\Pdf\\test.pdf
- macOS: 외장 드라이브 x31 → /Volumes/x31/Pdf/test.pdf
"""
import sys

# Windows D: 드라이브 = Mac에서 외장장치 x31 마운트 경로
if sys.platform == "win32":
    DEFAULT_PDF_PATH = r"D:\Pdf\test.pdf"
else:
    # macOS: 외장 드라이브는 /Volumes/<볼륨이름>/ 아래에 마운트됨
    DEFAULT_PDF_PATH = "/Volumes/x31/Pdf/test.pdf"
