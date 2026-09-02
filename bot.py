"""
نظام السكرتيرة الذكية - شركة البرج المتألق
الملف: bot.py
الإصدار المصحح: كشف النماذج الديناميكي + حل مشكلة الرد الثابت
"""

import os
import re
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from groq import Groq
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# 1. المفاتيح والمعرفات
TELEGRAM_BOT_TOKEN = "8624313127:AAHtPRy05UNfL5_6Cv1ySiqfcT5eqRCTks0"
GROQ_API_KEY = "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"
ADMIN_CHAT_ID = "7822645247"

client = Groq(api_key=GROQ_API_KEY)
user_conversations = {}

# 2. الأزرار والقوائم التفاعلية
def get_chat_persistent_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 معلومات التواصل وأقسام الشركة", callback_data="show_company_menu")]
    ])

def get_company_sections_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🏗️ المقاولات والإنشاءات", callback_data="dept_contracting"),
            InlineKeyboardButton("🏢 الاستثمارات العقارية", callback_data="dept_realestate")
        ],
        [
            InlineKeyboardButton("📦 التجارة العامة والتوريد", callback_data="dept_trade"),
            InlineKeyboardButton("🚚 النقل والخدمات اللوجستية", callback_data="dept_transport")
        ],
        [
            InlineKeyboardButton("📞 أرقام الهواتف المباشرة", callback_data="dept_contact"),
            InlineKeyboardButton("🌐 منصات التواصل والموقع", callback_data="dept_social")
        ],
        [
            InlineKeyboardButton("🔙 إغلاق القائمة", callback_data="hide_menu")
        ]
    ])

def get_back_to_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 رجوع لأقسام الشركة", callback_data="show_company_menu")]
    ])

# 3. تعليمات الذكاء الاصطناعي
SYSTEM_INSTRUCTION = """
أنتِ السكرتيرة التنفيذية والمستشارة الفنية لشركة "البرج المتألق للمقاولات العامة والاستثمارات العقارية والتجارة العامة والنقل العام".
أسلوبكِ: أنثوي، لبق، راقٍ، ومهذب جداً بلهجة عراقية محترمة وبيئة أعمال راقية (مثل: "يا أهلاً وسهلاً بحضرتك"، "تدلل/تدللين"، "يسعدنا نخدمك").

قواعد الإجابة:
1. أجيبي فوراً وبشكل مفصل ومباشر عن سؤال الزبون باللغة العربية.
   - إذا سأل عن مواد البناء (مثل الطابوق، السمنت، الحديد، التشطيبات): اشرحي الأنواع والاستخدامات الهندسية ومميزاتها بدقة ومعلومات وافية ومفيدة.
2. لا تضعي أرقام هواتف أو إيميل أو روابط في نهاية الأجوبة العادية لأن الزر الدائم موجود بالأسفل.
3. اذكري أرقام التواصل فقط إذا طلبها الزبون بصراحة.
4. حافظي على ترابط الحديث إذا كان السؤال تكميلياً لما قبله.
"""

def clean_think_tags(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    text = re.sub(r'<think>.*', '', text, flags=re.DOTALL)
    return text.strip()

def get_available_models():
    """جلب قائمة الموديلات الصالحة للاستخدام تلقائياً من سيرفر Groq"""
    try:
        models_data = client.models.list().data
        valid_models = []
        for m in models_data:
            mid = m.id.lower()
            # استبعاد نماذج الصوت والتفكير والصور
            if any(x in mid for x in ["whisper", "guard", "r1", "deepseek", "vision", "qwen-qwq"]):
                continue
            valid_models.append(m.id)
        if valid_models:
            return valid_models
    except Exception as e:
        print(f"Error fetching models: {e}")
    # نماذج احتياطية في حال تعذر القائمة
    return ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "mixtral-8x7b-32768"]

def generate_ai_reply(messages_payload):
    """توليد الرد الحقيقي وتجربة النماذج المتاحة فعلياً"""
    models = get_available_models()
    last_error = ""
    for model_name in models:
        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=messages_payload,
                temperature=0.5,
                max_tokens=800
            )
            raw = completion.choices[0].message.content
            cleaned = clean_think_tags(raw)
            if cleaned:
                return cleaned
        except Exception as e:
            last_error = str(e)
            print(f"Failed model {model_name}: {e}")
            continue

    # في حال فشل كل النماذج يظهر تفصيل الخطأ للتصحيح بدلاً من الرسالة الثابتة
    return f"عذراً، حدث خطأ فني أثناء المعالجة ({last_error[:80]}). يرجى المحاولة مرة ثانية."

