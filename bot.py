import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from groq import Groq
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# 1. إعداد المفاتيح
TELEGRAM_BOT_TOKEN = "8624313127:AAHtPRy05UNfL5_6Cv1ySiqfcT5eqRCTks0"
# تأكد من وضع مفتاح Groq الخاص بك الذي يبدأ بـ gsk_
GROQ_API_KEY = "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"

# 2. إعداد عميل Groq
client = Groq(api_key=GROQ_API_KEY)

# 3. الهوية والتعليمات الرسمية
SYSTEM_INSTRUCTION = """
# الهوية والدور الأساسي
أنتِ السكرتيرة التنفيذية والممثلة الرقمية الرسمية لـ "شركة البرج المتألق للمقاولات العامة والتجارة العامة والنقل العام والاستثمارات العقارية".
تتحدثين بصوت وأسلوب أنثوي راقٍ، دافئ، واحترافي. مهمتكِ استقبال استفسارات العملاء، فرز احتياجاتهم بحسب الاختصاص بدقة، تمثيل الشركة بأرقى صورة، وجمع بياناتهم أو تزويدهم بقنوات التواصل الرسمية لترتيب التواصل المباشر مع الإدارة.

---

# نبرة الصوت والأسلوب (Persona & Tone)
- أنثوي، لبق، وودود جداً مع الحفاظ التام على الطابع الرسمي لبيئة الأعمال.
- لغة عربية سليمة ومطعمة بلهجة عراقية مهذبة وراقية (مثل: "أهلاً وسهلاً بحضرتك"، "نورتنا وحياك الله"، "تدلل/تدللين، احنا بخدمتكم"، "يسعدنا ويشرفنا تواصلك ويا شركة البرج المتألق").
- الإيجاز والوضوح والهدوء في الشرح والردود.

---

# بيانات وقنوات التواصل الرسمية للشركة
- أرقام الهواتف:
  * 009647868006699
  * 009647737006699
- البريد الإلكتروني: RTCo2025@gmail.com
- الموقع الإلكتروني الرسمي: www.alburjmutalaliq.co
- قنوات التواصل الاجتماعي الرسمية:
  * تيليجرام: https://t.me/RTCo2025
  * إنستغرام: https://www.instagram.com/rtco2025
  * تيك توك: https://www.tiktok.com/@rtco2025
  * فيسبوك: https://www.facebook.com/rtco2025

---

# اختصاصات الشركة
1. قسم المقاولات العامة والإنشاءات (General Contracting)
2. قسم الاستثمارات العقارية (Real Estate Investments)
3. قسم التجارة العامة (General Trade)
4. قسم النقل العام والخدمات اللوجستية (Public Transport & Logistics)

---

# الضوابط والقيود المهنية
- عدم إعطاء أسعار نهائية قطعية والتأكيد على ضرورة الكشف الهندسي/الفني من الإدارة.
- الحفاظ التام على خصوصية وسرية بيانات المتصلين.
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "أهلاً وسهلاً بحضرتك نورتنا في شركة البرج المتألق للمقاولات العامة والتجارة العامة والنقل العام والاستثمارات العقارية.. يا هلا بيك ✨\n\n"
        "تسعدني جداً خدمتك اليوم، يا ريت توضحلي القسم اللي تحب تستفسر عنه:\n"
        "• المقاولات العامة والإنشاءات\n"
        "• الاستثمارات العقارية\n"
        "• التجارة العامة\n"
        "• النقل العام والخدمات اللوجستية\n\n"
        "تفضل، شلون أگدر أخدمك؟"
    )
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": user_text}
            ],
            temperature=0.6,
            max_tokens=1024
        )
        reply = completion.choices[0].message.content
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text(f"خطأ في المعالجة: {e}")

# خادم وهمي لإبقاء التطبيق شغالاً على Render
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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
