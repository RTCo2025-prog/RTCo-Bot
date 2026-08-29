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
            InlineKeyboardButton("📦 التجارة العامة والتوريد", callback_data="dept_trade"),
            InlineKeyboardButton("🚚 النقل والخدمات اللوجستية", callback_data="dept_transport")
        ],
        [
            InlineKeyboardButton("📞 أرقام الهواتف المباشرة", callback_data="dept_contact"),
            InlineKeyboardButton("🌐 منصات التواصل والموقع", callback_data="dept_social")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="go_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

# 3. توجيهات وهوية السكرتيرة الذكية التفصيلية
SYSTEM_INSTRUCTION = """
# الهوية والدور الأساسي
أنتِ السكرتيرة التنفيذية والمستشارة الرقمية لـ "شركة البرج المتألق للمقاولات العامة والتجارة العامة والنقل العام والاستثمارات العقارية".
أسلوبكِ: أنثوي، لبق، راقٍ، مهذب جداً، وواثق، وتتحدثين بلهجة عراقية محترمة وبيئة أعمال راقية (مثل: "يا أهلاً وسهلاً بحضرتك"، "نورتنا وحياك الله"، "تدلل/تدللين"، "يسعدنا جداً نخدمك").

---

# سياسة الرد والشرح للزبون (مهم جداً):
- لا تكتفي بكلمات عامة أو إحالة الزبون للاتصال مباشرة؛ بل قدّمي شرحاً وافياً ومفيداً يشرح إمكانيات الشركة وطريقة العمل في النقطة التي يسأل عنها.
- إذا سأل عن البناء أو المقاولات: وضّحي أن الشركة تنفذ الهيكل الأسود، التشطيبات الكاملة (تسليم مفتاح)، الديكورات الحديثة، مع تصاميم معمارية وإشراف هندسي يومي وضمان جودة.
- إذا سأل عن الاستثمار العقاري: وضّحي أن الشركة تقدم استشارات وتوفر فرصاً وأراضي وعقارات ذات عائد مجدٍ وتطوير عقاري آمن.
- إذا سأل عن التجارة والتوريد: اشرحي قدرة الشركة على توفير المواد الإنشائية والبضائع للشركات والمشاريع بأسعار تنافسية وسلاسل إمداد موثوقة.
- إذا سأل عن النقل: وضّحي توفير حلول النقل البري وإدارة الشحنات والأساطيل بأمان والتزام بالوقت.
- بالنسبة للأسعار: اشرحي العوامل التي يعتمد عليها السعر (المساحة، نوع المواد، المواصفات المطلوبة)، واقترحي عليه تزويدك بتفاصيل مشروعه، أو أخذ رقمه واسمه ليقوم المهندس/المختص بالتواصل معه وتقديم دراسة وكشف موقعي دقيق.

---

# بيانات وقنوات الشركة الرسمية:
- الهواتف: 009647868006699 | 009647737006699
- هاتف الإدارة: 07805509298
- الموقع: www.alburjmutalaliq.co
- الإيميل: RTCo2025@gmail.com
- تيليجرام: https://t.me/RTCo2025
- إنستغرام: https://www.instagram.com/rtco2025
- تيك توك: https://www.tiktok.com/@rtco2025
- فيسبوك: https://www.facebook.com/rtco2025
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

# 4. أمر البداية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "أهلاً وسهلاً بحضرتك نورتنا بشركة **البرج المتألق** للمقاولات العامة والاستثمارات العقارية والتجارة والنقل ✨\n\n"
        "تسعدني خدمتك والإجابة عن كل استفساراتك. تگدر تختار أحد الأقسام من الأزرار أدناه، أو تكتب سؤالك بالتفصيل هنا مباشرة 👇"
    )
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=get_main_keyboard(), parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.message.reply_text(welcome_text, reply_markup=get_main_keyboard(), parse_mode="Markdown")

# 5. معالجة الأزرار
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
            "🏗️ **قسم المقاولات العامة والإنشاءات:**\n\n"
            "نقدم حلولاً هندسية متكاملة تشمل:\n"
            "• أعمال الهيكل الإنشائي والخرسانات بدقة هندسية عالية.\n"
            "• التشطيبات الحديثة والمتكاملة (تسليم مفتاح ديلوكس).\n"
            "• التصاميم المعمارية والإنشائية، الديكورات الداخلية والواجهات الخارجية.\n"
            "• إشراف كادر هندسي مختص خطوة بخطوة مع ضمان الجودة.\n\n"
            "💬 *تگدر تكتب تفاصيل مساحة موقعك أو طلبك هنا، ويسعدني إجابتك فوراً.*"
        )
    elif data == "dept_realestate":
        text_response = (
            "🏢 **قسم الاستثمارات والتطوير العقاري:**\n\n"
            "• استشارات ودراسات جدوى اقتصادية للمشاريع العقارية.\n"
            "• تسويق، إدارة، وتطوير العقارات والأراضي السكنية والتجارية.\n"
            "• فرص استثمارية مدروسة تحقق أعلى عائد وقيمة مضافة لأموالك.\n\n"
            "💬 *حاب تستفسر عن بيع، شراء، أو استثمار معين؟ اكتبلي التفاصيل وبخدمتك.*"
        )
    elif data == "dept_trade":
        text_response = (
            "📦 **قسم التجارة العامة والتوريدات:**\n\n"
            "• استيراد وتأمين المواد الإنشائية ومستلزمات البناء عالية الجودة.\n"
            "• صفقات تجارية وسلاسل إمداد مستقرة للمشاريع والشركات.\n"
            "• أسعار تنافسية مع الالتزام التام بالمواصفات القياسية المعتمدة."
        )
    elif data == "dept_transport":
        text_response = (
            "🚚 **قسم النقل العام والخدمات اللوجستية:**\n\n"
            "• حلول النقل البري للبضائع والمواد بين المحافظات.\n"
            "• إدارة أساطيل النقل وتأمين مسارات آمنة ومنتظمة.\n"
            "• دقة في المواعيد ومرونة في تلبية الاحتياجات اللوجستية."
        )
    elif data == "dept_contact":
        text_response = (
            "📞 **قنوات الاتصال المباشرة:**\n\n"
            "▫️ هاتف: `009647868006699`\n"
            "▫️ هاتف: `009647737006699`\n"
            "▫️ هاتف الإدارة: `07805509298`\n"
            "▫️ البريد الإلكتروني: RTCo2025@gmail.com\n\n"
            "مكتبنا وكادرنا الفني والإداري بخدمتكم دوماً."
        )
    elif data == "dept_social":
        text_response = (
            "🌐 **منصاتنا وحساباتنا الرسمية:**\n\n"
            "• الموقع الإلكتروني: www.alburjmutalaliq.co\n"
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

# 6. معالجة الرسائل بذكاء وتفصيل مفيد
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
            temperature=0.6,
            max_tokens=800
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
            temperature=0.6,
            max_tokens=800
        )
        raw_reply = completion.choices[0].message.content
        reply = clean_think_tags(raw_reply)
        await update.message.reply_text(reply, reply_markup=get_back_keyboard())

    # إشعار الإدارة
    if ADMIN_CHAT_ID and ADMIN_CHAT_ID != "ضع_رقم_الآيدي_هنا":
        admin_summary = (
            f"📩 **استفسار جديد من عميل**\n\n"
            f"👤 **الاسم:** {user.full_name}\n"
            f"🔗 **اليوزر:** @{user.username if user.username else 'لا يوجد'}\n"
            f"🆔 **الآيدي:** `{user.id}`\n\n"
            f"💬 **سؤال الزبون:**\n{user_text}\n\n"
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
