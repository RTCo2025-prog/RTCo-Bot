import os
import re
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from groq import Groq
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# 1. إعداد المفاتيح والمعرفات
TELEGRAM_BOT_TOKEN = "8624313127:AAHtPRy05UNfL5_6Cv1ySiqfcT5eqRCTks0"
GROQ_API_KEY = "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"
ADMIN_CHAT_ID = "7822645247"

client = Groq(api_key=GROQ_API_KEY)

# 2. القوائم والأزرار التفاعلية
def get_main_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🏗️ المقاولات والإنشاءات", callback_data="dept_contracting"),
            InlineKeyboardButton("🏢 الاستثمارات العقارية", callback_data="dept_realestate")
        ],
        [
            InlineKeyboardButton("📦 التجارة العامة", callback_data="dept_trade"),
            InlineKeyboardButton("🚚 النقل واللوجستيات", callback_data="dept_transport")
        ],
        [
            InlineKeyboardButton("📞 أرقام الهواتف والتواصل", callback_data="dept_contact"),
            InlineKeyboardButton("🌐 منصاتنا الرسمية", callback_data="dept_social")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="go_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

# 3. توجيهات الذكاء الاصطناعي
SYSTEM_INSTRUCTION = """
أنتِ السكرتيرة التنفيذية لـ "شركة البرج المتألق للمقاولات العامة والتجارة العامة والنقل العام والاستثمارات العقارية".
أسلوبكِ: أنثوي، لبق، راقٍ بلهجة عراقية مهذبة ومختصرة جداً (خير الكلام ما قل ودل).
أجيبي باللغة العربية حصراً في حدود سطرين فقط، ووجّهي الزبون بلطف لترك اسمه ورقمه أو التواصل المباشر مع الإدارة عند الحاجة.
"""

def clean_think_tags(text: str) -> str:
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return cleaned.strip()

def get_active_model():
    try:
        models = client.models.list()
        available_ids = [m.id for m in models.data if "whisper" not in m.id and "guard" not in m.id]
        if available_ids:
            return available_ids[0]
    except Exception:
        pass
    return "llama-3.3-70b-versatile"

CURRENT_MODEL = get_active_model()

# 4. معالجة أمر البداية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "أهلاً وسهلاً بحضرتك نورتنا بشركة **البرج المتألق** ✨\n\n"
        "يسعدنا خدمتك، يرجى اختيار القسم المطلوب أو كتابة استفسارك مباشرة:"
    )
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=get_main_keyboard(), parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.message.reply_text(welcome_text, reply_markup=get_main_keyboard(), parse_mode="Markdown")

# 5. معالجة الضغط على الأزرار
async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "go_main":
        await start(update, context)
        return

    text_response = ""

    if data == "dept_contracting":
        text_response = (
            "🏗️ **قسم المقاولات العامة والإنشاءات**\n\n"
            "• تنفيذ أعمال البناء والتشطيبات المتكاملة وفق أحدث التصاميم.\n"
            "• إشراف هندسي وضمان شامل للمشاريع."
        )
    elif data == "dept_realestate":
        text_response = (
            "🏢 **قسم الاستثمارات العقارية**\n\n"
            "• إدارة وتطوير وتسويق العقارات والأراضي.\n"
            "• توفير فرص استثمارية مدروسة وبعوائد ممتازة."
        )
    elif data == "dept_trade":
        text_response = (
            "📦 **قسم التجارة العامة**\n\n"
            "• استيراد وتوريد وتأمين البضائع والسلع بدقة وسرعة وأسعار تنافسية."
        )
    elif data == "dept_transport":
        text_response = (
            "🚚 **قسم النقل العام والخدمات اللوجستية**\n\n"
            "• خدمات نقل بري وإدارة لوجستية آمنة لحركة البضائع والركاب."
        )
    elif data == "dept_contact":
        text_response = (
            "📞 **أرقام التواصل الرسمية المباشرة:**\n\n"
            "▫️ هاتف: `009647868006699`\n"
            "▫️ هاتف: `009647737006699`\n"
            "▫️ هاتف الإدارة: `07805509298`\n"
            "▫️ إيميل: RTCo2025@gmail.com"
        )
    elif data == "dept_social":
        text_response = (
            "🌐 **منصاتنا وحساباتنا الرسمية:**\n\n"
            "• الموقع: www.alburjmutalaliq.co\n"
            "• تيليجرام: https://t.me/RTCo2025\n"
            "• إنستغرام: https://www.instagram.com/rtco2025\n"
            "• تيك توك: https://www.tiktok.com/@rtco2025\n"
            "• فيسبوك: https://www.facebook.com/rtco2025"
        )

    await query.message.reply_text(
        text_response,
        reply_markup=get_back_keyboard(),
        parse_mode="Markdown"
    )

# 6. معالجة الرسائل وإرسال الإشعار للإدارة
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CURRENT_MODEL
    user = update.effective_user
    user_text = update.message.text

    try:
        completion = client.chat.completions.create(
            model=CURRENT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": user_text}
            ],
            temperature=0.4,
            max_tokens=300
        )
        raw_reply = completion.choices[0].message.content
        reply = clean_think_tags(raw_reply)
        await update.message.reply_text(reply, reply_markup=get_back_keyboard())
    except Exception:
        CURRENT_MODEL = get_active_model()
        completion = client.chat.completions.create(
            model=CURRENT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": user_text}
            ],
            temperature=0.4,
            max_tokens=300
        )
        raw_reply = completion.choices[0].message.content
        reply = clean_think_tags(raw_reply)
        await update.message.reply_text(reply, reply_markup=get_back_keyboard())

    # إرسال تقرير فوري لحسابك الخاص
    admin_summary = (
        f"📩 **استفسار جديد من عميل**\n\n"
        f"👤 **الاسم:** {user.full_name}\n"
        f"🔗 **اليوزر:** @{user.username if user.username else 'لا يوجد'}\n"
        f"🆔 **الآيدي:** `{user.id}`\n\n"
        f"💬 **نص الرسالة:**\n{user_text}\n\n"
        f"🤖 **رد السكرتيرة:**\n{reply}"
    )
    try:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_summary, parse_mode="Markdown")
    except Exception:
        pass

# 7. سيرفر الاستضافة
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"OK")

def start_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthHandler)
        server.serve_forever()
    except Exception:
        pass

if __name__ == '__main__':
    threading.Thread(target=start_server, daemon=True).start()
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.run_polling()
