from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def build_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Neue Meldung", callback_data='neue_meldung')],
        [InlineKeyboardButton("🏆 Bestenliste", callback_data='bestenliste')],
        [InlineKeyboardButton("📋 Meine Meldungen", callback_data='meine_meldungen')]
    ])

def build_back_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Zurück zum Menü", callback_data='back_to_menu')]
    ])
