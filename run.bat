@echo off
chcp 65001 > nul
echo ============================================
echo  고객 연락 자동화 프로그램 실행
echo ============================================
cd /d "%~dp0"

REM 설치된 Python 경로 자동 탐색
set PYTHON_CMD=

REM winget/공식 설치 기본 경로
for %%p in (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python39\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "python"
) do (
    if exist %%p (
        set PYTHON_CMD=%%p
        goto :run
    )
    %%p --version > nul 2>&1
    if not errorlevel 1 (
        set PYTHON_CMD=%%p
        goto :run
    )
)

echo [오류] Python을 찾을 수 없습니다.
echo PowerShell을 새로 열고 다시 시도하거나, PC를 재시작해주세요.
pause
exit /b 1

:run
echo Python: %PYTHON_CMD%
%PYTHON_CMD% main.py
if %errorlevel% neq 0 (
    echo.
    echo [오류] 실행 실패. install.bat을 먼저 실행해주세요.
    pause
)
