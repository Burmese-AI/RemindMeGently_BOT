import logging
from telegram import Update
from telegram.ext import Application, ContextTypes, CommandHandler, CallbackContext, MessageHandler, filters
import datetime

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends an introduction message."""
    await update.message.reply_text('''
🤖 Welcome to RemindMeGently!

📋 Available commands:
/start /help /guide - Show this message
/reminder - List all your reminders
/addReminder - Add a new reminder
/removeReminder - Remove a reminder
    ''')

async def remind(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends the reminder message."""
    job = context.job
    reminder_name = job.data.get('reminder_name')
    await context.bot.send_message(job.chat_id, text=f"⏰ Reminder: {reminder_name}!")

async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Adds a new reminder."""
    chat_id = update.message.chat_id
    try:
        reminder_name = str(context.args[0])
        reminder_time = str(context.args[1])  # Assuming second argument is 24-hour format time

        existing_jobs = context.job_queue.get_jobs_by_name(f"{chat_id}_{reminder_name}")
        if existing_jobs:
            await update.message.reply_text("⚠️ Error: A reminder with that name already exists. Please choose another name.")
            return
        
        reminder_time = datetime.datetime.strptime(reminder_time, "%H:%M")
        current_time = datetime.datetime.now().time()
        if reminder_time.time() <= current_time:
            await update.message.reply_text("⚠️ Error: Please set a reminder time later than the current time.")
            return
        
        # Calculate timer
        reminder_datetime = datetime.datetime.combine(datetime.date.today(), reminder_time.time())
        timer = (reminder_datetime - datetime.datetime.now()).total_seconds()

        context.job_queue.run_once(remind, timer, chat_id=chat_id, name=f"{chat_id}_{reminder_name}", data={'reminder_name': reminder_name})
        
        # Confirmation
        await update.message.reply_text("✅ Reminder successfully set!")

    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Usage: /addReminder <name> <24hr_format_time>")

async def unset_reminder(update: Update, context: CallbackContext) -> None:
    """Removes a reminder."""
    if len(context.args) == 0:
        await update.message.reply_text("⚠️ Usage: /removeReminder <name>")
        return
    
    chat_id = update.message.chat_id
    reminder_name = context.args[0]
    jobs_to_unset = context.job_queue.get_jobs_by_name(f"{chat_id}_{reminder_name}")
    
    if not jobs_to_unset:
        await update.message.reply_text(f"❌ No reminders found with name '{reminder_name}'.")
        return
    
    for job in jobs_to_unset:
        job.schedule_removal()
    
    await update.message.reply_text(f"✅ Successfully removed reminder named '{reminder_name}'.")

async def reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lists all reminders for the user."""
    job_queue = context.job_queue
    chat_id = update.message.chat_id
    
    if not job_queue.jobs():
        await update.message.reply_text("📅 There are no reminders currently set.")
        return
    
    reminder_names = []
    for job in job_queue.jobs():
        if job.name.startswith(f"{chat_id}_"):
            reminder_names.append(job.name.split('_', 1)[1])
    
    reminders_list = "\n".join(reminder_names)
    await update.message.reply_text(f"📅 Your reminders:\n{reminders_list}")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles unknown commands."""
    await update.message.reply_text('''
❓ Sorry, I don't understand that command.

📋 Available commands:
/start /help /guide - Show this message
/reminder - List all your reminders
/addReminder - Add a new reminder
/removeReminder - Remove a reminder
    ''')

def main():
    # Create the Application
    application = Application.builder().token("7225084652:AAHIZ_SNXPux94tR42fpDy4XOaTK_EEUBes").build()

    # Adding handlers
    application.add_handler(CommandHandler(["start", "help", "guide"], start))
    application.add_handler(CommandHandler(["addReminder"], set_reminder))
    application.add_handler(CommandHandler(["removeReminder"], unset_reminder))
    application.add_handler(CommandHandler(["reminder"], reminders))
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
