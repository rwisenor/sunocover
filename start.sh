#!/bin/bash
# -*- coding: utf-8 -*-

# צבעים
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "════════════════════════════════════════════════════════"
echo "  🎵 מעבד שירים עם RVC"
echo "  מפעיל את האפליקציה..."
echo "════════════════════════════════════════════════════════"
echo ""

# בדיקה שהקובץ הראשי קיים
if [ ! -f "standalone_song_processor.py" ]; then
    echo -e "${RED}❌ שגיאה: הקובץ standalone_song_processor.py לא נמצא${NC}"
    echo "   וודא שאתה נמצא בתיקייה הנכונה"
    exit 1
fi

# בדיקה שהסביבה הווירטואלית קיימת
if [ ! -d "venv" ] || [ ! -f "venv/bin/activate" ]; then
    echo -e "${RED}❌ שגיאה: סביבה וירטואלית לא נמצאה${NC}"
    echo ""
    echo "💡 הרץ ./setup.sh תחילה להתקנה"
    exit 1
fi

# הפעלת הסביבה הוירטואלית
echo "📦 מפעיל סביבה וירטואלית..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ כישלון בהפעלת הסביבה${NC}"
    exit 1
fi

# בדיקת local_models.json
if [ ! -f "local_models.json" ]; then
    echo -e "${YELLOW}⚠️  אזהרה: local_models.json לא נמצא!${NC}"
    echo ""
    echo "💡 צור את הקובץ על בסיס local_models.json.example"
    echo "   והגדר את המודלים שלך"
    echo ""
    read -p "להמשיך בכל זאת? (y/N): " continue
    if [[ "$continue" != "y" && "$continue" != "Y" ]]; then
        exit 1
    fi
fi

# בדיקת FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${YELLOW}⚠️  אזהרה: FFmpeg לא זמין!${NC}"
    echo "   העיבוד עלול להיכשל ללא FFmpeg"
    echo ""
fi

# הרצת האפליקציה
echo ""
echo "🚀 מפעיל את האפליקציה..."
echo ""
echo "════════════════════════════════════════════════════════"
echo "  ℹ️  לאחר ההפעלה:"
echo "  📱 פתח דפדפן וגש ל: http://localhost:7860"
echo "  🛑 לעצירה לחץ Ctrl+C"
echo "════════════════════════════════════════════════════════"
echo ""

python standalone_song_processor.py

# שמירת קוד היציאה
EXIT_CODE=$?

# הודעה בסוף
echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ האפליקציה נסגרה בהצלחה${NC}"
else
    echo -e "${RED}❌ האפליקציה נסגרה עם שגיאה (קוד: $EXIT_CODE)${NC}"
fi
echo ""
