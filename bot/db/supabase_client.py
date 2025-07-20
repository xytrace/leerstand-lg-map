import os
import uuid
import json
import requests
import re
from datetime import datetime
from supabase import create_client, Client
import asyncio
import logging
logger = logging.getLogger(__name__)


with open("config.json") as f:
    config = json.load(f)

SUPABASE_URL = config["supabase_url"]
SUPABASE_KEY = config["supabase_key"]
SUPABASE_BUCKET = config["supabase_bucket"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def normalize_street(address: str) -> str:
    """Normalizes 'Strasse', 'Straße', 'Str.' to 'Str.' and applies title case."""
    address = address.strip()
    address = re.sub(r'\bstrasse\b', 'Str.', address, flags=re.IGNORECASE)
    address = re.sub(r'\bstraße\b', 'Str.', address, flags=re.IGNORECASE)
    address = re.sub(r'\bstr\.\b', 'Str.', address, flags=re.IGNORECASE)
    address = re.sub(r'\s+', ' ', address)
    return address.title()


def extract_number(address: str) -> str:
    """Extracts the first house number in the address."""
    match = re.search(r'\d+\w*', address)
    return match.group(0).lower() if match else ""


async def get_or_create_user(tg_id: int, username: str):
    res = supabase.table("users").select("*").eq("telegram_id", tg_id).execute()
    data = res.data

    if data:
        user = data[0]
        return user["telegram_id"], user.get("alias", "") or "", user["id"]

    insert_res = supabase.table("users").insert({
        "telegram_id": tg_id,
        "alias": None,
        "punkte": 0
    }).execute()

    new_user = insert_res.data[0]
    return new_user["telegram_id"], "", new_user["id"]


async def add_points(tg_id: int, points: int):
    """Adds points using RPC function in Supabase"""
    await asyncio.to_thread(
        lambda: supabase.rpc("add_points_to_user", {"tgid": tg_id, "pts": points}).execute()
    )


async def upload_image(local_path: str, telegram_id: int) -> str:
    ext = os.path.splitext(local_path)[1]
    name = f"{telegram_id}_{uuid.uuid4().hex}{ext}"
    remote_path = f"{telegram_id}/{name}"

    with open(local_path, "rb") as f:
        supabase.storage.from_(SUPABASE_BUCKET).upload(remote_path, f, {"content-type": "image/jpeg"})

    return f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{remote_path}"


async def save_meldung(user_id, local_img_path, adresse, wohnungslage, dauer, lat, lon):
    adresse = adresse.strip()
    normalized_input = normalize_street(adresse)
    input_number = extract_number(adresse)

    all = supabase.table("meldungen").select("id, adresse, bestaetigungen").execute()

    for m in all.data:
        norm_existing = normalize_street(m["adresse"])
        num_existing = extract_number(m["adresse"])

        if norm_existing == normalized_input and num_existing == input_number:
            # Update bestaetigungen manually
            current = m.get("bestaetigungen", 0)
            supabase.table("meldungen").update({
                "bestaetigungen": current + 1
            }).eq("id", m["id"]).execute()

            tg = supabase.table("users").select("telegram_id").eq("id", user_id).limit(1).execute()
            if tg.data:
                await add_points(tg.data[0]["telegram_id"], 2)

            return "confirmed"

    tg = supabase.table("users").select("telegram_id").eq("id", user_id).limit(1).execute()
    if tg.data:
        await add_points(tg.data[0]["telegram_id"], 5)

    image_url = None
    if local_img_path:
        image_url = await upload_image(local_img_path, user_id)

    data = {
        "user_id": user_id,
        "adresse": adresse,
        "wohnungslage": wohnungslage,
        "dauer": dauer,
        "lat": lat,
        "lon": lon,
        "image_url": image_url,
        "created_at": datetime.utcnow().isoformat(),
        "bestaetigungen": 0
    }

    supabase.table("meldungen").insert(data).execute()
    return "new"


def top_five():
    res = supabase.table("users") \
        .select("alias", "punkte") \
        .neq("alias", None) \
        .order("punkte", desc=True) \
        .limit(5).execute()
    return [(r["alias"], r["punkte"]) for r in res.data]


def get_user_meldungen(user_id=None):
    query = supabase.table("meldungen").select("*").order("id", desc=True)
    if user_id is not None:
        query = query.eq("user_id", user_id)
    return query.execute().data


def confirm_meldung(mid: int) -> bool:
    res = supabase.table("meldungen").select("user_id", "bestaetigungen").eq("id", mid).limit(1).execute()
    if not res.data:
        return False

    uid = res.data[0]["user_id"]
    current = res.data[0].get("bestaetigungen", 0)

    user_res = supabase.table("users").select("telegram_id").eq("id", uid).limit(1).execute()
    if not user_res.data:
        return False

    tg_id = user_res.data[0]["telegram_id"]
    asyncio.run(add_points(tg_id, 3))

    supabase.table("meldungen").update({"bestaetigungen": current + 1}).eq("id", mid).execute()
    return True


def delete_meldung(mid: str) -> bool:
    logger.info(f"[DELETE] Starting deletion for Meldung ID {mid}")

    try:
        res = supabase.table("meldungen").select("image_url").eq("id", mid).limit(1).execute()
        if not res.data:
            logger.warning(f"[DELETE] No meldung found with ID {mid}")
            return False

        url = res.data[0]["image_url"]
        if url:
            path = url.split("/object/public/")[-1].split("?")[0]
            # Strip the bucket prefix
            path = path.replace(f"{SUPABASE_BUCKET}/", "")

            logger.info(f"[DELETE] Attempting to remove image from storage: {path}")
            try:
                result = supabase.storage.from_(SUPABASE_BUCKET).remove([path])
                logger.info(f"[DELETE] Image removed from storage: {path}, result: {result}")
            except Exception as e:
                logger.error(f"[DELETE] Image deletion failed: {e}")

        # Delete the row itself
        delete_result = supabase.table("meldungen").delete().eq("id", mid).execute()
        logger.info(f"[DELETE] Meldung {mid} deleted from database")

        return True

    except Exception as e:
        logger.error(f"[DELETE] Unexpected error during deletion of Meldung {mid}: {e}")
        return False

