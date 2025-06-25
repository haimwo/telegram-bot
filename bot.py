import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import tinytuya
import pytz
from waitress import serve
from wsgiref.simple_server import make_server

# הגדרת פורט
port = int(os.getenv("PORT", 8080))

# קריאת משתנים סביבתיים
BOT_TOKEN = os.getenv("BOT_TOKEN")
TUYA_API_KEY = os.getenv("TUYA_API_KEY")
TUYA_API_SECRET = os.getenv("TUYA_API_SECRET")
TUYA_API_REGION = os.getenv("TUYA_API_REGION")
ALLOWED_CHAT_IDS = ["103383402", "7201721304"]

# הגדרת אזור זמן (ישראל)
TIMEZONE = pytz.timezone('Asia/Jerusalem')

# רשימת מכשירים
DEVICES = {
    "boiler": {
        "name": "דוד חכם",
        "id": "bf99cebbfccecdd893nqbv",
        "key": "B>rYx|*=1e/vaJqM",
        "type": "switch"
    },
    "ac_plug": {
        "name": "פקק מזגן סלון",
        "id": "bfe2ce01ff2fa62d2frbsa",
        "key": ")?bdG&c$YEa~|d6i",
        "type": "switch"
    },
    "ac_remote": {
        "name": "שלט מזגן סלון",
        "id": "bf0729b073f299ca3b91nq",
        "key": ".!-IT;Xv2i=Fy<e&",
        "type": "ir_ac",
        "parent_id": "bf636e4c2327674c17jnyh"
    }
}

# חיבור ל-Tuya Cloud API
cloud = tinytuya.Cloud(
    apiRegion=TUYA_API_REGION,
    apiKey=TUYA_API_KEY,
    apiSecret=TUYA_API_SECRET
)

# WSGI app תקף
def simple_app(environ, start_response):
    status = '200 OK'
    response_headers = [('Content-Type', 'text/plain')]
    start_response(status, response_headers)
    return [b'Bot is running\n']

# פונקציית התחלה
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.chat_id) not in ALLOWED_CHAT_IDS:
        await update.message.reply_text("סליחה, אין לך הרשאה להשתמש בבוט הזה!")
        return

    keyboard = [
        [InlineKeyboardButton("דוד חכם - הדלק", callback_data="boiler_on"),
         InlineKeyboardButton("דוד חכם - כבה", callback_data="boiler_off")],
        [InlineKeyboardButton("דוד חכם - טיימר 45 דק'", callback_data="boiler_timer_2700")],
        [InlineKeyboardButton("פקק מזגן סלון - הדלק", callback_data="ac_plug_on"),
         InlineKeyboardButton("פקק מזגן סלון - כבה", callback_data="ac_plug_off")],
        [InlineKeyboardButton("מזגן סלון - הדלק (24°C, קירור, נמוך)", callback_data="ac_remote_on"),
         InlineKeyboardButton("מזגן סלון - כבה", callback_data="ac_remote_off")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("ברוכים הבאים לבוט הבית החכם!", reply_markup=reply_markup)

# פונקציית טיפול בכפתורים
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    dev_id, action = query.data.split("_")
    dev_info = DEVICES.get(dev_id)

    if dev_info["type"] == "switch":
        if action == "on":
            cloud.sendcommand(dev_info["id"], [{"code": "switch_1", "value": True}])
            await query.message.reply_text(f"{dev_info['name']} הודלק!")
        elif action == "off":
            cloud.sendcommand(dev_info["id"], [{"code": "switch_1", "value": False}])
            await query.message.reply_text(f"{dev_info['name']} כובה!")
        elif action == "timer_2700":
            cloud.sendcommand(dev_info["id"], [{"code": "countdown_1", "value": 2700}])
            await query.message.reply_text(f"{dev_info['name']} יכבה בעוד 45 דקות!")
    elif dev_info["type"] == "ir_ac":
        if action == "on":
            cloud.sendcommand(dev_info["id"], [{
                "code": "ir_send",
                "value": {
                    "device_id": dev_info["id"],
                    "command": {
                        "power": "on",
                        "mode": "cool",
                        "temp": 24,
                        "fan_speed": "low"
                    }
                }
            }])
            await query.message.reply_text("מזגן סלון הודלק: 24°C, קירור, עוצמה נמוכה!")
        elif action == "off":
            cloud.sendcommand(dev_info["id"], [{
                "code": "ir_send",
                "value": {
                    "device_id": dev_info["id"],
                    "command": {"power": "off"}
                }
            }])
            await query.message.reply_text("מזגן סלון כובה!")

def main() -> None:
    # הפעל שרת Waitress ברקע
    import multiprocessing
    p = multiprocessing.Process(target=lambda: serve(simple_app, host='0.0.0.0', port=port))
    p.start()
    
    # בנה והרץ את הבוט
    application = Application.builder().token(os.getenv("BOT_TOKEN")).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.run_polling()

if __name__ == "__main__":
    main()
