"""
نظام السكرتيرة الذكية - شركة البرج المتألق
الملف: bot.py
التحديث: رسالة أولى ترحيبية مميزة + زر موحد (معلومات التواصل وأقسام الشركة) تحت كل رد
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

# =============================================================
# 1. إعدادات الثوابت ومفاتيح التوصيل البرمجي
# =============================================================
TELEGRAM_BOT_TOKEN = "8624313127:AAHtPRy05UNfL5_6Cv1ySiqfcT5eqRCTks0"
GROQ_API_KEY = "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"
ADMIN_CHAT_ID = "7822645247"

client = Groq(api_key=GROQ_API_KEY)

# ذاكرة سياق المحادثة لكل مستخدم
user_conversations = {}

# =============================================================
# 2. القوائم والأزرار التفاعلية (Keyboards)
# =============================================================

# الزر الدائم الذي يظهر أسفل كل رد للزبون
def get_chat_persistent_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("📋 معلومات التواصل وأقسام الشركة", callback_data="show_company_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# قائمة الأقسام ومعلومات التواصل الموسعة
def get_company_sections_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
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
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🔙 رجوع لأقسام الشركة", callback_data="show_company_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# =============================================================
# 3. توجيهات وهوية الذكاء الاصطناعي (System Prompt)
# =============================================================
SYSTEM_INSTRUCTION = """
# الهوية والدور الأساسي
أنتِ السكرتيرة التنفيذية والمستشارة الرقمية لـ "شركة البرج المتألق للمقاولات العامة والتجارة العامة والنقل العام والاستثمارات العقارية".
أسلوبكِ: أنثوي، لبق، راقٍ، مهذب جداً، وواثق، وتتحدثين بلهجة عراقية محترمة وبيئة أعمال راقية (مثل: "يا أهلاً وسهلاً بحضرتك"، "تدلل/تدللين"، "يسعدنا جداً نخدمك").

---

# ضوابط الردود:
1. **الإجابة المباشرة فقط**:
   - أجيبي بدقة وبشكل فني واحترافي عن سؤال العميل فقط.
   - لا تضعي أرقام هواتف، ولا بريداً إلكترونياً، ولا روابط في نهاية كل رسالة؛ لأن الزبون لديه زر تفاعلي دائم بالأسفل مخصص لذلك.
2. **متى تُذكر أرقام وبيانات الشركة كتابياً؟**:
   - فقط إذا سأل العميل عنها بنص مباشر وصريح (مثل: "انطوني الرقم"، "شلون اتصل بيكم؟").
3. **سياق الحوار المستمر**:
   - اربطي الإجابات ببعضها بسلاسة وطبيعية إذا سأل سؤالاً تكميلياً معتمداً على كلامك السابق دون الحاجة لتكرار التحيات والمقدمات.
4. **الأسعار**:
   - وضحي أنها ترتبط بالمواصفات الفنية والمساحة، ورحبي بتزويدك بتفاصيل طلبه لترتيب كشف هندسي دقيق.
