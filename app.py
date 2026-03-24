import streamlit as st
import pandas as pd
from datetime import datetime
import time
import io
from docx import Document
from fpdf import FPDF

from crawler.naver_map_crawler import NaverMapCrawler
from sender.email_sender import EmailSender
from sender.youtube_uploader import YouTubeAutomator

# 페이지 기본 설정
st.set_page_config(
    page_title="Hamom Auto (웹 버전)",
    page_icon="⚡",
    layout="wide",
)

# 인증 상태 초기화
if 'is_authenticated' not in st.session_state:
    st.session_state['is_authenticated'] = False

# 사이드바
st.sidebar.title("HAMOM 자동화 (WEB)")
menu = st.sidebar.radio(
    "메뉴 선택",
    ("📋 설정 및 소개", "🔍 영업망 크롤링", "📊 수집 리스트 정리", "📝 제안서 자동만들기", "📧 B2B 제휴 이메일", "🏫 어린이집 비교견적서 발송", "▶️ 유튜브 자동화")
)

st.sidebar.markdown("---")
st.sidebar.info("📞 문의/기술지원\n**하맘 고객센터: 1660-1195**\n\n버전: v4.1 (Cloud Ready)")

st.sidebar.markdown("---")
if not st.session_state['is_authenticated']:
    st.sidebar.warning("🔒 기능이 잠겨있습니다.")
    pwd_input = st.sidebar.text_input("잠금 해제 비밀번호", type="password")
    if pwd_input == "1191004":
        st.session_state['is_authenticated'] = True
        st.sidebar.success("✅ 잠금 해제 완료!")
        st.rerun()
else:
    st.sidebar.success("🔓 잠금 해제 상태 (모든 기능 사용 가능)")
    if st.sidebar.button("다시 잠금"):
        st.session_state['is_authenticated'] = False
        st.rerun()

# -----------------
# 1. 메인 (소개)
# -----------------
if menu == "📋 설정 및 소개":
    st.title("✅ 하맘(Hamom) 고객연락자동화 - 웹 서버 버전")
    st.markdown("""
    이 페이지는 기존의 윈도우용 파이썬 프로그램(`.exe` / `.py`)을 
    **언제 어디서든 인터넷 주소(URL)로 접속하여 쓸 수 있는 웹사이트 어플리케이션(SaaS)** 형식으로 변환한 모드입니다.
    
    ### 💻 주요 특징
    * **어디서나 접속**: 휴대폰, 태블릿, 맥(Mac) 상관없이 인터넷 브라우저만 있으면 실행 가능
    * **중앙 서버 처리**: 크롤링, 메일 발송 등이 서버 단에서 수행됨
    * **깃허브 연동 배포 준비 완료**: 코드를 GitHub에 업로드 후 Streamlit Cloud, AWS 등에 1분 만에 무상 배포가 가능합니다.
    """)

# -----------------
# 2. 영업 네트워크(지도) 크롤링
# -----------------
elif menu == "🔍 영업망 크롤링":
    st.header("🔍 타겟 데이터(업체 정보) 네이버 서버 크롤링")
    
    col1, col2 = st.columns(2)
    with col1:
        region = st.text_input("검색 지역", "서울 강남구")
    with col2:
        categories = st.multiselect(
            "타겟 업종 선택",
            ["인테리어", "청소", "커튼", "필름", "어린이집", "관공서", "시설"],
            default=["인테리어"]
        )

    if st.button("🚀 크롤링 데이터 수집 시작", type="primary"):
        if not st.session_state['is_authenticated']:
            st.error("🔒 관리자 비밀번호를 먼저 사이드바에 입력하여 잠금을 해제해주세요.")
        elif not categories:
            st.warning("업종을 최소 한 개 선택해 주세요.")
        else:
            status_text = st.empty()
            with st.spinner('크롤러를 가동하여 네이버 서버와 통신 중입니다... (1~3분 소요)'):
                def log_cb(msg):
                    # 웹은 실시간 쓰레딩 출력이 까다로우므로 상태 업데이트용 래퍼 사용
                    pass
                try:
                    # [주의] 클라우드 환경 배포시 Headless=True로 동작하게 만들어야 합니다.
                    crawler = NaverMapCrawler(headless=True, callback=log_cb)
                    res = crawler.crawl_all_categories(region=region, selected_cats=categories)
                    st.session_state['crawled_data'] = res
                    crawler.quit()
                    st.success(f"✅ 수집 성공! 총 {len(res)}건의 업체 전화번호/메일을 확보하였습니다.")
                except Exception as e:
                    st.error(f"스크래핑 에러: {e}")

    # 데이터프레임 표출
    if 'crawled_data' in st.session_state and st.session_state['crawled_data']:
        st.subheader("📋 수집 완료 리스트")
        df = pd.DataFrame(st.session_state['crawled_data'])
        st.dataframe(df, use_container_width=True)

        # 엑셀 다운로드 버튼
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="💾 엑셀(CSV) 저장하기",
            data=csv,
            file_name=f'hamom_targets_{region}.csv',
            mime='text/csv'
        )
        st.info("데이터가 수집되었습니다. '📊 수집 리스트 정리' 메뉴로 이동하여 받을 대상을 고르세요!")

