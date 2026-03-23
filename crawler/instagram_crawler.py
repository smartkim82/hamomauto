"""
인스타그램 크롤러 & DM 발송기
공구 셀럽 계정 검색 및 DM 자동화
"""

import time
import random
import json
import os
from datetime import datetime
from pathlib import Path

try:
    from instagrapi import Client
    from instagrapi.exceptions import (
        LoginRequired, ChallengeRequired, TwoFactorRequired, BadPassword
    )
    INSTAGRAPI_AVAILABLE = True
except ImportError:
    INSTAGRAPI_AVAILABLE = False


class InstagramDMBot:
    """인스타그램 DM 발송 봇"""

    # 계정 보호를 위한 제한값
    MAX_DM_PER_DAY = 20       # 하루 최대 DM 수
    MIN_DELAY_SEC = 60        # DM 간 최소 대기 (초)
    MAX_DELAY_SEC = 180       # DM 간 최대 대기 (초)

    def __init__(self, username, password, session_file=None, callback=None):
        if not INSTAGRAPI_AVAILABLE:
            raise ImportError("instagrapi 패키지가 설치되지 않았습니다. pip install instagrapi")

        self.username = username
        self.password = password
        self.session_file = session_file or f"session_{username}.json"
        self.callback = callback
        self.client = Client()
        self.dm_count_today = 0
        self.sent_log = []

    def _log(self, msg):
        print(f"[인스타] {msg}")
        if self.callback:
            self.callback(msg)

    def login(self):
        """로그인 (세션 재사용)"""
        # 기존 세션 불러오기
        if Path(self.session_file).exists():
            try:
                self.client.load_settings(self.session_file)
                self.client.login(self.username, self.password)
                self._log("세션 로그인 성공")
                return True
            except Exception:
                self._log("세션 만료 - 새로 로그인합니다")

        # 신규 로그인
        try:
            self.client.login(self.username, self.password)
            self.client.dump_settings(self.session_file)
            self._log(f"로그인 성공: @{self.username}")
            return True
        except BadPassword:
            self._log("❌ 비밀번호가 틀렸습니다.")
            return False
        except ChallengeRequired:
            self._log("❌ 보안 인증이 필요합니다. 앱에서 직접 로그인하세요.")
            return False
        except Exception as e:
            self._log(f"❌ 로그인 오류: {e}")
            return False

    def search_influencers(self, hashtags, min_followers=5000, max_followers=500000):
        """해시태그로 공구 셀럽 검색"""
        results = []
        seen_users = set()

        for hashtag in hashtags:
            self._log(f"해시태그 검색: #{hashtag}")
            try:
                medias = self.client.hashtag_medias_recent(hashtag, amount=30)
                for media in medias:
                    user_id = media.user.pk
                    if user_id in seen_users:
                        continue
                    seen_users.add(user_id)

                    # 팔로워 수 확인
                    try:
                        user_info = self.client.user_info(user_id)
                        followers = user_info.follower_count
                        if min_followers <= followers <= max_followers:
                            results.append({
                                "username": user_info.username,
                                "full_name": user_info.full_name,
                                "followers": followers,
                                "bio": user_info.biography,
                                "user_id": str(user_id),
                                "is_business": user_info.is_business,
                                "category": user_info.category,
                                "email": self._extract_email_from_bio(user_info.biography or ""),
                                "검색해시태그": hashtag,
                            })
                            self._log(f"  발견: @{user_info.username} (팔로워 {followers:,}명)")
                        time.sleep(random.uniform(1, 2))
                    except Exception as e:
                        self._log(f"  유저 정보 오류: {e}")

                time.sleep(random.uniform(3, 6))
            except Exception as e:
                self._log(f"해시태그 검색 오류: {e}")

        self._log(f"총 {len(results)}명 발견")
        return results

    def _extract_email_from_bio(self, bio):
        """바이오에서 이메일 추출"""
        import re
        emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", bio)
        return emails[0] if emails else ""

    def send_dm(self, username, message, dry_run=False):
        """DM 발송"""
        if self.dm_count_today >= self.MAX_DM_PER_DAY:
            self._log(f"⚠️ 하루 DM 한도({self.MAX_DM_PER_DAY}개) 초과")
            return False

        try:
            if dry_run:
                self._log(f"[테스트] DM 발송 예정: @{username}")
                return True

            user_id = self.client.user_id_from_username(username)
            self.client.direct_send(message, [user_id])
            self.dm_count_today += 1

            log_entry = {
                "username": username,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "성공",
            }
            self.sent_log.append(log_entry)
            self._log(f"✅ DM 발송 성공: @{username} ({self.dm_count_today}/{self.MAX_DM_PER_DAY})")
            return True

        except Exception as e:
            self._log(f"❌ DM 발송 실패 @{username}: {e}")
            self.sent_log.append({
                "username": username,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": f"실패: {e}",
            })
            return False

    def send_dm_campaign(self, user_list, message_template, dry_run=False):
        """다수 사용자에게 DM 배치 발송"""
        success = 0
        fail = 0

        for i, user in enumerate(user_list):
            username = user.get("username", "")
            if not username:
                continue

            # 메시지 개인화
            message = message_template.format(
                name=user.get("full_name") or username,
                username=username,
                followers=user.get("followers", 0),
            )

            self._log(f"\n[{i+1}/{len(user_list)}] @{username} 에게 DM 발송 중...")
            result = self.send_dm(username, message, dry_run=dry_run)

            if result:
                success += 1
            else:
                fail += 1

            if self.dm_count_today >= self.MAX_DM_PER_DAY:
                self._log("하루 한도 도달. 내일 다시 시도하세요.")
                break

            # 랜덤 딜레이 (탐지 방지)
            delay = random.uniform(self.MIN_DELAY_SEC, self.MAX_DELAY_SEC)
            self._log(f"다음 DM까지 {delay:.0f}초 대기...")
            time.sleep(delay)

        self._log(f"\n=== 발송 완료: 성공 {success}건 / 실패 {fail}건 ===")
        return success, fail

    def save_log(self, filename=None):
        """발송 로그 저장"""
        if not filename:
            filename = f"dm_log_{datetime.now().strftime('%Y%m%d')}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.sent_log, f, ensure_ascii=False, indent=2)
        self._log(f"로그 저장: {filename}")


# 공구 셀럽 검색용 추천 해시태그
GONGGU_HASHTAGS = [
    "공구추천",
    "공구진행중",
    "공구셀럽",
    "인스타공구",
    "공구해요",
    "맞팔공구",
    "공동구매",
    "인플루언서공구",
    "육아공구",
    "주부공구",
]
