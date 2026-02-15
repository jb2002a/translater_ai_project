import streamlit as st
import os
from dotenv import load_dotenv
from pre_process import PdfToTextConvert as Convert
from pre_process import PreProcessing as PreProcess
import post_process.ToolsForList as ToolsForList
import post_process.Initial_translate as InitialTranslate

# Load environment variables from .env file
load_dotenv()

# 페이지 설정
st.set_page_config(page_title="PDF 번역기", page_icon="📚", layout="wide")

# 타이틀
st.title("📚 PDF 독일어-한국어 번역기")
st.markdown("---")

# 사이드바에서 설정 입력받기
with st.sidebar:
    st.header("⚙️ 설정")

    pdf_path = st.text_input(
        "PDF 파일 경로",
        value="D:\\Pdf\\test.pdf",
        help="변환할 PDF 파일의 전체 경로를 입력하세요",
    )

    col1, col2 = st.columns(2)
    with col1:
        start_page = st.number_input(
            "시작 페이지",
            min_value=0,
            value=20,
            step=1,
            help="0부터 시작하는 페이지 인덱스",
        )
    with col2:
        end_page = st.number_input(
            "종료 페이지",
            min_value=0,
            value=21,
            step=1,
            help="0부터 시작하는 페이지 인덱스",
        )

    st.markdown("---")

    author = st.text_input("저자명", value="Wilhelm Dilthey")

    book_title = st.text_input(
        "책 제목", value="Einleitung in die Geisteswissenschaften"
    )

    st.markdown("---")

    # 변환 시작 버튼
    start_button = st.button(
        "🚀 변환 및 번역 시작", type="primary", use_container_width=True
    )

# 메인 컨텐츠 영역
if start_button:
    if not os.path.exists(pdf_path):
        st.error(f"❌ PDF 파일을 찾을 수 없습니다: {pdf_path}")
    elif start_page > end_page:
        st.error("❌ 시작 페이지가 종료 페이지보다 클 수 없습니다.")
    else:
        try:
            # 프로그레스 바 및 상태 표시
            progress_bar = st.progress(0)
            status_text = st.empty()

            # 1. PDF에서 텍스트 추출
            status_text.text(
                f"📖 PDF 페이지 {start_page}부터 {end_page}까지 텍스트 추출 중..."
            )
            progress_bar.progress(20)

            text = Convert.pdf_to_text(pdf_path, start_page, end_page)

            # 2. 전처리
            status_text.text("🔧 텍스트 전처리 중...")
            progress_bar.progress(40)

            text = PreProcess.pre_process_text(text)

            # 3. 독일어 텍스트 저장
            status_text.text("💾 독일어 텍스트 저장 중...")
            progress_bar.progress(60)

            Convert.generate_text_file_du(text)

            # 4. 번역
            status_text.text("🌐 독일어에서 한국어로 번역 중...")
            progress_bar.progress(70)

            translated_text = InitialTranslate.initial_translate(
                text, author, book_title
            )

            # 5. 한국어 텍스트 저장
            status_text.text("💾 한국어 번역 저장 중...")
            progress_bar.progress(90)

            Convert.generate_text_file_ko(translated_text)

            # 완료
            progress_bar.progress(100)
            status_text.text("✅ 변환 및 번역이 완료되었습니다!")

            st.success("🎉 모든 작업이 성공적으로 완료되었습니다!")

            # 결과 표시
            st.markdown("---")
            st.header("📄 결과")

            # 다운로드 버튼
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📥 독일어 텍스트 다운로드",
                    data=text,
                    file_name="output_du.txt",
                    mime="text/plain",
                )
            with col2:
                st.download_button(
                    label="📥 한국어 번역 다운로드",
                    data=translated_text,
                    file_name="output_ko.txt",
                    mime="text/plain",
                )

            st.markdown("---")

            # ConvertToList를 사용하여 텍스트를 리스트로 변환
            du_list, ko_list = ToolsForList.ConvertToList(text, translated_text)

            # 원문과 번역을 번갈아가며 표시
            st.subheader("📝 원문과 번역")
            for i, (du_sentence, ko_sentence) in enumerate(zip(du_list, ko_list)):
                if (
                    du_sentence.strip() or ko_sentence.strip()
                ):  # 빈 줄이 아닌 경우만 표시
                    with st.container():
                        st.markdown(f"**[{i+1}] 🇩🇪 독일어:**")
                        st.text(du_sentence)
                        st.markdown(f"**[{i+1}] 🇰🇷 한국어:**")
                        st.text(ko_sentence)
                        st.markdown("---")

        except Exception as e:
            st.error(f"❌ 오류가 발생했습니다: {str(e)}")
            st.exception(e)

else:
    # 초기 화면 - 기존 파일이 있으면 표시
    if os.path.exists("output_du.txt") and os.path.exists("output_ko.txt"):
        st.info(
            "💡 이전 번역 결과가 있습니다. 왼쪽 사이드바에서 설정을 조정하고 '변환 및 번역 시작' 버튼을 클릭하세요."
        )

        st.markdown("---")
        st.header("📄 이전 결과")

        # 파일 읽기
        with open("output_du.txt", "r", encoding="utf-8") as f:
            du_text = f.read()
        with open("output_ko.txt", "r", encoding="utf-8") as f:
            ko_text = f.read()

        # 다운로드 버튼
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 독일어 텍스트 다운로드",
                data=du_text,
                file_name="output_du.txt",
                mime="text/plain",
            )
        with col2:
            st.download_button(
                label="📥 한국어 번역 다운로드",
                data=ko_text,
                file_name="output_ko.txt",
                mime="text/plain",
            )

        st.markdown("---")

        # ConvertToList를 사용하여 텍스트를 리스트로 변환
        du_list, ko_list = ToolsForList.ConvertToList(du_text, ko_text)

        # 원문과 번역을 번갈아가며 표시
        st.subheader("📝 원문과 번역")
        for i, (du_sentence, ko_sentence) in enumerate(zip(du_list, ko_list)):
            if du_sentence.strip() or ko_sentence.strip():  # 빈 줄이 아닌 경우만 표시
                with st.container():
                    st.markdown(f"**[{i+1}] 🇩🇪 독일어:**")
                    st.text(du_sentence)
                    st.markdown(f"**[{i+1}] 🇰🇷 한국어:**")
                    st.text(ko_sentence)
                    st.markdown("---")
    else:
        st.info(
            "👈 왼쪽 사이드바에서 PDF 파일 경로와 페이지 범위를 설정하고 '변환 및 번역 시작' 버튼을 클릭하세요."
        )

        # 사용 방법 안내
        with st.expander("📖 사용 방법"):
            st.markdown(
                """
            ### 사용 단계
            1. **PDF 파일 경로 입력**: 번역할 PDF 파일의 전체 경로를 입력합니다.
            2. **페이지 범위 설정**: 시작 페이지와 종료 페이지를 입력합니다 (0부터 시작).
            3. **저자 및 책 제목 입력**: 번역 품질 향상을 위해 저자명과 책 제목을 입력합니다.
            4. **변환 시작**: '변환 및 번역 시작' 버튼을 클릭합니다.
            5. **결과 확인**: 독일어 원문과 한국어 번역을 확인하고 다운로드할 수 있습니다.
            
            ### 참고사항
            - 페이지 인덱스는 0부터 시작합니다 (첫 페이지 = 0).
            - 번역에는 Claude AI를 사용하며, API 키가 .env 파일에 설정되어 있어야 합니다.
            - 변환된 파일은 output_du.txt와 output_ko.txt로 저장됩니다.
            """
            )
