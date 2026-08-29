import os
import threading
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# 1. إعداد المفاتيح
TELEGRAM_BOT_TOKEN = "8624313127:AAHtPRy05UNfL5_6Cv1ySiqfcT5eqRCTks0"
# انسخ المفتاح كاملاً من الصورة هنا
GEMINI_API_KEY = "AQ.Ab8RN6IAm6jqbKTM3Omz16-hwFinws_7dhKs0rhZRRfKgVVmBg"

# 2. الهوية ونظام التعليمات للسكرتيرة
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
2. الاستماع لاحتياج العميل بلطف وجمع بياناته (الاسم، رقم الهاتف، المحافظة، تفاصيل الطلب).
3. تزويد العميل بالقنوات الرسمية عند الحاجة.

---

# الضوابط والقيود المهنية
- عدم إعطاء أسعار نهائية قطعية والتأكيد على ضرورة الكشف الهندسي/الفني من الإدارة.
- الحفاظ التام على خصوصية وسرية بيانات المتصلين.
"""

def generate_gemini_reply(prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "system_instruction": {
            "parts": [{"text": SYSTEM_INSTRUCTION}]
        },
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }
    
    res = requests.post(url, headers=headers, json=payload, timeout=30)
    if res.status_code == 200:
        data = res.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    else:
        # محاولة عبر مسار الـ Authorization Header لدعم الـ Auth Keys
        auth_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GEMINI_API_KEY}"
        }
        alt_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
        res_auth = requests.post(alt_url, headers=auth_headers, json=payload, timeout=30)
        if res_auth.status_code == 200:
            data = res_auth.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        
        return f"عذراً، حدث خطأ: {res.text}"

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
    bot_reply = generate_gemini_reply(user_text)
    await update.message.reply_text(bot_reply)

# سيرفر وهمي لإبقاء التطبيق شغالاً على Render
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"OK")

def start_health_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthHandler)
        server.serve_forever()
    except Exception:
        pass

if __name__ == '__main__':
    threading.Thread(target=start_health_server, daemon=True).start()
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
