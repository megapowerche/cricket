from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import logging
from datetime import datetime
import os
import traceback

# Enable logging with more details
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot_debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Define the services and their payment plans
SERVICES = [
    {
        "name": "Cricket VIP Tips",
        "plans": [
            ("Join Weekly", "VIP", "https://whop.com/checkout/plan_eBTHj4g6J1DAY/"),
            ("Join Monthly", "VIP", "https://whop.com/checkout/plan_50xJ6DzpNc4gp/"),
            ("Join 3 Months", "VIP", "https://whop.com/checkout/plan_6sxlf4aofEXAL/"),
            ("Join Life Time", "VIP", "https://whop.com/checkout/plan_YSNEgKjyX74KE/"),
        ],
    },
]

# Define the visitors file path with absolute path
VISITORS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "visitors.txt")

# Visitor tracking functions
def track_visit(user_id: int):
    """Record a visit in the text file"""
    timestamp = datetime.now().isoformat()
    try:
        logger.info(f"Tracking visit for user {user_id} to file {VISITORS_FILE}")
        with open(VISITORS_FILE, "a") as f:
            f.write(f"{user_id},{timestamp}\n")
        logger.info(f"Successfully tracked visit from user {user_id}")
    except Exception as e:
        logger.error(f"Failed to track visit: {str(e)}")
        logger.error(traceback.format_exc())

def get_stats():
    """Read statistics from the text file"""
    logger.info(f"Checking stats from file: {VISITORS_FILE}")

    if not os.path.exists(VISITORS_FILE):
        logger.warning(f"Visitors file does not exist at: {VISITORS_FILE}")
        return 0, 0

    try:
        with open(VISITORS_FILE, "r") as f:
            lines = f.readlines()

        logger.info(f"Read {len(lines)} lines from visitors file")

        if not lines:
            logger.info("Visitors file is empty")
            return 0, 0

        unique_users = set()
        total_visits = 0

        for i, line in enumerate(lines):
            if line.strip():
                try:
                    parts = line.strip().split(',')
                    if len(parts) >= 1:
                        user_id = parts[0]
                        unique_users.add(user_id)
                        total_visits += 1
                except Exception as e:
                    logger.error(f"Error processing line {i}: {line.strip()}: {str(e)}")

        logger.info(f"Stats calculated: {total_visits} total visits, {len(unique_users)} unique users")
        return total_visits, len(unique_users)
    except Exception as e:
        logger.error(f"Error reading stats: {str(e)}")
        logger.error(traceback.format_exc())
        return 0, 0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send main menu when the command /start is issued."""
    user = update.effective_user
    logger.info(f"Start command received from user {user.id}")
    track_visit(user.id)

    keyboard = []
    for index, service in enumerate(SERVICES):
        keyboard.append([InlineKeyboardButton(service["name"], callback_data=f"service_{index}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Please choose a service:", reply_markup=reply_markup)

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reset the bot to the main menu."""
    user = update.effective_user
    logger.info(f"Reset command received from user {user.id}")
    track_visit(user.id)

    keyboard = []
    for index, service in enumerate(SERVICES):
        keyboard.append([InlineKeyboardButton(service["name"], callback_data=f"service_{index}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Resetting to main menu. Please choose a service:", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses."""
    query = update.callback_query
    await query.answer()

    # Handle back to services button
    if query.data == "back_to_services":
        keyboard = []
        for index, service in enumerate(SERVICES):
            keyboard.append([InlineKeyboardButton(service["name"], callback_data=f"service_{index}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Please choose a service:", reply_markup=reply_markup)
        return

    # Extract the service index from the callback data
    data = query.data
    if not data.startswith("service_"):
        return
    service_index = int(data.split("_")[1])
    service = SERVICES[service_index]

    # Create buttons for each plan
    keyboard = []
    for plan in service["plans"]:
        plan_name, price, url = plan
        button_text = f"{plan_name} {price}"
        keyboard.append([InlineKeyboardButton(button_text, url=url)])

    # Add back button
    keyboard.append([InlineKeyboardButton("Back to Services", callback_data="back_to_services")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=f"Plans for {service['name']}:",
        reply_markup=reply_markup
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show statistics to admin"""
    user = update.effective_user
    logger.info(f"Stats command received from user ID: {user.id}")
    logger.info(f"Admin check: user ID {user.id} == 1274132255 ? {user.id == 1274132255}")

    # Remove this check temporarily for testing
    # if user.id != 1274132255:  # Your admin ID
    #     await update.message.reply_text("❌ Access denied: This command is for admins only.")
    #     return

    try:
        total, unique = get_stats()
        message = (
            f"📊 Bot Statistics:\n"
            f"• Total visits: {total}\n"
            f"• Unique users: {unique}\n"
            f"• Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"• File path: {VISITORS_FILE}\n"
            f"• File exists: {os.path.exists(VISITORS_FILE)}"
        )
        logger.info(f"Sending stats message: {message}")
        await update.message.reply_text(message)
    except Exception as e:
        error_msg = f"Error in stats command: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        await update.message.reply_text(f"⚠️ Error retrieving stats: {str(e)}")

async def debug(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Debug command to check file system and permissions"""
    user = update.effective_user
    logger.info(f"Debug command received from user {user.id}")

    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        files_in_dir = os.listdir(current_dir)

        debug_info = (
            f"🔍 Debug Information:\n"
            f"• Current directory: {current_dir}\n"
            f"• Visitors file path: {VISITORS_FILE}\n"
            f"• Visitors file exists: {os.path.exists(VISITORS_FILE)}\n"
            f"• Files in directory: {', '.join(files_in_dir)}\n"
        )

        if os.path.exists(VISITORS_FILE):
            with open(VISITORS_FILE, "r") as f:
                content = f.read()

            lines = content.strip().split('\n')
            sample = lines[:5] if len(lines) > 5 else lines

            debug_info += (
                f"• Visitors file size: {os.path.getsize(VISITORS_FILE)} bytes\n"
                f"• Number of lines: {len(lines)}\n"
                f"• Sample content (first 5 lines or less):\n"
            )

            for i, line in enumerate(sample):
                debug_info += f"  {i+1}: {line}\n"

        await update.message.reply_text(debug_info)
    except Exception as e:
        error_msg = f"Error in debug command: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        await update.message.reply_text(f"⚠️ Debug error: {str(e)}")

def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token("7783749537:AAFmxHDNntmDsxVOroT8iVStgdnrQcXhxzM").build()

    # Create visitors file if not exists
    try:
        logger.info(f"Checking if visitors file exists at {VISITORS_FILE}")
        if not os.path.exists(VISITORS_FILE):
            logger.info(f"Creating visitors file at {VISITORS_FILE}")
            with open(VISITORS_FILE, "w") as f:
                pass
            logger.info(f"Successfully created visitors.txt file at {VISITORS_FILE}")
        else:
            logger.info(f"Visitors file already exists at {VISITORS_FILE}")
    except Exception as e:
        logger.error(f"Failed to create/check visitors.txt: {str(e)}")
        logger.error(traceback.format_exc())

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("reset", reset))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("debug", debug))

    # Add callback query handler
    application.add_handler(CallbackQueryHandler(button))

    logger.info("Bot is starting up...")
    # Start the Bot
    application.run_polling()
    logger.info("Bot has shutdown")

if __name__ == "__main__":
    main()