import os
import uuid
import re
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.db.supabase_client import get_or_create_user, add_points, save_meldung, get_user_meldungen, supabase
from bot.util.helpers import build_main_menu, build_back_menu
from bot.util.geocode import geocode_address


def validate_address(addr: str):
    if not re.match(r"^[^\d]+ \d+[a-zA-Z]?$", addr.strip()):
        return "Format ungültig. Beispiel: Musterstraße 12"
    return None


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    tg_user = update.effective_user
    telegram_id, alias, user_id = await get_or_create_user(tg_user.id, tg_user.username or "")
    context.user_data["user_id"] = user_id

    if context.user_data.get("waiting_for_name"):
        if len(text) < 2 or len(text) > 30:
            await update.message.reply_text("❌ Der Username muss zwischen 2 und 30 Zeichen lang sein.\nBitte versuche es erneut:")
            return
        supabase.table("users").update({"alias": text}).eq("id", user_id).execute()
        context.user_data["waiting_for_name"] = False
        await update.message.reply_text(f"Perfekt, {text}! ✅\n\nBitte gib nun die Adresse des Leerstands ein:")
        context.user_data["meldung_step"] = "adresse"
        return

    step = context.user_data.get("meldung_step")

    if step == "adresse":
        error = validate_address(text)
        if error:
            await update.message.reply_text(f"❌ {error}\nBitte nochmals eingeben:")
            return
        context.user_data["adresse"] = text
        await update.message.reply_text("🏠 Wie ist die Wohnungslage? (z.B. 3. OG, Hinterhaus, etc.)")
        context.user_data["meldung_step"] = "wohnungslage"

    elif step == "wohnungslage":
        context.user_data["wohnungslage"] = text
        await update.message.reply_text(
            "📸 Optional: Schicke ein Foto oder tippe auf 'Überspringen':",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Überspringen", callback_data="skip_photo")]])
        )
        context.user_data["meldung_step"] = "foto"

    elif step == "foto":
        await update.message.reply_text("Bitte schicke ein Foto oder tippe auf 'Überspringen'.")

    elif step == "dauer":
        dauer = text
        adresse = context.user_data.get("adresse")
        wohnungslage = context.user_data.get("wohnungslage")
        img_path = context.user_data.get("img_path")

        lat, lon = await geocode_address(adresse)
        if lat is None or lon is None:
            await update.message.reply_text("❌ Adresse konnte nicht geokodiert werden.")
            return

        status = await save_meldung(
            user_id=user_id,
            local_img_path=img_path,
            adresse=adresse,
            wohnungslage=wohnungslage,
            dauer=dauer,
            lat=lat,
            lon=lon
        )

        if status == "confirmed":
            msg = "✅ *Bestätigung gespeichert!*\n\nDieser Leerstand war bereits bekannt, danke für die Bestätigung! (+2 Punkte)"
        else:
            await add_points(telegram_id, 5)
            msg = (
                f"✅ *Meldung gespeichert!*\n\n📍 *Adresse:* {adresse}\n🏠 *Lage:* {wohnungslage}\n⏰ *Dauer:* {dauer}\n\nDanke! (+5 Punkte)"
            )

        await update.message.reply_text(
            msg,
            parse_mode="Markdown",
            reply_markup=build_main_menu()
        )
        context.user_data.clear()

    else:
        await update.message.reply_text("Bitte benutze die Buttons im Menü:", reply_markup=build_main_menu())


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("meldung_step") == "foto":
        file = await update.message.photo[-1].get_file()
        local_dir = "/tmp"
        fname = f"{uuid.uuid4().hex}.jpg"
        path = os.path.join(local_dir, fname)
        await file.download_to_drive(path)
        context.user_data["img_path"] = path
        await update.message.reply_text("⏰ Wie lange steht die Wohnung schon leer?")
        context.user_data["meldung_step"] = "dauer"
    else:
        await update.message.reply_text("Bitte beginne zuerst eine neue Meldung über das Menü.")


