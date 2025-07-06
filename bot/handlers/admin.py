from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.db.supabase_client import top_five, get_user_meldungen, confirm_meldung, delete_meldung
from bot.util.helpers import build_main_menu

ADMIN_USERNAMES = {"ohne_u", "vicquick"}  # Adjust as needed

def build_ranking_keyboard():
    rows = top_five()
    buttons = []
    medals = ["🥇", "🥈", "🥉", "4.", "5."]
    if rows:
        for i, (alias, pts) in enumerate(rows):
            medal = medals[i] if i < len(medals) else f"{i+1}."
            buttons.append([InlineKeyboardButton(f"{medal} {alias} – {pts} Pkt", callback_data="noop")])
    else:
        buttons.append([InlineKeyboardButton("Noch keine Einträge", callback_data="noop")])
    buttons.append([InlineKeyboardButton("🔙 Zurück zum Menü", callback_data='back_to_menu')])
    return InlineKeyboardMarkup(buttons)

async def handle_ranking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏆 *Aktuelle Bestenliste:*",
        reply_markup=build_ranking_keyboard(),
        parse_mode="Markdown"
    )

async def handle_all_meldungen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    all_reports = get_user_meldungen(None)
    if not all_reports:
        await update.message.reply_text("Noch keine Meldungen vorhanden.")
        return

    for m in all_reports:
        caption = f"#{m['id']} – {m['adresse']}\n🏠 Lage: {m['wohnungslage']}\n⏰ Dauer: {m['dauer']}\n✅ Bestätigt: {m['bestaetigungen']}x"
        try:
            if m["image_url"]:
                await update.message.reply_photo(m["image_url"], caption=caption)
            else:
                await update.message.reply_text(caption)
        except:
            await update.message.reply_text(f"❌ Foto nicht verfügbar\n{caption}")

async def handle_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Verwende /bestaetige <ID>")
        return

    try:
        mid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Ungültige ID")
        return

    success = confirm_meldung(mid)
    if not success:
        await update.message.reply_text("❌ Meldung nicht gefunden.")
        return

    await update.message.reply_text(
        f"✅ Meldung #{mid} bestätigt! (+3 Punkte für den Melder)",
        reply_markup=build_main_menu()
    )

async def handle_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username or ""
    if username not in ADMIN_USERNAMES:
        await update.message.reply_text("❌ Nicht autorisiert.")
        return

    if not context.args:
        await update.message.reply_text("Verwendung: /loesche <ID>")
        return

    try:
        mid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Ungültige ID")
        return

    success = delete_meldung(mid)
    if not success:
        await update.message.reply_text("❌ Meldung nicht gefunden.")
    else:
        await update.message.reply_text(f"✅ Meldung #{mid} gelöscht.")
