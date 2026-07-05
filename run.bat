@echo off
chcp 65001 >nul 2>&1
title Marouf - PlayStation Cafe Manager

echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║                                                    ║
echo ║    Marouf PlayStation Cafe Manager v1.0            ║
echo ║    تشغيل البرنامج                                   ║
echo ║                                                    ║
echo ╚══════════════════════════════════════════════════════╝
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python غير مثبت!
    echo يرجى تثبيت Python 3.10 أو أحدث وتشغيل install.bat أولاً.
    pause
    exit /b 1
)

:: Quick dependency check
python -c "import customtkinter" >nul 2>&1
if errorlevel 1 (
    echo [WARN] CustomTkinter غير مثبت - جاري التثبيت التلقائي...
    pip install customtkinter==5.2.2
    if errorlevel 1 (
        echo [ERROR] فشل التثبيت التلقائي. يرجى تشغيل install.bat يدوياً.
        pause
        exit /b 1
    )
)

python -c "import sqlalchemy" >nul 2>&1
if errorlevel 1 (
    echo [WARN] SQLAlchemy غير مثبت - جاري التثبيت التلقائي...
    pip install SQLAlchemy==2.0.35
    if errorlevel 1 (
        echo [ERROR] فشل التثبيت التلقائي. يرجى تشغيل install.bat يدوياً.
        pause
        exit /b 1
    )
)

:: Run the app
echo [OK] جاري تشغيل البرنامج...
echo.
cd /d "%~dp0"
python main.py

if errorlevel 1 (
    echo.
    echo [ERROR] حدث خطأ أثناء تشغيل البرنامج.
    echo يرجى مراجعة ملف debug.log للتفاصيل.
)

pause