"""
유튜브(YouTube) 영상 자동 업로더 모듈
Google API (Data API v3)를 사용하여 영상을 제목/설명/태그/썸네일(메타) 정보와 함께 업로드합니다.
"""

import os
import sys
import datetime
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# 유튜브 업로드 필수 스코프 (쓰기 권한)
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

class YouTubeAutomator:
    def __init__(self, callback=None):
        self.callback = callback
        self.api_service_name = "youtube"
        self.api_version = "v3"
        self.youtube = None

    def _log(self, msg):
        print(f"[유튜브] {msg}")
        if self.callback:
            self.callback(msg)

    def authenticate_youtube(self, client_secrets_file):
        """
        사용자 OAuth 인증 (유튜브 채널 로그인)
        client_secrets_file: Google Cloud Console에서 다운받은 'client_secret.json'
        token.json: 인증 이후 지속 로그인을 위해 자동 저장되는 파일
        """
        creds = None
        base_dir = Path(client_secrets_file).parent
        token_path = os.path.join(base_dir, 'token.json')

        # 기존 토큰 존재 시 불러오기
        if os.path.exists(token_path):
            try:
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            except Exception as e:
                self._log(f"기존 토큰 오류 (무시됨): {e}")

        # 유효한 크리덴셜 확인 및 재/초기 인증
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    self._log(f"토큰 갱신 실패: {e}")
                    creds = None

            if not creds:
                if not os.path.exists(client_secrets_file):
                    raise FileNotFoundError("클라이언트 시크릿 파일(client_secret.json)이 지정된 경로에 없습니다.")
                
                # 구글 로그인 창 띄우기
                self._log("구글 인증 창을 통한 로그인이 필요합니다. (브라우저 확인 요망)")
                flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # 인증 토큰 저장
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
                self._log(f"로그인 토큰 저장됨: {token_path}")

        # YouTube API 인스턴스 빌드
        self.youtube = build(self.api_service_name, self.api_version, credentials=creds)
        self._log("✅ 유튜브 채널 인증이 성공적으로 완료되었습니다.")
        return True

    def upload_video(self, file_path, title, description, tags=None, category_id="22", privacy_status="public", thumbnail_path=None):
        """
        유튜브 영상 업로드 함수
        """
        if not self.youtube:
            raise Exception("유튜브 API 인증이 진행되지 않았습니다.")
            
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"영상 파일을 찾을 수 없습니다: {file_path}")

        self._log(f"▶️ 영상 업로드 시작: '{title}'")
        
        # 태그 처리
        if isinstance(tags, str):
            tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
        elif not tags:
            tags = []

        # 메타데이터 (제목, 설명, 태그, 카테고리, 상태설정)
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': category_id # 22: 검색(People & Blogs), 27: 교육 등...
            },
            'status': {
                'privacyStatus': privacy_status, # public, private, unlisted
                'selfDeclaredMadeForKids': False
            }
        }

        # 동영상 객체 설정 (파일 청크 업로드)
        media = MediaFileUpload(file_path, chunksize=-1, resumable=True)

        req = self.youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        response = None
        # 청크 업로드 루프
        while response is None:
            status, response = req.next_chunk()
            if status:
                percent = int(status.progress() * 100)
                self._log(f"업로드 진행 중... {percent}%")
                
        video_id = response.get("id")
        self._log(f"✅ 영상 업로드 완료! (Video ID: {video_id})")

        # 썸네일 별도 설정
        if thumbnail_path and os.path.exists(thumbnail_path):
            self._log("🖼️ 커스텀 썸네일(메타) 이미지 업로드 중...")
            self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path)
            ).execute()
            self._log("✅ 썸네일 적용 완료!")

        return f"https://youtu.be/{video_id}"
