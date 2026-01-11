import logging
import asyncio
import random
import os
import sys
from telegram.ext import ContextTypes

# --- [ حل مشكلة المسارات ] ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from config import Config
    from db import db
except ImportError:
    import config as Config
    from db import db

logger = logging.getLogger(__name__)

# --- [ القواميس الملكية ] ---
NAMES = ["أحمد", "سلا", "نور", "عمر", "مريم", "ياسين", "ليان", "سارة", "خالد", "جنا"]

MESSAGES_QUICK = [
    "👤 {name} ينتظرك الآن في لعبة XO.. هل تقبل التحدي؟ ❌⭕️",
    "🎲 {name} رمى النرد ويتحداك! هل يمكنك الفوز؟",
    "💬 {name} طلب التحدث معك في الدردشة العشوائية.. ادخل الآن!",
    "👋 {name}: الوو.. وينك؟",
    "✨ {name}: هلا، نتعارف؟",
    "🎮 {name}: هيا نلعب، أنا بانتظارك!"
]

MESSAGES_LONG = [
    "👑 الإدارة: لديك مكافأة لم تستلمها بعد! اذهب لقسم الجوائز 🎁",
    "⭐ يمكنك ربح 10 نجوم لكل صديق تدعوه.. ابدأ ببناء ثروتك الآن!",
    "🗣️ فتح موضوع نقاش ساخن في الغرف.. انضم وعبّر عن رأيك!",
    "📈 نصيحة: تحديث بياناتك الشخصية يجعلك تظهر بشكل أفخم!"
]

# --- [ وظائف الإرسال ] ---

async def send_to_random_users(bot, templates, count=5):
    """وظيفة مساعدة لاختيار مستخدمين والإرسال لهم"""
    try:
        if db.db is None: return
        all_users = list(db.db.users.find({}, {"user_id": 1}).limit(200))
        if not all_users: return

        targets = random.sample(all_users, min(len(all_users), count))
        for target in targets:
            user_id = target['user_id']
            name = random.choice(NAMES)
            text = random.choice(templates).format(name=name)
            try:
                await bot.send_message(chat_id=user_id, text=text, parse_mode="Markdown")
                await asyncio.sleep(1) # تجنب الحظر
            except: continue
    except Exception as e:
        logger.error(f"Error in vibrancy send: {e}")

# --- [ المهام المجدولة ] ---

async def vibrancy_scheduler(bot):
    # 1. تنبيه فوري عند تشغيل البوت
    logger.info("🚀 إرسال التنبيه الفوري عند التشغيل...")
    await send_to_random_users(bot, ["📢 تم تحديث الأنظمة الملكية! البوت متصل الآن ومستعد لخدمتكم 👑"])

    # 2. تنبيه بعد 20 ثانية
    await asyncio.sleep(20)
    logger.info("⏱️ إرسال تنبيه الـ 20 ثانية...")
    await send_to_random_users(bot, MESSAGES_QUICK)

    # 3. إنشاء المهام الدورية (تشغيل متوازي)
    asyncio.create_task(loop_every_interval(bot, 7200, MESSAGES_QUICK))      # كل ساعتين
    asyncio.create_task(loop_every_interval(bot, 18000, MESSAGES_LONG))     # كل 5 ساعات
    asyncio.create_task(loop_every_interval(bot, 86400, ["🌟 مكافأتك اليومية جاهزة! لا تنسَ استلامها."])) # كل يوم

async def loop_every_interval(bot, seconds, templates):
    """حلقة تكرار لفترة زمنية محددة"""
    while True:
        await asyncio.sleep(seconds)
        await send_to_random_users(bot, templates)

async def setup(application):
    """حقن النظام عند تشغيل البوت"""
    # نبدأ المجدول كمهمة في الخلفية
    asyncio.create_task(vibrancy_scheduler(application.bot))
    logger.info("✅ تم ضبط جداول الحيوية (فوري، 20ث، 2س، 5س، يومي)")
