import os
import re
import time
import html
import logging
import threading
from collections import defaultdict

import requests
import telebot
from telebot import types

from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route("/")
def home():
    return "I am 👿 DEMON 👿 HOSTING BOT"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_flask, daemon=True)
    t.start()
    print("Flask Keep-Alive server started.")


# ==================================================
# BMT - NUMBER TO INFO PRO
# Developer: @Unkonwn_BMT
# ==================================================


# ================= CONFIGURATION ==================

BOT_TOKEN ="9230294564:AAENJRoAd_c_mZMCqeEHkhOoaHLJxrfiaxA"

API_URL = os.getenv(
    "NUMBER_INFO_API",
    "https://gajarbotol.site/apis/unknown.php"
)

ADMIN_IDS = [7276206449]

DEVELOPER = "@Unkonwn_BMT"
BOT_NAME = "BMT - Number To Info"

COOLDOWN = 5
API_TIMEOUT = 20

MAX_NUMBER_LENGTH = 15
MIN_NUMBER_LENGTH = 10

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("BMT_NUMBER_INFO")


if (
    not BOT_TOKEN
    or BOT_TOKEN == "PASTE_NEW_BOT_TOKEN_HERE"
):
    raise SystemExit(
        "ERROR: Configure BOT_TOKEN first!"
    )


# ================= BOT INITIALIZATION =============

bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="HTML",
    threaded=True
)

lock = threading.Lock()

stats = {
    "searches": 0,
    "errors": 0,
    "users": set(),
    "chats": set()
}

last_request = defaultdict(float)


# ================= TEXT UTILITIES =================

def clean_api_text(value):
    """
    Remove the unwanted API bot username
    from all string fields.
    """

    if not isinstance(value, str):
        return value

    value = re.sub(
        r"@num_1nfo_bd_bot",
        "",
        value,
        flags=re.IGNORECASE
    )

    value = re.sub(
        r"\s*\(\s*\)",
        "",
        value
    )

    value = re.sub(
        r"[ \t]{2,}",
        " ",
        value
    )

    return value.strip()


def clean_api_data(data):
    """
    Clean strings in a dictionary,
    including nested dictionaries and lists.
    """

    if isinstance(data, dict):
        return {
            key: clean_api_data(value)
            for key, value in data.items()
        }

    if isinstance(data, list):
        return [
            clean_api_data(item)
            for item in data
        ]

    if isinstance(data, str):
        return clean_api_text(data)

    return data


def safe(value, default="Not available"):
    """
    Escape HTML before inserting API text
    into Telegram messages.
    """

    if value is None:
        return default

    value = str(value).strip()

    if not value:
        return default

    return html.escape(value[:150])


def get_value(data, key, default="Not available"):
    value = data.get(key)

    if value is None or str(value).strip() == "":
        return default

    return value


# ================= NUMBER VALIDATION ===============

def normalize_number(number):
    """
    Accept a number containing 10-15 digits.
    Spaces, parentheses, dots and hyphens
    are ignored.
    """

    number = re.sub(
        r"[\s().-]",
        "",
        number
    )

    if number.startswith("00"):
        number = "+" + number[2:]

    if not re.fullmatch(r"\+?\d{10,15}", number):
        return None

    return number


def number_digits(number):
    return re.sub(r"\D", "", str(number))


# ================= USER STATISTICS ================

def register_user(message):
    with lock:
        if message.from_user:
            stats["users"].add(
                message.from_user.id
            )

        stats["chats"].add(
            message.chat.id
        )


def increase_error():
    with lock:
        stats["errors"] += 1


def increase_search():
    with lock:
        stats["searches"] += 1


# ================= INLINE KEYBOARDS ===============

def result_keyboard(number):
    digits = number_digits(number)

    keyboard = types.InlineKeyboardMarkup(
        row_width=2
    )

    if digits:
        keyboard.add(
            types.InlineKeyboardButton(
                "🟢 Open WhatsApp",
                url=f"https://wa.me/{digits}"
            ),
            types.InlineKeyboardButton(
                "✈️ Open Telegram",
                url=f"https://t.me/{digits}"
               ) 
            
        )

    keyboard.add(
        types.InlineKeyboardButton(
            "🔎 Search Again",
            callback_data="search_again"
        ),
        types.InlineKeyboardButton(
            "ℹ️ About BMT",
            callback_data="about"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "👨‍💻 Developer",
            url="https://t.me/Unkonwn_BMT"
        )
    )

    return keyboard


def home_keyboard():
    keyboard = types.InlineKeyboardMarkup(
        row_width=2
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "📖 How To Use",
            callback_data="help"
        ),
        types.InlineKeyboardButton(
            "ℹ️ About",
            callback_data="about"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "👨‍💻 Developer",
            url="https://t.me/Unkonwn_BMT"
        )
    )

    return keyboard


