from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.db.supabase_client import get_or_create_user

def build_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Neue Meldung", callback_data='neue_meldung')],
        [InlineKeyboardButton("🏆 Bestenliste", callback_data='bestenliste')],
        [InlineKeyboardButton("📋 Meine Meldungen", callback_data='meine_meldungen')]
    ])

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_user = update.effective_user
    telegram_id, alias, user_id = await get_or_create_user(tg_user.id, tg_user.username or "")
    context.user_data["user_id"] = user_id

    welcome = f"Willkommen zurück, {alias}! 👋" if alias else "Willkommen! 👋"
    text = f"{welcome}\n\n🏠 *Leerstand-Melde-Bot*\n\nWähle eine Option:"
    markup = build_main_menu()

    # CASE 1: called via /start
    if update.message:
        await update.message.reply_text(text, reply_markup=markup, parse_mode='Markdown')
    # CASE 2: called via callback button
    elif update.callback_query:
        try:
            await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode='Markdown')
        except Exception:
            await update.callback_query.message.reply_text(text, reply_markup=markup, parse_mode='Markdown')

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'back_to_menu':
        from . import start
        await start.handle_start(update, context)
        context.user_data.clear()
    elif data == 'noop':
        pass
    else:
        # ✅ Let the router in main.py handle everything else
        # 🔁 How? Re-dispatch the query:
        from telegram.ext import CallbackQueryHandler

        # re-dispatch this callback manually to the fallback handler
        handler = CallbackQueryHandler(handle_button_callback)
        await handler.callback(update, context)

