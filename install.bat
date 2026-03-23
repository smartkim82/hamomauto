@echo off
chcp 65001 > nul
echo ============================================
echo  고객 연락 자동화 - 패키지 설치
echo ============================================
echo.

REM Python 경로 자동 탐색
set PYTHON_CMD=

for %%p in (
    "python"
    "python3"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python39\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python310\python.exe"
) do (
    %%p --version > nul 2>&1
    if not errorlevel 1 (
        set PYTHON_CMD=%%p
        goto :found_python
    )
)

echo [오류] Python을 찾을 수 없습니다.
echo.
echo 아래 링크에서 Python 3.10 이상을 설치해주세요:
echo https://www.python.org/downloads/
echo.
echo 설치 시 "Add Python to PATH" 체크박스를 반드시 선택하세요!
pause
exit /b 1

:found_python
echo [OK] Python 발견: %PYTHON_CMD%
%PYTHON_CMD% --version
echo.

echo [1/3] pip 업그레이드...
%PYTHON_CMD% -m pip install --upgrade pip
echo.

echo [2/3] 기본 패키지 설치...
%PYTHON_CMD% -m pip install selenium webdriver-manager requests beautifulsoup4 lxml pandas openpyxl python-dotenv customtkinter
echo.

echo [3/3] 인스타그램 패키지 설치...
%PYTHON_CMD% -m pip install instagrapi Pillow
echo.

echo ============================================
echo  [완료] 설치가 끝났습니다!
echo  이제 run.bat을 실행하세요.
echo ============================================

REM Python 경로를 run.bat에서 재사용할 수 있게 저장
echo %PYTHON_CMD% > python_path.txt

pause