# ================= API REQUEST =====================

def get_number_info(number):
    """
    Request information from the configured API.
    """

    response = requests.get(
        API_URL,
        params={
            "number": number
        },
        timeout=API_TIMEOUT,
        headers={
            "User-Agent": "BMT-Number-To-Info/2.0"
        }
    )

    response.raise_for_status()

    data = response.json()

    if not isinstance(data, dict):
        raise ValueError(
            "API returned an invalid response."
        )

    # Clean unwanted username in every field.
    data = clean_api_data(data)

    return data


# ================= PREMIUM RESULT UI ===============

def format_result(data, searched_number):
    
     name = safe( 
         get_value(data, "name")
     )
     number = safe(
        get_value(data, "number", searched_number)
    )
     international = safe(
        get_value(data, "international_format")
    )
     country = safe(
        get_value(data, "country")
    )
     carrier = safe(
        get_value(data, "carrier")
    )
     number_type = safe(
        get_value(data, "type")
    )
     timestamp = safe(
        get_value(data, "timestamp")
    )
     return (
  "╭━━━━━━━━━━━━━━━━━━━━╮\n"
        "┃ ⚡ <b>BMT - NUMBER TO INFO</b>\n"
        "┃ 💎 <i>Premium Lookup Interface</i>\n"
        "╰━━━━━━━━━━━━━━━━━━━━╯\n\n"

        "👤 <b>Name</b>\n"
        f"└ <code>{name}</code>\n\n"

        "📱 <b>Phone Number</b>\n"
        f"└ <code>{number}</code>\n\n"

        "🌐 <b>International Format</b>\n"
        f"└ <code>{international}</code>\n\n"

        "🌍 <b>Country</b>\n"
        f"└ {country}\n\n"

        "📡 <b>Carrier</b>\n"
        f"└ {carrier}\n\n"

        "🗂 <b>Number Type</b>\n"
        f"└ {number_type}\n\n"

        "🕒 <b>API Timestamp</b>\n"
        f"└ <code>{timestamp}</code>\n\n"

        "━━━━━━━━━━━━━━━━━━━━\n"
        "🛡️ <i>API data may be incomplete or inaccurate.</i>\n"
        "ℹ️ WhatsApp links do not verify account existence.\n\n"

        "⚡ <b>Powered by BMT</b>\n"
        f"👨‍💻 <b>Developer:</b> {DEVELOPER}"
    )


# ================= LOADING ANIMATION ===============

def show_loading(chat_id, message_id):
    """
    Show a short progress animation.
    """

    frames = [
        (
            "╭━━━━━━━━━━━━━━━━━━━━╮\n"
            "┃ 🔎 <b>BMT SEARCH</b>\n"
            "╰━━━━━━━━━━━━━━━━━━━━╯\n\n"
            "▰▱▱▱▱  <i>Initializing...</i>"
        ),
        (
            "╭━━━━━━━━━━━━━━━━━━━━╮\n"
            "┃ ⚡ <b>BMT SEARCH</b>\n"
            "╰━━━━━━━━━━━━━━━━━━━━╯\n\n"
            "▰▰▱▱▱  <i>Processing request...</i>"
        ),
        (
            "╭━━━━━━━━━━━━━━━━━━━━╮\n"
            "┃ 🌐 <b>BMT SEARCH</b>\n"
            "╰━━━━━━━━━━━━━━━━━━━━╯\n\n"
            "▰▰▰▱▱  <i>Connecting to API...</i>"
        ),
        (
            "╭━━━━━━━━━━━━━━━━━━━━╮\n"
            "┃ 💎 <b>BMT SEARCH</b>\n"
            "╰━━━━━━━━━━━━━━━━━━━━╯\n\n"
            "▰▰▰▰▰  <i>Fetching metadata...</i>"
        )
    ]

    for frame in frames:
        try:
            bot.edit_message_text(
                frame,
                chat_id,
                message_id
            )

            time.sleep(0.25)

        except Exception:
            # Telegram may reject an unchanged frame.
            continue


# ================= START COMMAND ===================

