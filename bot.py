"""
نظام السكرتيرة الذكية - شركة البرج المتألق
الملف: bot.py
التحديث: تقرير إداري ملخص وجوهري بعد 15 دقيقة خمول + إصلاح فحص المفتاح
"""

import os
import re
import asyncio
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

# ذاكرة المحادثة لكل مستخدم
user_conversations = {}
# مهام التوقيت لمراقبة الـ 15 دقيقة
inactivity_timers = {}

# 2. الأزرار والقوائم
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

# 3. توجيهات الذكاء الاصطناعي
SYSTEM_INSTRUCTION = """
أنتِ السكرتيرة التنفيذية والمستشارة الفنية لشركة "البرج المتألق للمقاولات العامة والاستثمارات العقارية والتجارة العامة والنقل العام".
أسلوبكِ: أنثوي، لبق، راقٍ، ومهذب جداً بلهجة عراقية محترمة وبيئة أعمال راقية (مثل: "يا أهلاً وسهلاً بحضرتك"، "تدلل/تدللين"، "يسعدنا نخدمك").

قواعد الإجابة:
1. أجيبي فوراً وبشكل مفصل ومباشر عن سؤال الزبون باللغة العربية مع تقديم معلومات هندسية وفنية وافية ومفيدة.
2. لا تضعي أرقام هواتف أو إيميل أو روابط في نهاية الأجوبة العادية لأن الزر الدائم موجود بالأسفل.
3. اذكري أرقام التواصل فقط إذا طلبها الزبون بصراحة.
4. حافظي على ترابط الحديث وسياق الجلسة بشكل متسلسل.
"""

def clean_think_tags(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    text = re.sub(r'<think>.*', '', text, flags=re.DOTALL)
    return text.strip()

def get_available_models():
    """جلب النماذج المتاحة من Groq"""
    try:
        models_data = client.models.list().data
        valid_models = []
        for m in models_data:
            mid = m.id.lower()
            if any(x in mid for x in ["whisper", "guard", "r1", "deepseek", "vision", "qwen-qwq"]):
                continue
            valid_models.append(m.id)
        if valid_models:
            return valid_models
    except Exception:
        pass
    return ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]

def generate_ai_reply(messages_payload):
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
            continue
    return f"عذراً، يرجى التأكد من صلاحية مفتاح الربط في السيرفر: {last_error[:60]}"

# 4. معالجة الإشعار بعد 15 دقيقة خمول
async def session_timeout_reporter(user_id: int, user_info: dict, context: ContextTypes.DEFAULT_TYPE):
    """انتظار 15 دقيقة (900 ثانية) بعد آخر رسالة ثم تلخيص وإرسال التقرير للإدارة"""
    await asyncio.sleep(900)
    
    if user_id not in user_conversations or not user_conversations[user_id]:
        return

    history = user_conversations[user_id]
    
    # تفريغ المحادثة كنص متسلسل
    dialog_text = ""
    for msg in history:
        sender = "الزبون" if msg["role"] == "user" else "السكرتيرة"
        dialog_text += f"{sender}: {msg['content']}\n"

    # استخدام Groq لإنشاء ملخص تنفيذي للمحادثة
    summary_prompt = f"""
قم بتحليل محادثة خدمة العملاء التالية لشركة 'البرج المتألق':
{dialog_text}

استخرج النقاط بدقة وبصيغة تقرير رسمي مختصر جداً:
1. ماذا كان يحتاج الزبون بالتحديد؟ (الطلب الجوهري)
2. كيف تمت إجابته والحل المقدم له؟
3. الإجراء المقترح للمتابعة من الإدارة (إن وجد).
"""
    try:
        summary_res = client.chat.completions.create(
            model=get_available_models()[0],
            messages=[{"role": "user", "content": summary_prompt}],
            temperature=0.3,
            max_tokens=400
        )
        executive_summary = clean_think_tags(summary_res.choices[0].message.content)
    except Exception:
        executive_summary = "تعذر توليد الملخص الآلي، يرجى الاطلاع على نص المحادثة الكامل أدناه."

    user_link = f"tg://user?id={user_id}"
    username_info = f"@{user_info['username']}" if user_info.get("username") else "لا يوجد يوزر"

    report_message = (
        f"📊 **تقرير جلسة استفسار مكتملة (بعد 15 دقيقة خمول)**\n\n"
        f"👤 **العميل:** [{user_info['name']}]({user_link})\n"
        f"🔗 **اليوزر:** {username_info}\n"
        f"🆔 **الآيدي:** `{user_id}`\n\n"
        f"📌 **الملخص الجوهري للمحادثة:**\n{executive_summary}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📝 **نص المحادثة المجمعة بالكامل:**\n{dialog_text[:2000]}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👉 [اضغط هنا لفتح محادثة مباشرة مع العميل]({user_link})"
    )

    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=report_message,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
    except Exception:
        pass

    # مسح الذاكرة بعد تصدير التقرير لبدء جلسة جديدة مستقبلاً
    user_conversations.pop(user_id, None)
    inactivity_timers.pop(user_id, None)

# 5. معالجات الأوامر والرسائل
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_conversations[user_id] = []
    
    # إلغاء أي مؤقت سابق إن وجد
    if user_id in inactivity_timers:
        inactivity_timers[user_id].cancel()
        inactivity_timers.pop(user_id, None)

    welcome_text = (
        "يا أهلاً وسهلاً بحضرتك نورتنا في شركة **البرج المتألق** ✨\n"
        "*(للمقاولات العامة • الاستثمارات العقارية • التجارة العامة • النقل العام)*\n\n"
        "يسعدنا استقبال استفساراتك وخدمتك على مدار الساعة.\n"
        "تفضل بكتابة سؤالك مباشرة 👇"
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
    if len(user_conversations[user_id]) > 10:
        user_conversations[user_id] = user_conversations[user_id][-10:]

    payload = [{"role": "system", "content": SYSTEM_INSTRUCTION}] + user_conversations[user_id]

    reply = generate_ai_reply(payload)
    user_conversations[user_id].append({"role": "assistant", "content": reply})

    await update.message.reply_text(reply, reply_markup=get_chat_persistent_keyboard())

    # إعادة ضبط مؤقت الـ 15 دقيقة مع كل رسالة جديدة
    if user_id in inactivity_timers:
        inactivity_timers[user_id].cancel()

    user_info = {
        "name": user.full_name,
        "username": user.username
    }
    # بدء عداد الخمول لمدة 15 دقيقة
    inactivity_timers[user_id] = asyncio.create_task(
        session_timeout_reporter(user_id, user_info, context)
    )

# 6. سيرفر فحص الصحة لتوافق Render و UptimeRobot
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

# 7. نقطة الانطلاق
if __name__ == '__main__':
    threading.Thread(target=start_server, daemon=True).start()
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.run_polling()
