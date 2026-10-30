# 🚀 دليل النشر — Contract-Guard ZeroBaran

<div dir="rtl">

## النشر على خادم سحابي مجاني

### الخيار 1: Render (مجاني، الأسهل)

1. ارفع المشروع إلى GitHub
2. اذهب إلى [render.com](https://render.com) وأنشئ حساباً
3. اختر **New → Web Service**
4. اربط مستودع GitHub
5. الإعدادات:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `streamlit run dashboard/streamlit_app.py --server.port $PORT --server.address 0.0.0.0`
   - **Plan:** Free
6. أضف متغيرات البيئة في **Environment**
7. انشر

### الخيار 2: Railway (مجاني للاستخدام الأولي)

1. اذهب إلى [railway.app](https://railway.app)
2. **New Project → Deploy from GitHub repo**
3. أضف متغيرات البيئة
4. الإعدادات:
   - **Build:** `pip install -r requirements.txt`
   - **Start:** `streamlit run dashboard/streamlit_app.py --server.port $PORT`

### الخيار 3: تشغيل محلي دائم (Raspberry Pi / خادم منزلي)

```bash
# تثبيت النظام كخدمة systemd
sudo nano /etc/systemd/system/contract-guard.service
```

```ini
[Unit]
Description=Contract-Guard ZeroBaran
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/Contract-Guard-ZeroBaran
ExecStart=/opt/Contract-Guard-ZeroBaran/venv/bin/streamlit run dashboard/streamlit_app.py --server.port 8501
Restart=on-failure
EnvironmentFile=/opt/Contract-Guard-ZeroBaran/.env

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable contract-guard
sudo systemctl start contract-guard
```

---

## النشر الكامل (البوت + اللوحة)

### 1. تشغيل البوت في الخلفية
```bash
nohup python -m src.delivery.telegram_bot > bot.log 2>&1 &
```

### 2. تشغيل لوحة Streamlit
```bash
streamlit run dashboard/streamlit_app.py --server.port 8501 --server.address 0.0.0.0
```

### 3. تفعيل GitHub Actions
- ارفع المشروع إلى GitHub
- أضف المفاتيح في `Settings → Secrets → Actions`
- فعّل الـ workflows

---

## إعداد Supabase

### 1. إنشاء المشروع
1. سجّل في [supabase.com](https://supabase.com)
2. **New Project**
3. اختر اسماً وكلمة مرور قوية لقاعدة البيانات
4. اختر المنطقة الأقرب (EU West للشرق الأوسط)

### 2. إنشاء الجداول
1. اذهب إلى **SQL Editor**
2. الصق محتوى `src/database/schema.sql`
3. اضغط **Run**

### 3. الحصول على المفاتيح
1. اذهب إلى **Settings → API**
2. انسخ:
   - **Project URL** → `SUPABASE_URL`
   - **anon public key** → `SUPABASE_KEY`

---

## إعداد بوت تليجرام

### 1. إنشاء البوت
```
1. افتح @BotFather في تليجرام
2. أرسل /newbot
3. اختر اسماً ومعرّفاً
4. احفظ التوكن
```

### 2. الحصول على Chat ID
```
1. افتح @userinfobot
2. أرسل أي رسالة
3. ستحصل على Chat ID
```

### 3. تفعيل البوت
أضف إلى `.env`:
```
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_CHAT_ID=123456789
```

---

## الأمان في الإنتاج

### 1. قيود RLS في Supabase
في الإنتاج، عدّل سياسات RLS لتقييد الوصول:
```sql
-- بدلاً من (true)، قيّد على المستخدم المصرّح له
CREATE POLICY "Authenticated only" ON contracts
    FOR ALL USING (auth.role() = 'authenticated');
```

### 2. حماية مفاتيح API
- لا ترفع ملف `.env` إلى GitHub (موجود في `.gitignore`)
- استخدم GitHub Secrets لـ Actions
- دور المفاتيح كل 90 يوماً

### 3. نسخ احتياطي لقاعدة البيانات
```bash
# نسخ يومي عبر Supabase Dashboard
# Settings → Database → Backups → Schedule
```

---

## مراقبة الأداء

### مؤشرات صحية
- ✅ البوت يستجيب خلال 3 ثوانٍ
- ✅ تحليل عقد 10 بنود خلال < 60 ثانية
- ✅ لوحة Streamlit تحمل في < 5 ثوانٍ
- ✅ Supabase ضمن الطبقة المجانية (500MB)

### سجلات الأخطاء
```bash
# سجل البوت
tail -f bot.log

# سجلات Streamlit
tail -f ~/.streamlit/streamlit.log

# سجلات GitHub Actions
# اذهب إلى Actions tab في المستودع
```

---

## استكشاف الأخطاء

| المشكلة | الحل |
|---------|------|
| `GEMINI_API_KEY not set` | تحقق من ملف `.env` |
| `Supabase connection failed` | تأكد من URL و Key |
| البوت لا يستجيب | تأكد من التوكن و Chat ID |
| تحليل بطيء | استخدم Groq بدلاً من Gemini |
| `rate limit exceeded` | Gemini: 15 طلب/دقيقة، انتظر |

---

## الترقية

### الانتقال من الطبقة المجانية
إذا تجاوزت الاستخدام المجاني:
1. **Gemini** → [ترقية مدفوعة](https://ai.google.dev/pricing)
2. **Supabase** → [خطة Pro](https://supabase.com/pricing) ($25/شهر)
3. **استضافة** → VPS بـ $5/شهر (DigitalOcean, Linode)

---

</div>
