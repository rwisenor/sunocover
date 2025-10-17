@echo off
chcp 65001 >nul
echo.
echo ════════════════════════════════════════════════════════
echo   🎵 מעבד שירים עם RVC
echo   מפעיל את האפליקציה...
echo ════════════════════════════════════════════════════════
echo.

:: בדיקה שהקובץ הראשי קיים
if not exist "standalone_song_processor.py" (
    echo ❌ שגיאה: הקובץ standalone_song_processor.py לא נמצא
    echo    וודא שאתה נמצא בתיקייה הנכונה
    pause
    exit /b 1
)

:: בדיקה שהסביבה הווירטואלית קיימת
if not exist "venv\Scripts\activate.bat" (
    echo ❌ שגיאה: סביבה וירטואלית לא נמצאה
    echo.
    echo 💡 הרץ setup.bat תחילה להתקנה
    pause
    exit /b 1
)

:: הפעלת הסביבה הוירטואלית
echo 📦 מפעיל סביבה וירטואלית...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ כישלון בהפעלת הסביבה
    pause
    exit /b 1
)

:: בדיקת local_models.json
if not exist "local_models.json" (
    echo ⚠️  אזהרה: local_models.json לא נמצא!
    echo.
    echo 💡 צור את הקובץ על בסיס local_models.json.example
    echo    והגדר את המודלים שלך
    echo.
    set /p "continue=להמשיך בכל זאת? (y/N): "
    if /i not "!continue!"=="y" (
        pause
        exit /b 1
    )
)

:: בדיקת FFmpeg
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  אזהרה: FFmpeg לא זמין!
    echo    העיבוד עלול להיכשל ללא FFmpeg
    echo.
)

:: הרצת האפליקציה
echo.
echo 🚀 מפעיל את האפליקציה...
echo.
echo ════════════════════════════════════════════════════════
echo   ℹ️  לאחר ההפעלה:
echo   📱 פתח דפדפן וגש ל: http://localhost:7860
echo   🛑 לעצירה לחץ Ctrl+C
echo ════════════════════════════════════════════════════════
echo.

python standalone_song_processor.py

:: שמירת קוד היציאה
set EXIT_CODE=%ERRORLEVEL%

:: הודעה בסוף
echo.
if %EXIT_CODE% equ 0 (
    echo ✅ האפליקציה נסגרה בהצלחה
) else (
    echo ❌ האפליקציה נסגרה עם שגיאה (קוד: %EXIT_CODE%^)
)
echo.
pause
