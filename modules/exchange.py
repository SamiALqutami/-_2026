import sys
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes

# ضمان رؤية الملفات الرئيسية
sys.path.append(os.getcwd())
import database
import config

# النسبة الافتراضية للتبادل (3%)
EXCHANGE_PERCENTAGE = 0.03

async def register_exchange(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args # /exchange @channel_username 1000
    
    if len(args) < 2:
        await update.message.reply_text("❌ أرسل: /exchange @username [عدد_مشتركيك_الحالي]")
        return

    username = args[0]
    total_members = int(args[1])
    target = int(total_members * EXCHANGE_PERCENTAGE)

    conn = database.get_db()
    conn.execute('''INSERT OR REPLACE INTO exchange_channels 
                    (owner_id, username, total_members, target_joins) 
                    VALUES (?, ?, ?, ?)''', (user_id, username, total_members, target))
    conn.commit()

    await update.message.reply_text(
        f"✅ تم تسجيل قناتك في نظام التبادل الذكي.\n"
        f"📊 حجم القناة: {total_members}\n"
        f"🎯 الهدف المطلوب تحقيقه لك: {target} عضو (بنسبة 3%)"
    )

async def show_exchange_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = database.get_db()
    channel = conn.execute('SELECT * FROM exchange_channels WHERE owner_id=?', (user_id,)).fetchone()

    if not channel:
        await update.message.reply_text("❌ ليس لديك قناة مسجلة في التبادل.")
        return

    text = (
        f"📢 إحصائيات التبادل لقناتك {channel[2]}:\n"
        f"📥 استلمت: {channel[5]} عضو\n"
        f"📤 قدمت للنظام: {channel[6]} عضو\n"
        f"🎯 الهدف النهائي: {channel[4]} عضو"
    )
    await update.message.reply_text(text)

# دالة الاختيار الدائري (Round-Robin)
async def get_next_channel_for_ad(current_channel_size):
    conn = database.get_db()
    # اختيار قناة تقارب حجم القناة المعلن فيها لضمان العدالة
    # مع إعطاء الأولوية لمن لديه أقل عدد استلام (current_received)
    query = '''SELECT username FROM exchange_channels 
               WHERE is_active=1 AND current_received < target_joins
               ORDER BY ABS(total_members - ?) ASC, last_pushed ASC LIMIT 1'''
    result = conn.execute(query, (current_channel_size,)).fetchone()
    return result[0] if result else None

def setup(app):
    # حقن الأوامر تلقائياً في البوت الرئيسي
    app.add_handler(CommandHandler("exchange", register_exchange))
    app.add_handler(CommandHandler("status", show_exchange_status))
