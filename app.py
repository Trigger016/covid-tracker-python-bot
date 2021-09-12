from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.parsemode import ParseMode
import responses as res
import logging
from constants import API_KEY


print("Bot Starting...")
# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

#Defining Error Handler Function
def error(update, context):
    print(f"Update {update} error {context.error}")


def exception(update, context):
    try:
        message = update.message.text.lower()
        command_list = ["/start", 
                        "/help",
                        "/covid19", 
                        "/covid_id", 
                        "/berita", 
                        "/covid_world", 
                        "/notif", 
                        "/reset" ,
                        "/refresh"]

        if message not in command_list:
            suggest = res.suggestion(message, command_list)
            update.message.reply_text(text=f"Maksud anda <em>{suggest}</em>", 
                                      parse_mode=ParseMode.HTML)
    except(ValueError):
            update.message.reply_text(text="Perintah tidak terdaftar")

def main():
    # Keys Connector
    updater = Updater(API_KEY, use_context=True)
    dispatch = updater.dispatcher
    
    # Commands
    dispatch.add_handler(CommandHandler("start", res.start_command))
    dispatch.add_handler(CommandHandler("help", res.help_command))
    dispatch.add_handler(CommandHandler("covid19", res.info))
    dispatch.add_handler(CommandHandler("covid_id", res.indonesia))
    dispatch.add_handler(CommandHandler("berita", res.berita))
    dispatch.add_handler(CommandHandler("covid_world", res.status_comm))
    dispatch.add_handler(CommandHandler("notif", res.set_tracker))
    dispatch.add_handler(CommandHandler("reset", res.unset))
    dispatch.add_handler(CommandHandler("refresh", res.refresh))
    dispatch.add_handler(MessageHandler(Filters.text, exception))

    dispatch.add_error_handler(error)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()