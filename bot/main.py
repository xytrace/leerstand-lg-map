import json
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from bot.handlers.start import handle_start, handle_buttons
from bot.handlers.admin import (
    handle_ranking,
    handle_all_meldungen,
    handle_delete,
    handle_confirm,
)
from bot.handlers.meldung import handle_text, handle_photo, handle_button_callback

# Load config
with open("config.json") as f:
    config = json.load(f)

TOKEN = config["telegram_token"]

# Create Application
app = Application.builder().token(TOKEN).build()

# Register Handlers
app.add_handler(CommandHandler("start", handle_start))
app.add_handler(CommandHandler("ranking", handle_ranking))
app.add_handler(CommandHandler("meldungen", handle_all_meldungen))
app.add_handler(CommandHandler("loesche", handle_delete))
app.add_handler(CommandHandler("bestaetige", handle_confirm))

app.add_handler(CallbackQueryHandler(handle_buttons))
app.add_handler(CallbackQueryHandler(handle_button_callback))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

# Start polling
if __name__ == "__main__":
    print("🚀 Leerstand-Melde-Bot läuft...")
    app.run_polling()