# 4. معالجات الأحداث
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_conversations[user_id] = []
    
    welcome_text = (
        "يا أهلاً وسهلاً بحضرتك نورتنا في شركة **البرج المتألق** ✨\n"
        "*(للمقاولات العامة • الاستثمارات العقارية • التجارة العامة • النقل العام)*\n\n"
        "يسعدنا استقبال استفساراتك وخدمتك. تفضل بكتابة سؤالك مباشرة 👇"
    )
    target = update.message if update.message else update.callback_query.message
    await target.reply_text(welcome_text, reply_markup=get_chat_persistent_keyboard(), parse_mode="Markdown")

async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "show_company_menu":
        await query.message.reply_text(
            "🏛️ **شركة البرج المتألق**\nيرجى اختيار القسم للاطلاع على التفاصيل:",
            reply_markup=get_company_sections_keyboard(),
            parse_mode="Markdown"
        )
        return
    elif data == "hide_menu":
        await query.message.delete()
        return

    responses = {
        "dept_contracting": "🏗️ **قسم المقاولات العامة والإنشاءات:**\n\n• تنفيذ الهيكل الإنشائي والخرساني بدقة هندسية.\n• تشطيبات متكاملة ديلوكس وتسليم مفتاح.\n• تصاميم معمارية وديكورات داخلية عصرية.\n• إشراف كادر هندسي معتمد وضمان شامل للجودة.",
        "dept_realestate": "🏢 **قسم الاستثمارات والتطوير العقاري:**\n\n• دراسات جدوى واستشارات عقارية متخصصة.\n• فرص استثمارية وأراضٍ وعقارات ذات عائد استثماري ممتاز.\n• إدارة وتطوير وتسويق المشاريع العقارية.",
        "dept_trade": "📦 **قسم التجارة العامة والتوريدات:**\n\n• استيراد وتأمين المواد الإنشائية ومستلزمات البناء.\n• صفقات تجارية وسلاسل إمداد موثوقة للشركات والمشاريع.\n• أسعار تنافسية مطابقة لأعلى المواصفات القياسية.",
        "dept_transport": "🚚 **قسم النقل العام والخدمات اللوجستية:**\n\n• نقل بري آمن وموثوق للمواد والبضائع.\n• إدارة الأساطيل وتأمين المسارات بين المحافظات.\n• التزام تام بالمواعيد وسرعة في التوصيل.",
        "dept_contact": "📞 **أرقام الهواتف وقنوات الاتصال:**\n\n▫️ هاتف: `009647868006699`\n▫️ هاتف: `009647737006699`\n▫️ هاتف الإدارة: `07805509298`\n▫️ البريد الإلكتروني: RTCo2025@gmail.com",
        "dept_social": "🌐 **منصاتنا وموقعنا الرسمي:**\n\n• الموقع: www.alburjmutalaliq.co\n• تليجرام: https://t.me/RTCo2025\n• إنستغرام وتيك توك وفيسبوك: @rtco2025"
    }

    resp = responses.get(data, "")
    if resp:
        await query.message.reply_text(resp, reply_markup=get_back_to_menu_keyboard(), parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_text = update.message.text
    user_id = user.id

    if user_id not in user_conversations:
        user_conversations[user_id] = []

    user_conversations[user_id].append({"role": "user", "content": user_text})
    if len(user_conversations[user_id]) > 6:
        user_conversations[user_id] = user_conversations[user_id][-6:]

    payload = [{"role": "system", "content": SYSTEM_INSTRUCTION}] + user_conversations[user_id]

    reply = generate_ai_reply(payload)
    user_conversations[user_id].append({"role": "assistant", "content": reply})

    await update.message.reply_text(reply, reply_markup=get_chat_persistent_keyboard())

    # إشعار الإدارة الفوري
    if ADMIN_CHAT_ID:
        try:
            user_link = f"tg://user?id={user.id}"
            username_info = f"@{user.username}" if user.username else "لا يوجد يوزر"
            admin_msg = (
                f"📩 استفسار جديد من زبون\n\n"
                f"👤 الاسم: {user.full_name}\n"
                f"🔗 اليوزر: {username_info}\n"
                f"🆔 الآيدي: `{user.id}`\n\n"
                f"💬 سؤال الزبون:\n{user_text}\n\n"
                f"🤖 رد السكرتيرة:\n{reply}\n\n"
                f"👉 مراسلة الزبون: {user_link}"
            )
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_msg, disable_web_page_preview=True)
        except Exception:
            pass

# 5. خادم الويب للـ Keep-Alive
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
