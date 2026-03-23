"""
이메일 발송 템플릿 관리자
업체 제안서, 어린이집 비교견적 등 다양한 양식 제공
"""

import smtplib
import ssl
import time
import random
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from pathlib import Path

class EmailSender:
    def __init__(self, smtp_host, smtp_port, username, password, callback=None):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.callback = callback
        self.sent_count = 0
        self.send_log = []

    def _log(self, msg):
        print(f"[이메일] {msg}")
        if self.callback:
            self.callback(msg)

    def get_template(self, company_name, template_type="기본제안서"):
        # 기본 제안서 포맷들
        if template_type == "기본제안서":
            return self._template_interior(company_name) # 임시로 인테리어 양식 매칭
            
        # 어린이집 비교견적 5가지 양식
        if template_type == "비교견적 양식1 (심플)":
            return self._template_kid_simple(company_name)
        elif template_type == "비교견적 양식2 (상세비용)":
            return self._template_kid_detail(company_name)
        elif template_type == "비교견적 양식3 (친환경/안전강조)":
            return self._template_kid_eco(company_name)
        elif template_type == "비교견적 양식4 (프리미엄)":
            return self._template_kid_premium(company_name)
        elif template_type == "비교견적 양식5 (정기관리형)":
            return self._template_kid_subscription(company_name)
            
        # 업종별 맞춤형이 들어올 경우
        return self._template_interior(company_name)

    # ==========================================
    # 어린이집 비교견적 양식 1~5
    # ==========================================
    def _template_kid_simple(self, company_name):
        return f"""
        <!DOCTYPE html><html><head><meta charset="UTF-8">
        <style>body{{font-family:'Malgun Gothic',sans-serif;color:#333;line-height:1.6;}}</style>
        </head><body>
        <h2>[비교견적서] {company_name} 시설 관리 비용 안내 (기본/심플형)</h2>
        <p>안녕하세요. {company_name} 원장님/담당자님.</p>
        <p>저희 하맘(Hamom)에서는 어린이집/유치원 전용으로 거품을 뺀 합리적인 시설 시공 및 청소 비교견적을 제공하고 있습니다.</p>
        <table border="1" cellpadding="8" cellspacing="0" style="width:100%; border-collapse:collapse; text-align:center;">
            <tr style="background:#f0f0f0;"><th>구분</th><th>항목</th><th>예상 단가(평당)</th><th>비고</th></tr>
            <tr><td>기본 시공</td><td>안전 매트 / 도배 / 필름</td><td>상담 후 확정</td><td>최소 비용 보장</td></tr>
            <tr><td>정기 청소</td><td>장난감 소독 / 살균 스팀</td><td>별도 협의</td><td>-</td></tr>
        </table>
        <p>구체적인 현장 상황에 따라 비용은 변동될 수 있습니다. <b>무료 방문 견적</b>이 필요하시면 편하게 회신 부탁드립니다.</p>
        <p>감사합니다.</p>
        </body></html>
        """

    def _template_kid_detail(self, company_name):
        return f"""
        <!DOCTYPE html><html><head><meta charset="UTF-8">
        <style>body{{font-family:'Malgun Gothic',sans-serif;}} th{{background:#ffe4ec;}} td,th{{border:1px solid #ddd; padding:10px;}}</style>
        </head><body>
        <h2>[상세 견적] {company_name} 환경 개선 프로젝트 안내</h2>
        <p>{company_name}의 아이들이 안전하게 뛰어놀 수 있는 공간을 위해 항목별 상세 비교견적을 제안합니다.</p>
        <table style="width:100%; border-collapse:collapse;">
            <tr><th>분류</th><th>시공/작업 상세내용</th><th>타사 평균가</th><th>당사 제안가</th></tr>
            <tr><td>바닥 안전</td><td>방염 쿠션매트 시공 (친환경)</td><td>15,000원/㎡</td><td><b>12,000원/㎡</b></td></tr>
            <tr><td>방충/방범</td><td>미세 방충망 및 방범창 교체</td><td>소형 기준 3만원</td><td><b>2.5만원</b></td></tr>
            <tr><td>위생/청소</td><td>전 구역 피톤치드 살균/항균</td><td>회당 15만원</td><td><b>10만원 (정기할인)</b></td></tr>
        </table>
        <p>* 위 견적은 예시 단가이며, 면적과 조건에 따라 달라집니다.<br>비교해보시고 언제든 문의주세요!</p>
        </body></html>
        """

    def _template_kid_eco(self, company_name):
        return f"""
        <html><body>
        <h2 style="color:#2ca02c;">🌿 {company_name} 친환경 자재 시공/청소 비교견적 제안</h2>
        <p>어린이 시설의 가장 중요한 기준은 '안전'과 '무독성'입니다.</p>
        <p>저희 업체는 환경부 인증 마크를 획득한 친환경 접착제와 살균수만을 사용합니다.</p>
        <ul>
            <li><b>A안 (기본 케어):</b> 친환경 도배 + 기본 소독 (평당 X원)</li>
            <li><b>B안 (안심 보장케어):</b> 친환경 도배 + 쿠션매트 + 피톤치드 3중 살균 (평당 X원)</li>
            <li><b>C안 (프리미엄):</b> B안 + 전체 창호 단열/안전 필름 시공</li>
        </ul>
        <p>다른 업체와 <b>'자재 등급'</b>을 꼭 비교해 보세요! 안심하고 원장님이 선택하실 수 있는 견적을 보내드립니다.</p>
        </body></html>
        """

    def _template_kid_premium(self, company_name):
        return f"""
        <html><body style="background:#fafafa; padding:20px;">
        <div style="background:#fff; border-top:4px solid #gold; padding:20px; box-shadow:0 0 10px rgba(0,0,0,0.05);">
        <h2>✨ {company_name} 프리미엄 시설/인테리어 패키지 견적</h2>
        <p>VIP 프리미엄 유치원/어린이집을 위한 최고급 자재와 전문 인력 투입을 약속드립니다.</p>
        <p>보육 공간의 가치를 한 단계 높이는 시공. 비용보다는 '품질 검수'와 'A/S 기간'으로 승부합니다.</p>
        <p><b>[타사 대비 특장점]</b><br>1. 업계 최장 3년 무상 A/S 보장<br>2. 보육시간을 피한 야간/주말 시공 무상 지원<br>3. 시공 전후 공기질 측정 데이터 제공</p>
        <p>정확한 비교견적서(PDF)를 요청하시면 바로 회신해 드리겠습니다.</p>
        </div>
        </body></html>
        """

    def _template_kid_subscription(self, company_name):
        return f"""
        <html><body>
        <h2>📅 {company_name} 정기 구독형 관리 시스템 (청소/유지보수)</h2>
        <p>목돈이 들어가는 방식이 아닌, 매월 정해진 비용으로 보육 시설 전체를 관리해 드립니다.</p>
        <table border="1" cellpadding="5" cellspacing="0">
            <tr><th>서비스명</th><th>주기</th><th>비교견적가 (월)</th></tr>
            <tr><td>일반 청소 및 방역</td><td>주 2회 방문</td><td>월 XX만원 부터 (타사대비 15% 저렴)</td></tr>
            <tr><td>시설물 유지보수 콜</td><td>무제한 요청</td><td>월 XX만원</td></tr>
            <tr><td>통합 패키지</td><td>청소+유지보수</td><td><b>월 XX만원 (추천!)</b></td></tr>
        </table>
        <p>원장님의 고민을 덜어드릴 구독형 관리 서비스, 무료 1주 체험 견적을 신청해보세요!</p>
        </body></html>
        """

    def _template_interior(self, company_name):
        return f"""
        <!DOCTYPE html><html><head><meta charset="UTF-8"></head>
        <body style="font-family:Arial; padding:20px;">
        <h2>B2B 인테리어/시공 파트너십 제안 - {company_name} 귀중</h2>
        <p>안녕하세요. {company_name} 담당자님.</p>
        <p>성공적인 비즈니스를 위한 시공 및 온라인 마케팅 제휴를 제안드립니다.</p>
        <p>귀사의 훌륭한 시공 사례를 돋보이게 하는 포트폴리오 사이트 제작 및 타겟 광고를 지원해 드립니다.</p>
        <p>언제든 회신 주시면 자세한 안내서 보내드리겠습니다. 감사합니다.</p>
        </body></html>
        """

    def send_email(self, to_email, subject, html_body, dry_run=False):
        if dry_run:
            self._log(f"[테스트] 발송 예정: {to_email} (제목: {subject})")
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = self.username
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.ehlo()
                server.starttls(context=context)
                server.login(self.username, self.password)
                server.sendmail(self.username, to_email, msg.as_string())

            self.sent_count += 1
            self.send_log.append({
                "email": to_email, "subject": subject,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": "성공"
            })
            self._log(f"✅ 발송 성공: {to_email}")
            return True

        except Exception as e:
            self._log(f"❌ 발송 실패 {to_email}: {e}")
            self.send_log.append({
                "email": to_email, "subject": subject,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": f"실패: {e}"
            })
            return False

    def send_campaign(self, targets, subject_template, template_type="기본제안서", dry_run=False, delay_range=(5, 15)):
        success, fail = 0, 0
        for i, target in enumerate(targets):
            email = target.get("이메일", "")
            name = target.get("업체명", "담당자")

            if not email:
                continue

            html = self.get_template(name, template_type)
            subject = subject_template.format(name=name)

            ok = self.send_email(email, subject, html, dry_run)
            if ok: success += 1
            else: fail += 1

            if not dry_run and i < len(targets) - 1:
                delay = random.uniform(*delay_range)
                self._log(f"다음 발송 대기: {delay:.1f}초")
                time.sleep(delay)

        self._log(f"\n캠페인 완료: 성공 {success}건 / 실패 {fail}건")
        return success, fail
