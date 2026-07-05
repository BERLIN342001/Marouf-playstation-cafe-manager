@echo off
chcp 65001 >nul 2>&1
title Marouf - Installing Dependencies

echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║   Marouf PlayStation Cafe Manager                   ║
echo ║   تثبيت المكتبات المطلوبة                             ║
echo ╚══════════════════════════════════════════════════════╝
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python غير مثبت!
    echo يرجى تثبيت Python 3.10 أو أحدث من:
    echo https://www.python.org/downloads/
    echo.
    echo تأكد من تفعيل الخيار "Add Python to PATH" أثناء التثبيت.
    pause
    exit /b 1
)

echo [OK] Python موجود
python --version
echo.

:: Install dependencies
echo [1/2] جاري تثبيت CustomTkinter...
pip install customtkinter==5.2.2
if errorlevel 1 (
    echo [ERROR] فشل تثبيت CustomTkinter
    pause
    exit /b 1
)
echo [OK] CustomTkinter تم التثبيت

echo.
echo [2/2] جاري تثبيت SQLAlchemy...
pip install SQLAlchemy==2.0.35
if errorlevel 1 (
    echo [ERROR] فشل تثبيت SQLAlchemy
    pause
    exit /b 1
)
echo [OK] SQLAlchemy تم التثبيت

echo.
echo ══════════════════════════════════════════════════════
echo   تم تثبيت جميع المكتبات بنجاح!
echo   يمكنك الآن تشغيل run.bat
echo ══════════════════════════════════════════════════════
echo.
pause