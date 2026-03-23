"""
하맘 고객연락자동화 - 메인 GUI
업체 크롤링, 업체 제안 이메일 발송, 어린이집 비교견적 이메일 발송 통합 솔루션
"""

import sys
import threading
import queue
import datetime
from pathlib import Path
import pandas as pd

import customtkinter as ctk
from tkinter import messagebox, filedialog

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class HamomAutoContactApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("하맘 고객연락자동화 (Hamom Contact Automation)")
        self.geometry("1400x900")
        self.minsize(1200, 800)
        
        self.log_queue = queue.Queue()
        self.crawl_results = [] # [{'업체명':'...', '전화번호':'...', '이메일':'...', '주소':'...'}, ...]
        self.ig_results = []
        
        # 선택된 데이터 추적용
        self.email_b2b_selections = {}
        self.email_kids_selections = {}

        self._build_sidebar()
        self._build_main_frame()
        self._process_log_queue()
        
        self.select_tab("크롤링")

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        logo_label = ctk.CTkLabel(
            self.sidebar, 
            text="HAMOM\nAutomation", 
            font=ctk.CTkFont(family="Malgun Gothic", size=26, weight="bold"),
            text_color="#58a6ff"
        )
        logo_label.pack(pady=(30, 30))
        
        self.tab_buttons = {}
        tabs = [
            ("크롤링", "📋 동종업체 크롤링"),
            ("업체이메일", "📧 업체 제안 이메일 발송"),
            ("어린이집이메일", "🏫 어린이집 비교견적 이메일 발송"),
            ("문자", "💬 고객 문자 발송"),
            ("인스타", "📸 셀럽 인스타 DM"),
            ("유튜브", "▶️ 유튜브 자동 영상 업로드"),
            ("설정", "⚙️ 기본 설정")
        ]
        
        for key, text in tabs:
            btn = ctk.CTkButton(
                self.sidebar, 
                text=text,
                font=ctk.CTkFont(family="Malgun Gothic", size=15),
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                anchor="w",
                height=40,
                command=lambda k=key: self.select_tab(k)
            )
            btn.pack(fill="x", padx=10, pady=5)
            self.tab_buttons[key] = btn
            
        version_label = ctk.CTkLabel(
            self.sidebar, 
            text="v3.0.0\nPowered by Hamom",
            font=ctk.CTkFont(family="Malgun Gothic", size=11),
            text_color="gray50"
        )
        version_label.pack(side="bottom", pady=20)

    def _build_main_frame(self):
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        
        self.frames = {}
        self.frames["크롤링"] = self._create_crawl_frame()
        self.frames["업체이메일"] = self._create_b2b_email_frame()
        self.frames["어린이집이메일"] = self._create_kids_email_frame()
        self.frames["문자"] = self._create_sms_frame()
        self.frames["인스타"] = self._create_ig_frame()
        self.frames["유튜브"] = self._create_youtube_frame()
        self.frames["설정"] = self._create_settings_frame()

    def select_tab(self, tab_key):
        for key, frame in self.frames.items():
            frame.pack_forget()
            btn = self.tab_buttons[key]
            btn.configure(fg_color="transparent" if key != tab_key else ("gray75", "gray25"))
        self.frames[tab_key].pack(fill="both", expand=True)

    # ----------------------------------------------------
    # 탭 1: 업체 크롤링
    # ----------------------------------------------------
    def _create_crawl_frame(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header = ctk.CTkLabel(frame, text="📋 동종업체 크롤링 (B2B 영업용 수집)", font=ctk.CTkFont(family="Malgun Gothic", size=22, weight="bold"))
        header.pack(anchor="w", pady=(0, 20))
        
        ctrl = ctk.CTkFrame(frame)
        ctrl.pack(fill="x", pady=(0, 15))
        
        region_frm = ctk.CTkFrame(ctrl, fg_color="transparent")
        region_frm.pack(side="left", padx=15, pady=15)
        ctk.CTkLabel(region_frm, text="검색 지역:", font=ctk.CTkFont(weight="bold", size=14)).pack(side="left", padx=(0, 10))
        self.crawl_region = ctk.CTkEntry(region_frm, placeholder_text="예: 서울 강남구", width=140, height=35)
        self.crawl_region.pack(side="left")
        
        cat_frm = ctk.CTkFrame(ctrl, fg_color="transparent")
        cat_frm.pack(side="left", padx=(5,15), pady=15)
        ctk.CTkLabel(cat_frm, text="업종:", font=ctk.CTkFont(weight="bold", size=14)).pack(side="left", padx=(0, 10))
        
        self.cat_vars = {}
        categories = ["인테리어", "청소", "커튼", "필름", "어린이집", "관공서", "시설"]
        
        # 2줄로 배치
        check_wrap1 = ctk.CTkFrame(cat_frm, fg_color="transparent")
        check_wrap1.pack(fill="x")
        check_wrap2 = ctk.CTkFrame(cat_frm, fg_color="transparent")
        check_wrap2.pack(fill="x")
        
        for i, cat in enumerate(categories):
            var = ctk.StringVar(value=cat)
            parent = check_wrap1 if i < 4 else check_wrap2
            chk = ctk.CTkCheckBox(parent, text=cat, variable=var, onvalue=cat, offvalue="")
            chk.pack(side="left", padx=5, pady=5)
            self.cat_vars[cat] = var
            
        btn_frm = ctk.CTkFrame(ctrl, fg_color="transparent")
        btn_frm.pack(side="right", padx=15, pady=15)
        
        ctk.CTkButton(btn_frm, text="▶ 크롤링 시작", fg_color="#238636", hover_color="#2ea043", height=40, font=ctk.CTkFont(size=14, weight="bold"), command=self._start_crawl, width=130).pack(side="left", padx=5)
        ctk.CTkButton(btn_frm, text="💾 엑셀 저장", command=self._save_crawl_excel, height=35, width=100).pack(side="left", padx=5)
        ctk.CTkButton(btn_frm, text="📂 엑셀 로드", fg_color="gray40", hover_color="gray50", height=35, command=self._load_excel, width=100).pack(side="left", padx=5)

        self.crawl_log = ctk.CTkTextbox(frame, font=ctk.CTkFont(family="Consolas", size=13), fg_color="#0d1117", text_color="#57e389")
        self.crawl_log.pack(side="top", fill="both", expand=True, pady=(0, 10))
        
        self.crawl_info = ctk.CTkLabel(frame, text="✅ 수집 대기 중", text_color="#3fb950", font=ctk.CTkFont(weight="bold", size=14))
        self.crawl_info.pack(side="bottom", anchor="e")
        
        return frame

    # ----------------------------------------------------
    # 공통: 이메일 보낼 목록(체크박스 리스트) 렌더링 함수
    # ----------------------------------------------------
    def _refresh_email_list(self, scroll_frame, selection_dict):
        # 기존 위젯 지우기
        for widget in scroll_frame.winfo_children():
            widget.destroy()
            
        selection_dict.clear()
        
        targets = [r for r in self.crawl_results if r.get("이메일")]
        if not targets:
            ctk.CTkLabel(scroll_frame, text="💡 크롤링된 데이터 중 '이메일' 정보가 있는 업체가 없습니다.", font=ctk.CTkFont(size=14)).pack(pady=40)
            return

        # 전체 선택 기능용 최상단 프레임
        hdr = ctk.CTkFrame(scroll_frame, corner_radius=5, fg_color="gray20", height=40)
        hdr.pack(fill="x", pady=(0,10))
        hdr.pack_propagate(False)
        
        ctk.CTkLabel(hdr, text="선택", width=50, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10, pady=10)
        ctk.CTkLabel(hdr, text="업체명", width=250, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkLabel(hdr, text="카테고리", width=120, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkLabel(hdr, text="이메일", width=250, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkLabel(hdr, text="전화번호", width=150, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left")

        # 업체 목록
        for i, t in enumerate(targets):
            row_color = "transparent" if i % 2 == 0 else "gray15"
            row = ctk.CTkFrame(scroll_frame, fg_color=row_color)
            row.pack(fill="x", pady=2)
            
            var = ctk.BooleanVar(value=True) # 기본 선택됨
            chk = ctk.CTkCheckBox(row, text="", variable=var, width=50, checkbox_width=20, checkbox_height=20)
            chk.pack(side="left", padx=10)
            
            name = t.get("업체명", "")
            if len(name) > 20: name = name[:20] + "..."
            ctk.CTkLabel(row, text=name, width=250, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=t.get("검색카테고리", ""), width=120, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=t.get("이메일", ""), width=250, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=t.get("전화번호", ""), width=150, anchor="w").pack(side="left")
            
            selection_dict[t.get("이메일")] = {"data": t, "var": var}

    def _get_selected_targets(self, selection_dict):
        res = []
        for email, info in selection_dict.items():
            if info["var"].get():
                res.append(info["data"])
        return res

    # ----------------------------------------------------
    # 탭 2: 업체 제안 이메일 발송
    # ----------------------------------------------------
    def _create_b2b_email_frame(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header = ctk.CTkLabel(frame, text="📧 업체 제안 이메일 발송 (B2B 제휴)", font=ctk.CTkFont(family="Malgun Gothic", size=22, weight="bold"))
        header.pack(anchor="w", pady=(0, 20))
        
        content = ctk.CTkFrame(frame, fg_color="transparent")
        content.pack(fill="both", expand=True)
        
        left = ctk.CTkFrame(content, width=350, corner_radius=8)
        left.pack(side="left", fill="y", padx=(0, 15))
        left.pack_propagate(False)
        
        top_lbl = ctk.CTkLabel(left, text="[ 메일 계정 설정 ]", font=ctk.CTkFont(weight="bold"))
        top_lbl.pack(pady=(15, 5))
        
        self._add_label(left, "발신 이메일 (Gmail)")
        self.b2b_email = ctk.CTkEntry(left, placeholder_text="your@gmail.com", height=35)
        self.b2b_email.pack(fill="x", padx=20, pady=(0, 15))
        
        self._add_label(left, "앱 비밀번호 (16자리)")
        self.b2b_pwd = ctk.CTkEntry(left, show="*", height=35)
        self.b2b_pwd.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkFrame(left, height=2, fg_color="gray30").pack(fill="x", padx=20, pady=10)
        
        self._add_label(left, "이메일 제목 형식")
        self.b2b_title = ctk.CTkEntry(left, height=35)
        self.b2b_title.insert(0, "[제안] {name} 디지털 마케팅 파트너십")
        self.b2b_title.pack(fill="x", padx=20, pady=(0, 15))
        
        self.b2b_dryrun = ctk.StringVar(value="TEST")
        ctk.CTkCheckBox(left, text="테스트 모드 (실제 발송 안 됨)", variable=self.b2b_dryrun, onvalue="TEST", offvalue="REAL").pack(anchor="w", padx=20, pady=15)
        
        ctk.CTkButton(left, text="📨 발송 시작", fg_color="#238636", hover_color="#2ea043", height=45, font=ctk.CTkFont(size=15, weight="bold"), command=self._start_b2b_email).pack(fill="x", padx=20, pady=20)
        
        self.b2b_info = ctk.CTkLabel(left, text="대기중", text_color="#3fb950", font=ctk.CTkFont(size=13, weight="bold"))
        self.b2b_info.pack()

        right = ctk.CTkFrame(content, corner_radius=8)
        right.pack(side="right", fill="both", expand=True)
        
        top_ctrl = ctk.CTkFrame(right, fg_color="transparent")
        top_ctrl.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(top_ctrl, text="✨ 전송 대상 선택 (클릭하여 체크 해제 가능)", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        ctk.CTkButton(top_ctrl, text="🔄 목록 감지(새로고침)", width=120, fg_color="#1f6feb", command=lambda: self._refresh_email_list(self.b2b_scroll, self.email_b2b_selections)).pack(side="right")
        
        self.b2b_scroll = ctk.CTkScrollableFrame(right, corner_radius=0)
        self.b2b_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        return frame

    # ----------------------------------------------------
    # 탭 3: 어린이집 비교견적 이메일 발송 
    # ----------------------------------------------------
    def _create_kids_email_frame(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header = ctk.CTkLabel(frame, text="🏫 어린이집 비교견적 이메일 발송", font=ctk.CTkFont(family="Malgun Gothic", size=22, weight="bold"))
        header.pack(anchor="w", pady=(0, 20))
        
        content = ctk.CTkFrame(frame, fg_color="transparent")
        content.pack(fill="both", expand=True)
        
        left = ctk.CTkFrame(content, width=350, corner_radius=8)
        left.pack(side="left", fill="y", padx=(0, 15))
        left.pack_propagate(False)
        
        top_lbl = ctk.CTkLabel(left, text="[ 메일 계정 설정 ]", font=ctk.CTkFont(weight="bold"))
        top_lbl.pack(pady=(15, 5))
        
        self._add_label(left, "발신 이메일 (Gmail)")
        self.kid_email = ctk.CTkEntry(left, placeholder_text="your@gmail.com", height=35)
        self.kid_email.pack(fill="x", padx=20, pady=(0, 10))
        self._add_label(left, "앱 비밀번호")
        self.kid_pwd = ctk.CTkEntry(left, show="*", height=35)
        self.kid_pwd.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkFrame(left, height=2, fg_color="gray30").pack(fill="x", padx=20, pady=10)
        
        self._add_label(left, "이메일 제목")
        self.kid_title = ctk.CTkEntry(left, height=35)
        self.kid_title.insert(0, "[비교견적] {name} 시설관리/청소 제안")
        self.kid_title.pack(fill="x", padx=20, pady=(0, 15))

        self._add_label(left, "비교견적 양식 (템플릿 5종)")
        self.kid_template = ctk.CTkOptionMenu(left, height=35, dropdown_font=ctk.CTkFont(size=13), values=[
            "비교견적 양식1 (심플)", 
            "비교견적 양식2 (상세비용)", 
            "비교견적 양식3 (친환경/안전강조)", 
            "비교견적 양식4 (프리미엄)",
            "비교견적 양식5 (정기관리형)"
        ])
        self.kid_template.pack(fill="x", padx=20, pady=(0, 15))

        self.kid_dryrun = ctk.StringVar(value="TEST")
        ctk.CTkCheckBox(left, text="테스트 모드 (실제 발송 안 됨)", variable=self.kid_dryrun, onvalue="TEST", offvalue="REAL").pack(anchor="w", padx=20, pady=15)
        
        ctk.CTkButton(left, text="📨 비교견적 발송 시작", fg_color="#1f6feb", height=45, font=ctk.CTkFont(size=15, weight="bold"), command=self._start_kids_email).pack(fill="x", padx=20, pady=15)
        
        self.kid_info = ctk.CTkLabel(left, text="대기중", text_color="#1f6feb", font=ctk.CTkFont(size=13, weight="bold"))
        self.kid_info.pack()

        # 우측 목록
        right = ctk.CTkFrame(content, corner_radius=8)
        right.pack(side="right", fill="both", expand=True)
        
        top_ctrl = ctk.CTkFrame(right, fg_color="transparent")
        top_ctrl.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(top_ctrl, text="✨ 전송 대상 선택 (어린이집 등)", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        ctk.CTkButton(top_ctrl, text="🔄 목록 감지(새로고침)", width=120, fg_color="#1f6feb", command=lambda: self._refresh_email_list(self.kid_scroll, self.email_kids_selections)).pack(side="right")
        
        self.kid_scroll = ctk.CTkScrollableFrame(right, corner_radius=0)
        self.kid_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        return frame

    # ----------------------------------------------------
    # 탭 4: 문자 발송
    # ----------------------------------------------------
    def _create_sms_frame(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        ctk.CTkLabel(frame, text="💬 고객 문자 발송 (SMS API 연동)", font=ctk.CTkFont(family="Malgun Gothic", size=22, weight="bold")).pack(anchor="w", pady=(0, 20))
        ctk.CTkLabel(frame, text="API 인프라 연결 및 문자 전송용 탭 구성 예정입니다.", font=ctk.CTkFont(size=14)).pack(pady=40)
        return frame

    # ----------------------------------------------------
    # 탭 5: 인스타
    # ----------------------------------------------------
    def _create_ig_frame(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        ctk.CTkLabel(frame, text="📸 셀럽 인스타 DM", font=ctk.CTkFont(family="Malgun Gothic", size=22, weight="bold")).pack(anchor="w", pady=(0, 20))
        ctk.CTkLabel(frame, text="공동구매 진행 등 DM 발송 기능 구성 예정입니다.", font=ctk.CTkFont(size=14)).pack(pady=40)
        return frame

    # ----------------------------------------------------
    # 탭 6: 유튜브 자동 업로드 
    # ----------------------------------------------------
    def _create_youtube_frame(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header = ctk.CTkLabel(frame, text="▶️ 유튜브 이미지/배너/영상 메타 자동화 업로더", font=ctk.CTkFont(family="Malgun Gothic", size=22, weight="bold"))
        header.pack(anchor="w", pady=(0, 20))
        
        content = ctk.CTkFrame(frame, fg_color="transparent")
        content.pack(fill="both", expand=True)

        left = ctk.CTkFrame(content, width=400, corner_radius=8)
        left.pack(side="left", fill="y", padx=(0, 15))
        left.pack_propagate(False)

        top_lbl = ctk.CTkLabel(left, text="[ 영상 및 메타데이터 기본정보 ]", font=ctk.CTkFont(weight="bold"))
        top_lbl.pack(pady=(15, 10))

        # 파일 선택창
        self.yt_video_path = ctk.StringVar(value="")
        self.yt_thumb_path = ctk.StringVar(value="")
        self.yt_secret_path = ctk.StringVar(value="")

        def slct_vid(): self.yt_video_path.set(filedialog.askopenfilename(title="영상", filetypes=[("Video", "*.mp4 *.mov *.avi")]))
        def slct_thmb(): self.yt_thumb_path.set(filedialog.askopenfilename(title="썸네일", filetypes=[("Image", "*.jpg *.png *.jpeg")]))
        def slct_sec(): self.yt_secret_path.set(filedialog.askopenfilename(title="유튜브 OAuth JSON키", filetypes=[("JSON", "*.json")]))

        file_frm = ctk.CTkFrame(left, fg_color="transparent")
        file_frm.pack(fill="x", padx=10)
        
        ctk.CTkButton(file_frm, text="📂 자동화 인증키 (구글 client_secret.json)", fg_color="#444", height=30, command=slct_sec).pack(fill="x", pady=5)
        ctk.CTkLabel(file_frm, textvariable=self.yt_secret_path, font=ctk.CTkFont(size=10)).pack()
        
        ctk.CTkButton(file_frm, text="📂 영상 파일 선택 (MP4 등)", height=30, fg_color="#c4302b", hover_color="#8b0000", command=slct_vid).pack(fill="x", pady=5)
        ctk.CTkLabel(file_frm, textvariable=self.yt_video_path, font=ctk.CTkFont(size=10)).pack()
        
        ctk.CTkButton(file_frm, text="🖼️ 커스텀 썸네일 이미지 선택 (리디자인)", height=30, fg_color="#d68400", hover_color="#aa6600", command=slct_thmb).pack(fill="x", pady=5)
        ctk.CTkLabel(file_frm, textvariable=self.yt_thumb_path, font=ctk.CTkFont(size=10)).pack()

        # 메타 작성
        self._add_label(left, "유튜브 제목")
        self.yt_title = ctk.CTkEntry(left, height=35)
        self.yt_title.insert(0, "[자동화] 유튜브 홍보 메타영상")
        self.yt_title.pack(fill="x", padx=15, pady=(0, 10))

        self._add_label(left, "관련 태그 (쉽표 구분)")
        self.yt_tags = ctk.CTkEntry(left, height=35)
        self.yt_tags.insert(0, "메타,디자인,유튜브자동화,홍보")
        self.yt_tags.pack(fill="x", padx=15, pady=(0, 10))

        self._add_label(left, "설명 (메타데이터)")
        self.yt_desc = ctk.CTkTextbox(left, height=120)
        self.yt_desc.pack(fill="x", padx=15, pady=(0, 10))
        self.yt_desc.insert("1.0", "시청해주셔서 감사합니다!\n이 영상은 하맘 자동화 프로그램에 의해 업로드 되었습니다.\n#자동화 #B2B")

        self.yt_status = ctk.CTkOptionMenu(left, values=["public (공개)", "private (비공개)", "unlisted (일부공개)"])
        self.yt_status.set("private (비공개)")
        self.yt_status.pack(fill="x", padx=15, pady=10)

        ctk.CTkButton(left, text="🚀 정보/메타 포함 유튜브 영상 업로드", font=ctk.CTkFont(weight="bold", size=14), fg_color="#c4302b", hover_color="#9e2a2b", height=45, command=self._start_youtube_upload).pack(fill="x", padx=15, pady=10)

        # 우측 로그/설명
        right = ctk.CTkFrame(content, corner_radius=8)
        right.pack(side="right", fill="both", expand=True)

        guide = ctk.CTkLabel(right, text="[✨ 사용 전 필수 준비] 구글 클라우드 콘솔에서 발급한 'YouTube Data API v3' client_secret.json 파일이 필요합니다.  최초 인증 시 크롬창이 떠서 권한을 수락해야 합니다.", text_color="orange")
        guide.pack(pady=10)

        self.youtube_log = self._create_log_textbox(right, height=500)
        self.youtube_log.pack(side="bottom", fill="both", expand=True, padx=15, pady=15)

        return frame

    # ----------------------------------------------------
    # 탭 7: 설정
    # ----------------------------------------------------
    def _create_settings_frame(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        ctk.CTkLabel(frame, text="⚙️ 기본 설정", font=ctk.CTkFont(family="Malgun Gothic", size=22, weight="bold")).pack(anchor="w", pady=(0, 20))
        
        card = ctk.CTkFrame(frame)
        card.pack(fill="x", pady=10)
        
        info = (
            "✅ 하맘 고객연락자동화 (Hamom Automation)\n\n"
            "- 동종업체 크롤링: 최신 Selenium 동적 크롤러 적용 ('관공서', '어린이집' 등 타겟 추가)\n"
            "- 업체 제안/비교견적: 수집된 이메일을 5가지 맞춤 양식 템플릿으로 발송 지원\n"
            "- 메타 유튜브 자동업로드: 영상(MP4) 및 메타데이터, 썸네일을 입력받아 스튜디오에 자동 예약 및 퍼블리싱 (API 기반)\n"
        )
        ctk.CTkLabel(card, text=info, justify="left", font=ctk.CTkFont(size=15)).pack(padx=20, pady=20, anchor="w")
        return frame

    # ----------------------------------------------------
    # 유틸
    # ----------------------------------------------------
    def _add_label(self, parent, text):
        ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=13, weight="bold"), text_color="gray70").pack(anchor="w", padx=20, pady=(10, 2))

    def _create_log_textbox(self, parent, height=200):
        log = ctk.CTkTextbox(parent, height=height, font=ctk.CTkFont(family="Consolas", size=13), fg_color="#0d1117", text_color="#57e389")
        return log

    def _append_log(self, widget, message):
        widget.insert("end", f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}\n")
        widget.see("end")

    def _process_log_queue(self):
        try:
            while True:
                tab, msg = self.log_queue.get_nowait()
                if tab == "crawl":
                    self._append_log(self.crawl_log, msg)
                elif tab == "youtube":
                    self._append_log(self.youtube_log, msg)
        except queue.Empty:
            pass
        self.after(200, self._process_log_queue)

    def _make_callback(self, tab_name):
        return lambda msg: self.log_queue.put((tab_name, msg))

    # ----------------------------------------------------
    # 로직 - 크롤링
    # ----------------------------------------------------
    def _start_crawl(self):
        region = self.crawl_region.get().strip()
        selected_cats = [cat for cat, var in self.cat_vars.items() if var.get()]
        if not selected_cats:
            messagebox.showwarning("오류", "업종을 선택하세요.")
            return
            
        def run():
            cb = self._make_callback("crawl")
            cb(f"🚀 크롤링 시작: 지역={region}, 업종={selected_cats}")
            try:
                from crawler.naver_map_crawler import NaverMapCrawler
                crawler = NaverMapCrawler(headless=False, callback=cb)
                results = crawler.crawl_all_categories(region=region, max_per_keyword=30, selected_cats=selected_cats)
                self.crawl_results = results
                cb(f"\n✅ 완료. {len(results)}건 수집됨.")
                self.after(0, lambda: self.crawl_info.configure(text=f"✅ {len(results)}건 메모리 로드 완료"))
                
                # 수집 직후 리스트 리프레시
                self.after(0, lambda: self._refresh_email_list(self.b2b_scroll, self.email_b2b_selections))
                self.after(0, lambda: self._refresh_email_list(self.kid_scroll, self.email_kids_selections))
                crawler.quit()
            except Exception as e:
                cb(f"❌ 에러: {e}")
                
        threading.Thread(target=run, daemon=True).start()

    def _save_crawl_excel(self):
        fname = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if fname and self.crawl_results:
            pd.DataFrame(self.crawl_results).to_excel(fname, index=False)

    def _load_excel(self):
        fname = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
        if fname:
            self.crawl_results = pd.read_excel(fname).to_dict("records")
            self._refresh_email_list(self.b2b_scroll, self.email_b2b_selections)
            self._refresh_email_list(self.kid_scroll, self.email_kids_selections)
            self.crawl_info.configure(text=f"✅ {len(self.crawl_results)}건 로드 완료")

    # ----------------------------------------------------
    # 로직 - 이메일 (업체 B2B)
    # ----------------------------------------------------
    def _start_b2b_email(self):
        address = self.b2b_email.get().strip()
        pwd = self.b2b_pwd.get().strip()
        title = self.b2b_title.get()
        dryrun = self.b2b_dryrun.get() == "TEST"
        
        targets = self._get_selected_targets(self.email_b2b_selections)
        if not targets:
            messagebox.showwarning("주의", "선택된 업체가 없습니다 (체크박스를 확인하세요)")
            return
            
        def run():
            self.after(0, lambda: self.b2b_info.configure(text="발송 중... (콘솔 확인)"))
            try:
                from sender.email_sender import EmailSender
                sender = EmailSender("smtp.gmail.com", 587, address, pwd, callback=print)
                success, fail = sender.send_campaign(targets, title, template_type="기본제안서", dry_run=dryrun, delay_range=(1, 3))
                self.after(0, lambda: self.b2b_info.configure(text=f"완료. 성공:{success}/실패:{fail}"))
            except Exception as e:
                self.after(0, lambda: self.b2b_info.configure(text=f"에러: {e}"))
                
        threading.Thread(target=run, daemon=True).start()

    # ----------------------------------------------------
    # 로직 - 이메일 (어린이집)
    # ----------------------------------------------------
    def _start_kids_email(self):
        address = self.kid_email.get().strip()
        pwd = self.kid_pwd.get().strip()
        title = self.kid_title.get()
        template = self.kid_template.get()
        dryrun = self.kid_dryrun.get() == "TEST"
        
        targets = self._get_selected_targets(self.email_kids_selections)
        if not targets:
            messagebox.showwarning("주의", "선택된 업체가 없습니다 (체크박스를 확인하세요)")
            return
            
        def run():
            self.after(0, lambda: self.kid_info.configure(text=f"양식 '{template}' 발송 중... (콘솔 참조)"))
            try:
                from sender.email_sender import EmailSender
                sender = EmailSender("smtp.gmail.com", 587, address, pwd, callback=print)
                success, fail = sender.send_campaign(targets, title, template_type=template, dry_run=dryrun, delay_range=(2, 4))
                self.after(0, lambda: self.kid_info.configure(text=f"완료 (성공:{success} / 실패:{fail})"))
            except Exception as e:
                self.after(0, lambda: self.kid_info.configure(text=f"에러: {e}"))

    # ----------------------------------------------------
    # 로직 - 유튜브 파트
    # ----------------------------------------------------
    def _start_youtube_upload(self):
        secret = self.yt_secret_path.get()
        video = self.yt_video_path.get()
        thumb = self.yt_thumb_path.get()
        title = self.yt_title.get()
        tags = self.yt_tags.get()
        desc = self.yt_desc.get("1.0", "end").strip()
        status = self.yt_status.get().split()[0]  # "private (비공개)" -> "private"

        if not secret or not video:
            messagebox.showwarning("오류", "인증키(json)와 유튜브 영상 파일이 필요합니다.")
            return

        def run():
            cb = self._make_callback("youtube")
            cb("📺 자동화 모듈 구동 중. 인증키를 검증합니다...")
            try:
                from sender.youtube_uploader import YouTubeAutomator
                uploader = YouTubeAutomator(callback=cb)
                # 인증 호출
                uploader.authenticate_youtube(secret)
                
                # 영상 매크로 메타 데이터 딕셔너리로 업로드 호출
                cb(f"✅ 인증 완료. {title} 영상과 설정한 메타, 이미지 배너를 업로드합니다. (몇 분 가량 기다려주세요)...")
                link = uploader.upload_video(
                    file_path=video,
                    title=title,
                    description=desc,
                    tags=tags,
                    privacy_status=status,
                    thumbnail_path=thumb if thumb else None
                )
                cb(f"🚀 [유튜브 자동화 퍼블리싱 최종 완료]\n접속 링크: {link}")
                messagebox.showinfo("성공", f"영상 업로드가 완료되었습니다!\n{link}")

            except Exception as e:
                cb(f"❌ [에러 발생]: {e}")

        threading.Thread(target=run, daemon=True).start()

if __name__ == "__main__":
    app = HamomAutoContactApp()
    app.mainloop()