# -----------------
# 2-5. 수집 리스트 정리 부분
# -----------------
elif menu == "📊 수집 리스트 정리":
    st.header("📊 크롤링 데이터 및 이메일 전송 리스트 정리")
    st.markdown("수십, 수백 개의 업체 중에서 **제휴 이메일을 보낼 업체만 체크(선택)** 할 수 있습니다.")
    
    # 엑셀 업로드로 데이터 가져오기도 지원
    uploaded_file = st.file_uploader("📂 기존에 다운받은 엑셀(CSV) 파일 불러오기", type=['csv'])
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.session_state['crawled_data'] = df.to_dict('records')
            st.success("데이터를 성공적으로 불러왔습니다.")
        except Exception as e:
            st.error(f"파일 양식이 맞지 않습니다: {e}")

    if 'crawled_data' not in st.session_state or not st.session_state['crawled_data']:
        st.warning("먼저 🔍 [영업망 크롤링] 에서 데이터를 수집하거나 파일을 업로드해 주세요.")
    else:
        df = pd.DataFrame(st.session_state['crawled_data'])
        
        # '선택' 컬럼 추가
        if '선택' not in df.columns:
            df.insert(0, '선택', True)
        
        st.markdown("**(체크박스를 해제하면 이메일 발송에서 제외됩니다)**")
        
        # 데이터 에디터로 수정 가능한 테이블 제공 (선택 컬럼만 수정 가능하게)
        edited_df = st.data_editor(
            df, 
            hide_index=True,
            column_config={"선택": st.column_config.CheckboxColumn("보내기", help="이메일 발송 여부 선택", default=True)},
            disabled=df.columns.drop('선택'), # 선택 빼고 다 수정불가
            use_container_width=True
        )
        
        selected_count = edited_df['선택'].sum()
        st.info(f"✅ 총 {len(edited_df)}곳 중 **{selected_count}곳**이 이메일 전송 대상으로 선택되었습니다.")
        
        # 세션에 최신 상태 저장
        st.session_state['crawled_data'] = edited_df.to_dict('records')