@bot.message_handler(commands=["start"])
def start_command(message):
    register_user(message)

    text = (
        "╭━━━━━━━━━━━━━━━━━━━━╮\n"
        "┃ ⚡ <b>BMT - NUMBER TO INFO</b>\n"
        "┃ 💎 <i>Premium Bot Interface</i>\n"
        "╰━━━━━━━━━━━━━━━━━━━━╯\n\n"

        "👋 <b>Welcome to BMT!</b>\n\n"

        "🔎 <b>How to use</b>\n"
        "Send a command like:\n\n"

        "<code>/info 018XXXXXXXX</code>\n\n"

        "🌐 International format:\n"
        "<code>/info +88018XXXXXXXX</code>\n\n"

        "✨ Features\n"
        "├ ⚡ Animated search interface\n"
        "├ 🌍 Country and carrier metadata\n"
        "├ 👥 Group and private chat support\n"
        "└ 💎 Premium result layout\n\n"

        "🛡️ Use only for lawful purposes.\n\n"

        f"👨‍💻 <b>Developer:</b> {DEVELOPER}"
    )

    bot.reply_to(
        message,
        text,
        reply_markup=home_keyboard()
    )


# ================= HELP COMMAND ====================

@bot.message_handler(commands=["help"])
def help_command(message):
    register_user(message)

    text = (
        "╭━━━━━━━━━━━━━━━━━━━━╮\n"
        "┃ 📖 <b>BMT HELP CENTER</b>\n"
        "╰━━━━━━━━━━━━━━━━━━━━╯\n\n"

        "🔎 <b>Search command</b>\n"
        "<code>/info NUMBER</code>\n\n"

        "Example:\n"
        "<code>/info 018XXXXXXXX</code>\n\n"

        "🌐 International format is also accepted.\n\n"

        "📌 <b>Other commands</b>\n"
        "├ /start — Open the bot\n"
        "├ /help — Show instructions\n"
        "├ /info — Request number metadata\n"
        "└ /stats — Admin statistics\n\n"

        f"👨‍💻 Developer: {DEVELOPER}"
    )

    bot.reply_to(
        message,
        text,
        reply_markup=home_keyboard()
    )


# ================= INFO COMMAND ====================

@bot.message_handler(commands=["info"])
def info_command(message):
    register_user(message)

    if not message.from_user:
        return

    parts = message.text.split(
        maxsplit=1
    )

    if len(parts) < 2:
        bot.reply_to(
            message,
            "❌ <b>NUMBER REQUIRED</b>\n\n"
            "Usage:\n"
            "<code>/info 018XXXXXXXX</code>"
        )
        return

    number = normalize_number(
        parts[1].strip()
    )

    if not number:
        bot.reply_to(
            message,
            "❌ <b>INVALID NUMBER FORMAT</b>\n\n"
            "Please enter a number containing "
            "10–15 digits.\n\n"
            "Example:\n"
            "<code>/info 018XXXXXXXX</code>"
        )
        return

    key = (
        message.chat.id,
        message.from_user.id
    )

    now = time.monotonic()

    if now - last_request[key] < COOLDOWN:
        bot.reply_to(
            message,
            "⏳ <b>Please wait!</b>\n\n"
            "Try again in a few seconds."
        )
        return

    last_request[key] = now

    status = bot.reply_to(
        message,
        (
            "╭━━━━━━━━━━━━━━━━━━━━╮\n"
            "┃ 🔎 <b>BMT SEARCH</b>\n"
            "╰━━━━━━━━━━━━━━━━━━━━╯\n\n"
            "▰▱▱▱▱ <i>Starting...</i>"
        )
    )

    try:
        # Loading animation
        show_loading(
            message.chat.id,
            status.message_id
        )

        # Fetch API metadata
        data = get_number_info(number)

        if not data.get("success"):
            increase_error()

            bot.edit_message_text(
                (
                    "╭━━━━━━━━━━━━━━━━━━━━╮\n"
                    "┃ ⚠️ <b>NO RESULT</b>\n"
                    "╰━━━━━━━━━━━━━━━━━━━━╯\n\n"
                    "The API did not return a successful result.\n"
                    "Please try again later.\n\n"
                    f"👨‍💻 {DEVELOPER}"
                ),
                message.chat.id,
                status.message_id
            )
            return

        result = format_result(
            data,
            number
        )

        result_number = (
            data.get("number") or number
        )

        bot.edit_message_text(
            result,
            message.chat.id,
            status.message_id,
            reply_markup=result_keyboard(
                str(result_number)
            ),
            disable_web_page_preview=True
        )

        increase_search()

        logger.info(
            "Successful metadata request in chat %s",
            message.chat.id
        )

    except requests.Timeout:
        increase_error()

        logger.warning(
            "Number metadata API timed out."
        )

        safe_edit(
            message.chat.id,
            status.message_id,
            (
                "⏱️ <b>REQUEST TIMEOUT</b>\n\n"
                "The API took too long to respond.\n"
                "Please try again later."
            )
        )

    except requests.RequestException as error:
        increase_error()

        logger.warning(
            "API connection error: %s",
            error
        )

        safe_edit(
            message.chat.id,
            status.message_id,
            (
                "⚠️ <b>API CONNECTION ERROR</b>\n\n"
                "Could not connect to the API.\n"
                "Check your internet connection and retry."
            )
        )

    except ValueError as error:
        increase_error()

        logger.warning(
            "Invalid API response: %s",
            error
        )

        safe_edit(
            message.chat.id,
            status.message_id,
            (
                "⚠️ <b>INVALID API RESPONSE</b>\n\n"
                "The API returned unexpected data."
            )
        )

    except Exception:
        increase_error()

        logger.exception(
            "Unexpected error in info_command"
        )

        safe_edit(
            message.chat.id,
            status.message_id,
            (
                "⚠️ <b>SOMETHING WENT WRONG</b>\n\n"
                "Please try again later."
            )
        )


