from flask import Flask
import threading
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, Filters

# Telegram Token এবং Admin ID
TOKEN = "7463988311:AAHNpqounyuEsZsOs9G8dOWlyH4MqyiqA7o"   # <-- এখানে তোমার টোকেন বসাও
ADMIN_ID = 7647930808               # <-- এখানে তোমার Telegram আইডি বসাও

# নোটিফিকেশন অনুমতি তালিকা
user_notification_permission = {}

# Flask App for Keep Alive
app = Flask('')

@app.route('/')
def home():
    return "🤖 Bot is Alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    thread = threading.Thread(target=run_flask)
    thread.start()

# Logging সেটআপ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# START Command
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    keyboard = InlineKeyboardButton("🤝🏻 Accept Agreement", callback_data='accept_agreement')
    agreement_msg = (
        f"👋 হ্যালো *{user.first_name}*!\n\n"
        "এই বট ব্যবহার করতে হলে আমাদের Terms & Conditions মেনে নিতে হবে।\n"
        "👉 নিচে Accept বোতামে ক্লিক করে সম্মতি দিন।"
    )
    update.message.reply_text(
        agreement_msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

# Button Callback Handler
def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()

    if query.data == 'accept_agreement':
        keyboard = [
            [InlineKeyboardButton("✅ Allow Notifications", callback_data='allow_notifications')],
            [InlineKeyboardButton("❌ Decline", callback_data='decline_notifications')]
        ]
        query.edit_message_text(
            "✅ Agreement Accepted!\n\n"
            "আপনি কি নোটিফিকেশন পেতে চান? নিচের অপশন থেকে নির্বাচন করুন।",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif query.data == 'allow_notifications':
        user_notification_permission[user_id] = True
        query.edit_message_text("🔔 Notifications Enabled!")
    elif query.data == 'decline_notifications':
        user_notification_permission[user_id] = False
        query.edit_message_text("🚫 Notifications Disabled.")

# Admin Broadcast with Image + Text + Button
def broadcast(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("❌ এই কমান্ড ব্যবহারের অনুমতি নেই।")
        return

    if not context.args or '|' not in ' '.join(context.args):
        update.message.reply_text(
            "❗ ফরম্যাট ভুল।\n"
            "সঠিক ব্যবহার:\n"
            "/broadcast <image_url> | <caption> | <button_text> | <button_url>"
        )
        return

    try:
        raw = ' '.join(context.args)
        image_url, caption, button_text, button_url = map(str.strip, raw.split('|', 3))

        keyboard = InlineKeyboardButton(button_text, url=button_url)
        markup = InlineKeyboardMarkup(keyboard)

        count = 0
        for uid, allowed in user_notification_permission.items():
            if allowed:
                try:
                    context.bot.send_photo(
                        chat_id=uid,
                        photo=image_url,
                        caption=f"📢 {caption}",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=markup
                    )
                    count += 1
                except Exception as e:
                    logging.error(f"Couldn't send to {uid}: {e}")
                    continue

        update.message.reply_text(f"✅ বার্তা পাঠানো হয়েছে {count} জনকে।")

    except Exception as e:
        update.message.reply_text("❌ ত্রুটি হয়েছে। লগ চেক করুন।")
        logging.error("Broadcast error:", exc_info=e)

# Help
def help_command(update: Update, context: CallbackContext):
    update.message.reply_text(
        "/start - বট চালু\n"
        "/help - সাহায্য\n"
        "/broadcast <image_url> | <caption> | <button_text> | <button_url> - (Admin only)"
    )

# Error Logger
def error_handler(update: object, context: CallbackContext):
    logging.error(msg="Error:", exc_info=context.error)

# Main Bot Runner
def main():
    keep_alive()  # Flask Keep Alive চালু করো
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(CommandHandler("broadcast", broadcast, Filters.user(user_id=ADMIN_ID), pass_args=True))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_error_handler(error_handler)

    updater.start_polling()
    logging.info("🤖 Bot is running...")
    updater.idle()

if __name__ == '__main__':
    main()