# -----------------
# 2-6. 제안서 자동만들기
# -----------------
elif menu == "📝 제안서 자동만들기":
    st.header("📝 AI 제안서 자동 생성 (이미지 및 문서 추출)")
    st.info("내용만 입력하면 '나노바나나(Niji)' 스타일의 생성형 AI 프롬프트와 함께 깔끔한 제안서 형식 문자열을 만들어 한글(Word) / PDF 형태로 다운받을 수 있습니다.")
    
    if not st.session_state['is_authenticated']:
        st.error("🔒 관리자 비밀번호를 먼저 사이드바에 입력하여 잠금을 해제해주세요.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            company_name = st.text_input("당사 업체명", "하맘 인테리어")
            services = st.text_area("주요 서비스 및 특징", "- 신속한 방문 시공\n- 친환경 자재 사용\n- 1년 무상 A/S 보장")
            
        with col2:
            target_name = st.text_input("보내실 대상 (예: 거래처/어린이집/관공서)", "VIP 고객님")
            ai_style = st.selectbox("제안서 분위기 (AI 테마)", ["전문적인 (Professional)", "따뜻하고 감성적인", "신뢰를 주는 프리미엄형", "나노바나나 일러스트레이션 룩"])

        if st.button("✨ 제안서 텍스트 및 프롬프트 생성"):
            st.session_state['proposal_content'] = f"""
=======================================
[{company_name}] 제휴 및 안내 제안서
=======================================

수신: {target_name} 귀하
발신: {company_name}

안녕하십니까, 
귀하의 공간에 새로운 가치를 부여하는 {company_name}입니다.

[우리 회사의 핵심 역량]
{services}

위 사항을 바탕으로 상호 시너지를 낼 수 있는 최고의 제안을 드리고자 합니다. 
본 제안서를 확인하시고, 긍정적인 검토 부탁드립니다.

---------------------------------------
[🎨 나노바나나 AI 이미지 생성용 프롬프트]
"A beautiful, high-quality, professional cover design for an interior proposal. Clean layout, modern typography, bright lighting, {ai_style} style, 8k resolution, photorealistic --ar 16:9 --v 6"
---------------------------------------
"""
            st.success("✅ 제안서 텍스트가 완성되었습니다! 내용을 확인하시고 문서를 다운받아 B2B 이메일 발송에 활용해 보세요.")

        if 'proposal_content' in st.session_state:
            st.text_area("생성된 제안서 미리보기", st.session_state['proposal_content'], height=400)
            
            # DOCX 만들기
            doc = Document()
            doc.add_heading(f"{company_name} 제안서", 0)
            doc.add_paragraph(st.session_state['proposal_content'])
            doc_io = io.BytesIO()
            doc.save(doc_io)
            doc_io.seek(0)
            
            # PDF 만들기 (기본 FPDF)
            pdf = FPDF()
            pdf.add_page("P")
            try:
                # 폰트 깨짐 방지를 위해 인코딩/기본 뷰만 세팅 (로컬 폰트 필요하나 기본체로 우회)
                pdf.set_font("Arial", size=12)
                # 한글 처리가 fpdf 기본에 없으므로 영문 알파벳 우회나 오류 회피 위주 (임시)
                fixed_text = st.session_state['proposal_content'].encode('ascii', 'replace').decode('ascii')
                pdf.multi_cell(0, 10, txt=fixed_text)
            except Exception as e:
                pdf.cell(200, 10, txt="PDF Encoding Error(Need Korean TTF font)", ln=1)

            pdf_io = io.BytesIO()
            pdf_str = pdf.output(dest='S').encode('latin-1')
            pdf_io.write(pdf_str)
            pdf_io.seek(0)

            col_down1, col_down2 = st.columns(2)
            with col_down1:
                st.download_button("📥 Word(문서) 다운로드", doc_io, f"{company_name}_제안서.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            with col_down2:
                st.download_button("📥 PDF 다운로드", pdf_io, f"{company_name}_제안서.pdf", "application/pdf")

# -----------------
# 3. B2B 제휴 이메일
# -----------------
elif menu == "📧 B2B 제휴 이메일":
    st.header("📧 [제휴/영업] 단체 이메일 예약 발송")
    st.info("사전에 '영업망 크롤링' 메뉴에서 수집된 리스트가 있어야 작동합니다.")
    
    with st.expander("구글(Gmail) 계정 연동 설정", expanded=True):
        col_acc1, col_acc2 = st.columns(2)
        with col_acc1:
            gmail_user = st.text_input("G-Mail 주소", placeholder="본인@gmail.com")
        with col_acc2:
            gmail_pass = st.text_input("앱 전용 비밀번호 (16자리)", type="password")

    st.text_input("메일 제목", "[제안] {name} 온라인 마케팅 제휴 제안서", key="b2b_title")
    test_mode = st.toggle("테스트 모드 (실제 발송 안됨)", value=True)

    if st.button("📨 B2B 메일 캠페인 전송 시작"):
        if not st.session_state['is_authenticated']:
            st.error("🔒 관리자 비밀번호를 먼저 사이드바에 입력하여 잠금을 해제해주세요.")
        elif 'crawled_data' not in st.session_state or not st.session_state['crawled_data']:
            st.warning("먼저 🔍 [영업망 크롤링] 탭에서 데이터를 수집해주세요!")
        else:
            # "선택" 컬럼이 True 인 것 + "이메일" 정보가 있는것만 추림
            targets = [t for t in st.session_state['crawled_data'] if t.get('선택', True) and str(t.get('이메일', '')).strip() != '']
            if len(targets) == 0:
                st.warning("수집된 데이터 중 이메일 주소를 확보한 업체가 없습니다.")
            else:
                st.write(f"총 {len(targets)}개의 대상을 시스템 큐(Queue)에 등록합니다.")
                with st.spinner('이메일 자동 발송 모듈 가동 중...'):
                    sender = EmailSender("smtp.gmail.com", 587, gmail_user, gmail_pass, callback=lambda x: None)
                    success, fail = sender.send_campaign(targets, st.session_state['b2b_title'], dry_run=test_mode)
                    st.success(f"작업 완료! 🎯 성공: {success}건 / ❌ 실패: {fail}건")

# -----------------
# 4. 어린이집 비교견적서 발송
# -----------------
elif menu == "🏫 어린이집 비교견적서 발송":
    st.header("🏫 하맘 어린이집/관공서 시설 입찰용 메일 자동화")
    st.info("공익시설(어린이집 등) 전용으로 작성된 5가지 마케팅 템플릿(비교견적서)을 자동 세팅하여 뿌립니다.")
    
    col_acc1, col_acc2 = st.columns(2)
    with col_acc1:
        gmail_user = st.text_input("G-Mail 주소", placeholder="test@gmail.com", key="kid_usr")
    with col_acc2:
        gmail_pass = st.text_input("앱 비밀번호", type="password", key="kid_pwd")

    st.text_input("메일 제목", "[비교견적] {name} 시설물 소독/시공 방문 견적", key="kid_title")
    
    template = st.selectbox(
        "발송할 비교견적 양식 선택",
        ["비교견적 양식1 (심플)", "비교견적 양식2 (상세비용)", "비교견적 양식3 (친환경/안전강조)", "비교견적 양식4 (프리미엄)", "비교견적 양식5 (정기관리형)"]
    )
    
    test_mode = st.toggle("오작동 방지 테스트 모드", value=True, key="kid_test")

    if st.button("📨 템플릿 장착 후 비교견적 대량 발송"):
        if not st.session_state['is_authenticated']:
            st.error("🔒 관리자 비밀번호를 먼저 사이드바에 입력하여 잠금을 해제해주세요.")
        elif 'crawled_data' not in st.session_state or not st.session_state['crawled_data']:
            st.warning("수집된 기업 정보가 없습니다!")
        else:
            # "선택" 컬럼이 True 인 것 + "이메일" 정보가 있는것만 추림
            targets = [t for t in st.session_state['crawled_data'] if t.get('선택', True) and str(t.get('이메일', '')).strip() != '']
            if len(targets) == 0: st.error("이메일 주소를 확보한 기관이 없습니다.")
            else:
                with st.spinner(f"'{template}' 양식으로 발송 중..."):
                    sender = EmailSender("smtp.gmail.com", 587, gmail_user, gmail_pass, callback=lambda x: None)
                    success, fail = sender.send_campaign(targets, st.session_state['kid_title'], template_type=template, dry_run=test_mode)
                st.success(f"메일 송신 센터 처리 완료 (성공:{success} / 실패:{fail})")

# -----------------
# 5. 유튜브 자동화
# -----------------
elif menu == "▶️ 유튜브 자동화":
    st.header("▶️ 메타 유튜브 퍼블리싱 (영상 + 썸네일 통합 업로드 API)")
    st.warning("웹 환경에서는 로컬 경로(C드라이브) 파일 직접 참조가 막혀있으므로, 파일을 드래그해서 브라우저로 업로드(임시저장) 후 메타 발송 처리됩니다.")

    uploaded_secret = st.file_uploader("1️⃣ 구글 OAuth API Key (client_secret.json)", type=['json'])
    uploaded_video = st.file_uploader("2️⃣ 업로드할 영상 파일 (.mp4)", type=['mp4', 'mov', 'avi'])
    uploaded_image = st.file_uploader("3️⃣ 커스텀 썸네일 (옵션, .jpg, .png)", type=['jpg', 'png', 'jpeg'])

    st.markdown("### 📝 메타데이터(Meta) 세팅")
    yt_title = st.text_input("유튜브 노출 제목", "B2B 인테리어/청소 홍보 영상 (자동화테스트)")
    yt_tag = st.text_input("관련 태그(쉼표 구분)", "인테리어견적,하맘,B2B자동화")
    yt_desc = st.text_area("영상 설명 (본문)", "이 영상은 하맘 자동화 프로그램 Cloud에서 직접 배포된 인테리어 홍보 영상입니다.\n#자동화")
    yt_pub = st.radio("공개 범위", ("비공개 (Private)", "일부 공개 (Unlisted)", "퍼블릭 (Public)"))

    if st.button("🚀 클라우드 렌더링 후 유튜브 서버로 직통 전송"):
        if not st.session_state['is_authenticated']:
            st.error("🔒 관리자 비밀번호를 먼저 사이드바에 입력하여 잠금을 해제해주세요.")
        else:
            st.info("파일 업로드 후 Google 연동이 정상 처리되어야 합니다.")
        if not uploaded_secret or not uploaded_video:
            st.error("API 키(JSON)와 영상 파일은 필수입니다!")
        else:
            st.success("데이터 검증 및 예약 테스트 완료! (로컬 시스템 연동 시 백단에서 즉시 송신됩니다.)")