# ================= SAFE MESSAGE EDIT ===============

def safe_edit(chat_id, message_id, text):
    try:
        bot.edit_message_text(
            text,
            chat_id,
            message_id,
            disable_web_page_preview=True
        )

    except Exception:
        logger.exception(
            "Could not edit status message."
        )

        try:
            bot.send_message(
                chat_id,
                text
            )
        except Exception:
            logger.exception(
                "Could not send fallback message."
            )


# ================= CALLBACK BUTTONS ===============

@bot.callback_query_handler(
    func=lambda call: call.data in (
        "help",
        "about",
        "search_again"
    )
)
def callback_handler(call):
    try:
        bot.answer_callback_query(
            call.id
        )
    except Exception:
        pass

    if call.data == "help":
        text = (
            "📖 <b>BMT HELP</b>\n\n"
            "Use this command:\n"
            "<code>/info 018XXXXXXXX</code>\n\n"
            "The bot supports group commands and private chats."
        )

    elif call.data == "search_again":
        text = (
            "🔎 <b>SEARCH AGAIN</b>\n\n"
            "Send another command:\n"
            "<code>/info NUMBER</code>"
        )

    else:
        text = (
            "╭━━━━━━━━━━━━━━━━━━━━╮\n"
            "┃ ⚡ <b>BMT - NUMBER TO INFO</b>\n"
            "╰━━━━━━━━━━━━━━━━━━━━╯\n\n"
            "A bot for displaying available phone-number "
            "metadata returned by its configured API.\n\n"
            "🛡️ Personal names are displayed.\n"
            "ℹ️ WhatsApp and Telegram links do not verify account existence.\n\n"
            f"👨‍💻 Developer: {DEVELOPER}"
        )

    try:
        bot.send_message(
            call.message.chat.id,
            text,
            disable_web_page_preview=True
        )
    except Exception:
        logger.exception(
            "Callback response failed."
        )


# ================= ADMIN STATISTICS ================

@bot.message_handler(commands=["stats"])
def stats_command(message):
    register_user(message)

    if not message.from_user:
        return

    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(
            message,
            "⛔ <b>ADMIN ONLY</b>"
        )
        return

    with lock:
        searches = stats["searches"]
        errors = stats["errors"]
        users = len(stats["users"])
        chats = len(stats["chats"])

    text = (
        "╭━━━━━━━━━━━━━━━━━━━━╮\n"
        "┃ 📊 <b>BMT ADMIN PANEL</b>\n"
        "╰━━━━━━━━━━━━━━━━━━━━╯\n\n"

        f"🔎 Successful requests: <code>{searches}</code>\n"
        f"⚠️ Errors: <code>{errors}</code>\n"
        f"👤 Users seen: <code>{users}</code>\n"
        f"💬 Chats seen: <code>{chats}</code>\n\n"

        "ℹ️ Statistics reset when the bot restarts.\n\n"
        f"👨‍💻 Developer: {DEVELOPER}"
    )

    bot.reply_to(
        message,
        text
    )


# ================= UNKNOWN COMMAND ================

@bot.message_handler(
    func=lambda message: (
        bool(message.text)
        and message.text.startswith("/")
    )
)
def unknown_command(message):
    bot.reply_to(
        message,
        "❓ <b>Unknown command</b>\n\n"
        "Use /help to see available commands."
    )


# ================= CONNECTION RETRY ===============

def run_bot():
    logger.info(
        "%s is starting...",
        BOT_NAME
    )

    while True:
        try:
            bot.infinity_polling(
                skip_pending=True,
                timeout=30,
                long_polling_timeout=20,
                logger_level=logging.WARNING
            )

        except KeyboardInterrupt:
            logger.info(
                "Bot stopped by user."
            )
            break

        except Exception:
            logger.exception(
                "Telegram connection failed."
            )

            logger.info(
                "Retrying connection in 5 seconds..."
            )

            time.sleep(5)


# ================= MAIN ===========================

if __name__ == "__main__":
    keep_alive()
    run_bot()
