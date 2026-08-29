import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from google import genai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# المفاتيح
TELEGRAM_BOT_TOKEN = "8624313127:AAHtPRy05UNfL5_6Cv1ySiqfcT5eqRCTks0"
GEMINI_API_KEY = "AQ.Ab8RN6JrSt2als432M6wZqQX2q6F2KBUJvCKF3QNtFquKMXzbw"


# التعليمات الرسمية للسكرتيرة
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

# بيانات وقنوات التواصل الرسمية للشركة (تُقدّم للعميل عند الطلب أو الحاجة)
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

# اختصاصات الشركة (الرؤية، الرسالة، والأهداف)

### 1. قسم المقاولات العامة والإنشاءات (General Contracting)
* الرؤية: بناء منشآت ومشاريع هندسية متينة وعصرية تطبق أرقى المعايير الفنية والجمالية.
* الرسالة: تنفيذ أعمال البناء، التشطيبات، والتصاميم الهندسية بكفاءة عالية وفق جداول زمنية دقيقة وإشراف هندسي متكامل.
* الهدف: تلبية احتياجات الأفراد والشركات في تشييد وتطوير العقارات والمشاريع بجودة تضمن الاستدامة ورضا العميل.

### 2. قسم الاستثمارات العقارية (Real Estate Investments)
* الرؤية: خلق فرص استثمارية عقارية آمنة وواعدة تحقق أعلى عائد وقيمة مضافة.
* الرسالة: تقديم استشارات وخدمات تطوير، تسويق، وإدارة العقارات والأراضي برؤية استثمارية واضحة ومدروسة.
* الهدف: توجيه المستثمرين والراغبين بالتملك نحو أفضل الخيارات العقارية المناسبة لميزانياتهم وتطلعاتهم.

### 3. قسم التجارة العامة (General Trade)
* الرؤية: التميز والموثوقية كشريك استراتيجي في توريد وتأمين البضائع والمنتجات.
* الرسالة: ربط الأسواق بمنتجات وسلع عالية الجودة من خلال سلاسل توريد معتمدة وصفقات تجارية رصينة.
* الهدف: تزويد السوق والمشاريع بكافة المواد والمتطلبات التجارية بدقة وسرعة وأسعار تنافسية.

### 4. قسم النقل العام والخدمات اللوجستية (Public Transport & Logistics)
* الرؤية: توفير حلول نقل متطورة، آمنة وفعالة تسهم في تسهيل الحركة اللوجستية.
* الرسالة: تقديم خدمات نقل بري وتوزيع وإدارة حركة الأساطيل مع مراعاة أعلى معايير السلامة والالتزام بالوقت.
* الهدف: دعم سلاسل الإمداد ونقل الركاب والبضائع بمرونة تامة وتكاليف مدروسة.

---

# مسار المحادثة والتعامل مع العميل (Workflow)
1. الترحيب وتحديد القسم المطلوب.
2. الاستماع للعميل وجمع بياناته (الاسم، رقم الهاتف، المحافظة، تفاصيل الطلب).
3. تزويد العميل بالقنوات الرسمية عند الحاجة.

---

# الضوابط والقيود المهنية
- عدم إعطاء أسعار نهائية قطعية والتأكيد على ضرورة الكشف الهندسي/الفني.
- الحفاظ على خصوصية وسرية بيانات المتصلين.
"""

client = genai.Client(api_key=GEMINI_API_KEY)

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
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_text,
            config={"system_instruction": SYSTEM_INSTRUCTION}
        )
        await update.message.reply_text(response.text)
    except Exception:
        await update.message.reply_text(
            "عذراً، حدث خلل بسيط في الاتصال.. تكدر تتواصل ويانا مباشرة عبر الهاتف: 009647868006699 أو تعيد إرسال رسالتك بعد لحظات."
        )

# خادم وهمي لمنصة Render لتجاوز مشكلة Port Timeout
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"OK")

def start_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

if __name__ == '__main__':
    threading.Thread(target=start_server, daemon=True).start()
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
