import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, CallbackQueryHandler, TypeHandler, MessageHandler, filters
from config import Config

logger = logging.getLogger(__name__)

# --- [ الإعدادات ] ---
CHANNEL_ID = "@NN26S"
GROUP_ID = -1003493496120 
CHANNEL_LINK = "https://t.me/NN26S"
GROUP_LINK = "https://t.me/Anonymousa_Arabic"

async def setup(application):
    # حارس الاشتراك (الأولوية القصوى)
    application.add_handler(TypeHandler(Update, mandatory_guard), group=-100)
    # حذف رسائل الانضمام والمغادرة من المجموعة
    application.add_handler(MessageHandler(filters.StatusUpdate.ALL, clean_group_logs), group=-99)

async def clean_group_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف مخلفات الانضمام والمغادرة في المجموعة"""
    try:
        await update.message.delete()
    except:
        pass

async def check_status(bot, user_id):
    """فحص حالة الاشتراك في القناة والمجموعة منفصلين"""
    results = {"channel": False, "group": False}
    try:
        ch = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if ch.status in ['member', 'administrator', 'creator']: results["channel"] = True
        
        gr = await bot.get_chat_member(chat_id=GROUP_ID, user_id=user_id)
        if gr.status in ['member', 'administrator', 'creator']: results["group"] = True
    except: pass
    return results

async def send_admin_log(bot, user, action):
    """إشعار مختصر للمشرف"""
    try:
        text = f"👤 {user.first_name} (@{user.username or 'No'}) "
        text += "🆕 انضم للبوت" if action == "JOIN" else "✅ اكتمل اشتراكه"
        await bot.send_message(chat_id=Config.ADMIN_ID, text=text)
    except: pass

async def mandatory_guard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """منع القائمة الرئيسية وحجز البوت"""
    if not update.effective_user or update.effective_user.is_bot: return
    
    user = update.effective_user
    if user.id == Config.ADMIN_ID: return

    status = await check_status(context.bot, user.id)

    # إذا لم يكتمل الاشتراك
    if not (status["channel"] and status["group"]):
        if update.message and update.message.text == "/start":
            if not context.user_data.get('logged'):
                await send_admin_log(context.bot, user, "JOIN")
                context.user_data['logged'] = True

        # بناء الرسالة الذكية
        text = "🔒 **لتفعيل حسابك، يرجى اتباع الخطوات:**\n\n"
        if not status["channel"]:
            text += f"1️⃣ اشترك أولًا في القناة: [القناة الرسمية]({CHANNEL_LINK})\n"
        if not status["group"]:
            text += f"2️⃣ ثم انضم للمجموعة: [مجموعة النقاش]({GROUP_LINK})\n"
        
        text += "\n▶️ **بعد ذلك اضغط (تفعيل / Start)**"

        # أزرار الروابط
        keyboard = []
        if not status["channel"]:
            keyboard.append([InlineKeyboardButton("📢 القناة الرسمية", url=CHANNEL_LINK)])
        if not status["group"]:
            keyboard.append([InlineKeyboardButton("💬 مجموعة النقاش", url=GROUP_LINK)])
        
        # زر التفعيل الموحد
        keyboard.append([InlineKeyboardButton("▶️ Start | 🔓 تفعيل", url=f"https://t.me/{(await context.bot.get_me()).username}?start=verify")])

        if update.message:
            await update.message.reply_text(
                text, 
                reply_markup=InlineKeyboardMarkup(keyboard), 
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
        
        # إيقاف معالجة أي موديول آخر (بما في ذلك main.py) لضمان حجز البوت
        raise context.ApplicationHandlerStop
    
    # إذا اكتمل الاشتراك للتو
    if status["channel"] and status["group"] and not context.user_data.get('verified'):
        await send_admin_log(context.bot, user, "VERIFIED")
        context.user_data['verified'] = True

