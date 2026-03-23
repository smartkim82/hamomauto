# 📁 프로젝트 구조

고객연락자동화/
├── 📄 main.py                    # 메인 GUI 실행 파일
├── 📄 install.bat                # 패키지 설치 (처음 한 번만)
├── 📄 run.bat                    # 프로그램 실행
├── 📄 requirements.txt           # 의존성 목록
├── 📄 .env.example               # 환경변수 예시
├── 📁 crawler/
│   ├── naver_map_crawler.py     # 네이버 지도 크롤러
│   └── instagram_crawler.py     # 인스타그램 DM 봇
└── 📁 sender/
    └── email_sender.py          # 이메일 발송 모듈

# 🚀 사용 방법

## 1단계: 설치
install.bat 더블클릭 (처음 한 번만)

## 2단계: 실행
run.bat 더블클릭

## 3단계: 업체 크롤링 탭
- 지역 입력 (예: 서울 강남)
- 업종 체크 (인테리어/청소/커튼/필름)
- "크롤링 시작" 클릭
- 결과 엑셀 저장

## 4단계: 이메일 발송 탭
- Gmail 앱 비밀번호 입력
- 테스트 모드로 먼저 확인
- 실제 발송 실행

## 5단계: 인스타 DM 탭
- 인스타 계정 로그인
- 해시태그로 공구 셀럽 검색
- DM 메시지 작성 후 발송