async def handle_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tg_user = update.effective_user
    telegram_id, alias, user_id = await get_or_create_user(tg_user.id, tg_user.username or "")
    context.user_data["user_id"] = user_id

    data = query.data
    context.user_data["callback_data"] = data

    if data == "neue_meldung":
        if not alias:
            await query.edit_message_text("Du bist neu hier! Wie soll ich dich nennen?\nBitte gib deinen gewünschten Nutzernamen ein:")
            context.user_data["waiting_for_name"] = True
        else:
            await query.edit_message_text(f"Hallo {alias}!\nBitte gib die Adresse des Leerstands ein:")
            context.user_data["meldung_step"] = "adresse"

    elif data == "bestenliste":
        from bot.db.supabase_client import top_five
        ranking = top_five()
        if not ranking:
            await query.edit_message_text("🏆 *Bestenliste*\n\nNoch keine Punkte vergeben.", parse_mode="Markdown")
            return

        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        lines = [
            f"{medals[i]} {alias} – {punkte} Punkte"
            for i, (alias, punkte) in enumerate(ranking)
        ]
        text = "🏆 *Bestenliste:*\n\n" + "\n".join(lines)
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=build_back_menu())

    elif data == "meine_meldungen":
        meldungen = get_user_meldungen(user_id)
        if not meldungen:
            await query.edit_message_text("❌ Du hast noch keine Meldungen.", reply_markup=build_back_menu())
            return
        context.user_data["meldungen"] = meldungen
        context.user_data["meldung_index"] = 0
        context.user_data["image_message_id"] = None
        await show_meldung(update, context)

    elif data in ("next_meldung", "prev_meldung"):
        image_msg_id = context.user_data.pop("image_message_id", None)
        if image_msg_id:
            try:
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=image_msg_id)
            except Exception as e:
                print("Image delete failed:", e)

        if data == "next_meldung":
            context.user_data["meldung_index"] += 1
        else:
            context.user_data["meldung_index"] -= 1

        await show_meldung(update, context)

    elif data == "toggle_image":
        index = context.user_data.get("meldung_index", 0)
        meldungen = context.user_data.get("meldungen", [])
        if index < len(meldungen):
            m = meldungen[index]
            if context.user_data.get("image_message_id"):
                try:
                    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=context.user_data["image_message_id"])
                except Exception as e:
                    print("Image delete failed:", e)
                context.user_data["image_message_id"] = None
            else:
                sent = await query.message.reply_photo(photo=m["image_url"])
                context.user_data["image_message_id"] = sent.message_id

        await show_meldung(update, context)

    elif data == "skip_photo":
        context.user_data["img_path"] = None
        context.user_data["meldung_step"] = "dauer"
        await query.edit_message_text("⏰ Wie lange steht die Wohnung schon leer?")

    elif data == "back_to_menu":
        from bot.start import handle_start
        await handle_start(update, context)
        context.user_data.clear()

    elif data == "noop":
        pass


async def show_meldung(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    meldungen = context.user_data.get("meldungen", [])
    index = context.user_data.get("meldung_index", 0)

    if not meldungen:
        await query.edit_message_text("❌ Keine Meldungen gefunden.", reply_markup=build_back_menu())
        return

    index = max(0, min(index, len(meldungen) - 1))
    context.user_data["meldung_index"] = index
    m = meldungen[index]
    total = len(meldungen)

    caption = (
        f"📋 Meldung {index+1}/{total}\n\n"
        f"#{m['id']} – {m['adresse']}\n"
        f"🏠 Lage: {m['wohnungslage']}\n"
        f"⏰ Dauer: {m['dauer']}\n"
        f"✅ Bestätigt: {m['bestaetigungen']}x"
    )

    keyboard = []
    nav_buttons = []
    if index > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Zurück", callback_data="prev_meldung"))
    if index < total - 1:
        nav_buttons.append(InlineKeyboardButton("Weiter ➡️", callback_data="next_meldung"))
    if nav_buttons:
        keyboard.append(nav_buttons)

    if m.get("image_url"):
        show = context.user_data.get("image_message_id")
        toggle_label = "❌ Bild ausblenden" if show else "📸 Bild ansehen"
        keyboard.append([InlineKeyboardButton(toggle_label, callback_data="toggle_image")])

    keyboard.append([InlineKeyboardButton("🔙 Zurück zum Menü", callback_data="back_to_menu")])
    markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(caption, reply_markup=markup)
