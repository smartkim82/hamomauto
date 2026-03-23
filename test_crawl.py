import requests
import json
import urllib.parse

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Referer": "https://search.naver.com/",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

# 네이버 스마트 플레이스 검색 API (place API)
query = urllib.parse.quote("서울 인테리어")

urls_to_test = [
    f"https://search.naver.com/search.naver?query={query}&where=place&sm=tab_pge&start=1",
    f"https://m.place.naver.com/place/list?query={query}&x=126.9779692&y=37.566535&clientX=126.9779692&clientY=37.566535",
    f"https://map.naver.com/p/api/search/allSearch?query={query}&type=place&page=1&displayCount=5",
    f"https://api.place.naver.com/graphql",  # GraphQL 방식
]

for url in urls_to_test:
    print(f"\n--- 시도: {url[:70]}...")
    try:
        r = requests.get(url, headers=headers, timeout=8)
        print(f"  상태: {r.status_code} | Content-Type: {r.headers.get('Content-Type','')[:50]}")
        if r.status_code == 200:
            content = r.text[:300]
            print(f"  내용: {content}")
    except Exception as e:
        print(f"  오류: {e}")