"""

# =============================================================
# 4. دوال التنظيف واختيار النماذج
# =============================================================
def clean_think_tags(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    text = re.sub(r'<think>.*', '', text, flags=re.DOTALL)
    return text.strip()

def get_clean_model() -> str:
    try:
        models = client.models.list()
        for m in models.data:
            m_id = m.id.lower()
            if any(x in m_id for x in ["whisper", "guard", "r1", "deepseek", "reasoning", "qwen-qwq"]):
                continue
            return m.id
    except Exception:
        pass
    return "llama-3.3-70b-versatile"

CURRENT_MODEL = get_clean_model()

# =============================================================
# 5. معالجات الأحداث (الأوامر والأزرار والرسائل)
# =============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_conversations[user_id] = []  # تصفير الذاكرة لبدء جلسة جديدة
    
    # أول رسالة مميزة، أنيقة، ومختصرة للشركة
    first_message = (
        "يا أهلاً وسهلاً بحضرتك نورتنا في **شركة البرج المتألق** ✨\n"
        "*(للمقاولات العامة • الاستثمارات العقارية • التجارة العامة • النقل العام)*\n\n"
        "يسعدنا جداً استقبال استفساراتك وخدمتك على مدار الساعة.\n"
        "تفضل بكتابة سؤالك مباشرة، وسأجيبك بكل سرور 👇"
    )
    
    target = update.message if update.message else update.callback_query.message
    await target.reply_text(
        first_message,
        reply_markup=get_chat_persistent_keyboard(),
        parse_mode="Markdown"
    )

async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "show_company_menu":
        menu_text = (
            "🏛️ **شركة البرج المتألق**\n"
            "يرجى اختيار القسم للاطلاع على تفاصيله أو بيانات الاتصال:"
        )
        await query.message.reply_text(
            menu_text,
            reply_markup=get_company_sections_keyboard(),
            parse_mode="Markdown"
        )
        return

    elif data == "hide_menu":
        await query.message.delete()
        return

    text_response = ""
    if data == "dept_contracting":
        text_response = (
            "🏗️ **قسم المقاولات العامة والإنشاءات:**\n\n"
            "• تنفيذ الهيكل الإنشائي والخرساني بدقة هندسية.\n"
            "• تشطيبات متكاملة ديلوكس وتسليم مفتاح.\n"
            "• تصاميم معمارية وديكورات داخلية عصرية.\n"
            "• إشراف كادر هندسي معتمد وضمان شامل للجودة."
        )
    elif data == "dept_realestate":
        text_response = (
            "🏢 **قسم الاستثمارات والتطوير العقاري:**\n\n"
            "• دراسات جدوى واستشارات عقارية متخصصة.\n"
            "• فرص استثمارية وأراضٍ وعقارات ذات عائد استثماري ممتاز.\n"
            "• إدارة وتطوير وتسويق المشاريع العقارية."
        )
    elif data == "dept_trade":
        text_response = (
            "📦 **قسم التجارة العامة والتوريدات:**\n\n"
            "• استيراد وتأمين المواد الإنشائية ومستلزمات البناء.\n"
            "• صفقات تجارية وسلاسل إمداد موثوقة للشركات والمشاريع.\n"
            "• أسعار تنافسية مطابقة لأعلى المواصفات القياسية."
        )
    elif data == "dept_transport":
        text_response = (
            "🚚 **قسم النقل العام والخدمات اللوجستية:**\n\n"
            "• نقل بري آمن وموثوق للمواد والبضائع.\n"
            "• إدارة الأساطيل وتأمين المسارات بين المحافظات.\n"
            "• التزام تام بالمواعيد وسرعة في التوصيل."
        )
    elif data == "dept_contact":
        text_response = (
            "📞 **أرقام الهواتف وقنوات الاتصال:**\n\n"
            "▫️ هاتف: `009647868006699`\n"
            "▫️ هاتف: `009647737006699`\n"
            "▫️ هاتف الإدارة: `07805509298`\n"
            "▫️ البريد الإلكتروني: RTCo2025@gmail.com\n\n"
            "يسعدنا تواصلكم واستقبالكم دائماً."
        )
    elif data == "dept_social":
        text_response = (
            "🌐 **منصاتنا وموقعنا الرسمي:**\n\n"
            "• الموقع الإلكتروني: www.alburjmutalaliq.co\n"
            "• تيليجرام: https://t.me/RTCo2025\n"
            "• إنستغرام: https://www.instagram.com/rtco2025\n"
            "• تيك توك: https://www.tiktok.com/@rtco2025\n"
            "• فيسبوك: https://www.facebook.com/rtco2025"
        )

    await query.message.reply_text(
        text_response,
        reply_markup=get_back_to_menu_keyboard(),
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CURRENT_MODEL
    user = update.effective_user
    user_text = update.message.text
    user_id = user.id

    # إدارة الذاكرة وسياق الحوار
    if user_id not in user_conversations:
        user_conversations[user_id] = []

    user_conversations[user_id].append({"role": "user", "content": user_text})

    # الحفاظ على آخر 6 رسائل للسرعة وتكامل السياق
    if len(user_conversations[user_id]) > 6:
        user_conversations[user_id] = user_conversations[user_id][-6:]

    messages_payload = [{"role": "system", "content": SYSTEM_INSTRUCTION}] + user_conversations[user_id]

    try:
        completion = client.chat.completions.create(
            model=CURRENT_MODEL,
            messages=messages_payload,
            temperature=0.4,
            max_tokens=800
        )
        raw_reply = completion.choices[0].message.content
        reply = clean_think_tags(raw_reply)
        if not reply:
            reply = "تفضل حضرتك، شلون أگدر أساعدك؟"
    except Exception:
        CURRENT_MODEL = get_clean_model()
        completion = client.chat.completions.create(
            model=CURRENT_MODEL,
            messages=messages_payload,
            temperature=0.4,
            max_tokens=800
        )
        raw_reply = completion.choices[0].message.content
        reply = clean_think_tags(raw_reply)
        if not reply:
            reply = "تفضل حضرتك، شلون أگدر أساعدك؟"

    user_conversations[user_id].append({"role": "assistant", "content": reply})

    # إرسال الرد المباشر للزبون مع الزر التفاعلي الدائم في النهاية
    await update.message.reply_text(
        reply,
        reply_markup=get_chat_persistent_keyboard()
    )

    # إرسال إشعار للإدارة فوراً مع رابط محادثة الزبون
    if ADMIN_CHAT_ID:
        user_link = f"tg://user?id={user.id}"
        username_text = f"@{user.username}" if user.username else "لا يوجد (استخدم الرابط المباشر)"

        admin_summary = (
            f"📩 **استفسار جديد من زبون**\n\n"
            f"👤 **الاسم:** [{user.full_name}]({user_link})\n"
            f"🔗 **اليوزر:** {username_text}\n"
            f"🆔 **الآيدي:** `{user.id}`\n\n"
            f"💬 **سؤال الزبون:**\n{user_text}\n\n"
            f"🤖 **رد السكرتيرة:**\n{reply}\n\n"
            f"👉 [اضغط هنا لمراسلة الزبون مباشرة]({user_link})"
        )
        try:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=admin_summary,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
        except Exception:
            pass

# =============================================================
# 6. سيرفر فحص الصحة لتوافق الاستضافة (Keep-Alive)
# =============================================================
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

# =============================================================
# 7. نقطة الانطلاق والتشغيل
# =============================================================
if __name__ == '__main__':
    threading.Thread(target=start_server, daemon=True).start()
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.run_polling()
