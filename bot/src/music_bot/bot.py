import asyncio
import logging
import tempfile
import uuid
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from .audio import EFFECTS, cut_audio, extract_audio, process_audio
from .catalog import CatalogTrack, download_preview, search_tracks
from .config import load_settings
from .database import CatalogStore, FavoritesStore
from .instagram import download_public_video
from .keyboards import main_menu_keyboard, video_audio_keyboard

logging.basicConfig(level=logging.INFO)
settings = load_settings()
bot = Bot(token=settings.bot_token)
dispatcher = Dispatcher()
favorites = FavoritesStore(settings.database_path)
catalog = CatalogStore(settings.database_path)
inbox = Path("data/inbox")
inbox.mkdir(parents=True, exist_ok=True)
recent_uploads: dict[int, tuple[Path, str, str]] = {}
recent_videos: dict[str, tuple[int, Path, str]] = {}


def upload_keyboard(upload_key: str, include_45_second_cut: bool = True) -> InlineKeyboardMarkup:
    clip_buttons = [
        InlineKeyboardButton(text="15 soniya", callback_data=f"cut:15:{upload_key}"),
        InlineKeyboardButton(text="30 soniya", callback_data=f"cut:30:{upload_key}"),
    ]
    if include_45_second_cut:
        clip_buttons.append(
            InlineKeyboardButton(text="45 soniya", callback_data=f"cut:45:{upload_key}")
        )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🐢 Sekin + reverb", callback_data=f"fx:slowed:{upload_key}"),
                InlineKeyboardButton(text="⚡ Tezlashtirish", callback_data=f"fx:nightcore:{upload_key}"),
            ],
            [
                InlineKeyboardButton(text="🔊 Bassni kuchaytirish", callback_data=f"fx:bass:{upload_key}"),
                InlineKeyboardButton(text="⭐ Sevimlilarga", callback_data=f"fav:{upload_key}"),
            ],
            clip_buttons,
        ]
    )


async def check_sponsors(user_id: int) -> bool:
    for channel in settings.sponsor_channels:
        try:
            member = await bot.get_chat_member(channel, user_id)
        except Exception:
            logging.exception("Could not check sponsor channel %s", channel)
            return False
        if member.status not in {"member", "administrator", "creator"}:
            return False
    return True


@dispatcher.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer(
        "🎵 VibeCraft Music botiga xush kelibsiz!\n\n"
        "🎧 Istalgan qoʻshiqni yuborsangiz, bot uning tezligini va kayfiyatini oʻzgartirib beradi "
        "(masalan: Slowed + Reverb — sekinlashtirilgan, Nightcore — tezlashtirilgan yoki "
        "Bass Boost — basini kuchaytirilgan versiyasi).\n\n"
        "📲 Boshlash uchun istalgan qoʻshiq nomini yuboring yoki audio fayl tashlang!",
        reply_markup=main_menu_keyboard(),
    )


@dispatcher.message(F.text == "🔍 QIDIRUV")
async def search_prompt(message: Message) -> None:
    await message.answer("Qidirish uchun qoʻshiq nomi yoki ijrochi ismini yuboring.")


@dispatcher.message(F.text == "🔥 TREND XITLAR")
async def show_trends(message: Message) -> None:
    await message.answer(
        "Trend xitlar jadvali hozircha ulanmagan. Qoʻshiq nomini yuborib katalogdan qidiring."
    )


@dispatcher.message(F.text == "🎛 AUDIO EFFEKTLAR")
async def show_effects_prompt(message: Message) -> None:
    await message.answer(
        "Audio fayl yoki voice yuboring. Shunda sekinlashtirish, tezlashtirish, bass va kesish tugmalari chiqadi."
    )


@dispatcher.message(F.text == "📞 ALOQA")
async def show_contact(message: Message) -> None:
    if settings.admin_contact:
        await message.answer(f"Aloqa uchun: @{settings.admin_contact}")
    else:
        await message.answer("Admin kontaktini sozlash uchun .env faylida ADMIN_CONTACT ni kiriting.")


async def send_help(message: Message) -> None:
    await message.answer(
        "Audio yuboring va tugmalardan effekt yoki 15/30/45 soniyali kesimni tanlang.\n"
        "/favorites - saqlangan qo'shiqlar\n"
        "Kesim hozircha audio boshidan olinadi."
    )


@dispatcher.message(Command("help"))
async def help_command(message: Message) -> None:
    await send_help(message)


@dispatcher.message(F.text == "💡 YORDAM")
async def help_menu_button(message: Message) -> None:
    await send_help(message)


async def send_favorites(message: Message) -> None:
    tracks = favorites.list_for_user(message.from_user.id)
    if not tracks:
        await message.answer("Sevimlilar ro'yxati hozircha bo'sh.")
        return
    await message.answer("Sevimlilaringiz:")
    for file_id, title in tracks:
        await message.answer_audio(file_id, caption=title)


@dispatcher.message(Command("favorites"))
async def show_favorites(message: Message) -> None:
    await send_favorites(message)


@dispatcher.message(F.text == "⭐ SEVIMLILAR")
async def favorites_menu_button(message: Message) -> None:
    await send_favorites(message)


async def search_catalog(query: str, country: str) -> list[CatalogTrack]:
    try:
        return await asyncio.to_thread(search_tracks, query, country)
    except Exception:
        logging.exception("Music catalog search failed for country %s", country)
        return []


@dispatcher.message(
    F.text
    & (F.text.contains("instagram.com") | F.text.contains("instagr.am"))
)
async def receive_instagram_link(message: Message) -> None:
    url = (message.text or "").strip()
    status = await message.answer("Instagram videosi tekshirilmoqda...")
    try:
        source_path, title = await asyncio.to_thread(download_public_video, url, inbox)
        upload_key = uuid.uuid4().hex[:12]
        recent_videos[upload_key] = (message.from_user.id, source_path, title)
        await message.answer_video(
            FSInputFile(source_path),
            caption=title[:900],
            supports_streaming=True,
            reply_markup=video_audio_keyboard(upload_key),
        )
        await status.delete()
    except Exception as error:
        logging.info("Instagram video download unavailable: %s", error)
        await status.edit_text(
            "Video yuborilmadi. Ochiq post/reel havolasini tekshiring yoki hajmi kichikroq "
            "video yuboring. Private yoki login talab qiladigan kontent qo'llanmaydi."
        )


@dispatcher.message(F.text & ~F.text.startswith("/"))
async def search_song(message: Message) -> None:
    query = (message.text or "").strip()
    if len(query) < 2:
        await message.answer("Qidirish uchun qoʻshiq nomini yuboring.")
        return

    unique_tracks = catalog.get_recent_search(query)
    search_status: Message | None = None
    if unique_tracks is None:
        unique_tracks = catalog.search_cached(query)
        if not unique_tracks:
            search_status = await message.answer("🔍 Katalogdan qidirilmoqda...")
            regional_results, international_results = await asyncio.gather(
                search_catalog(query, "UZ"),
                search_catalog(query, "US"),
            )
            unique_tracks = []
            seen: set[tuple[str, str]] = set()
            for track in regional_results + international_results:
                key = (track.title.casefold(), track.artist.casefold())
                if key not in seen:
                    seen.add(key)
                    unique_tracks.append(track)

            if unique_tracks:
                catalog.cache_tracks(unique_tracks)
                catalog.cache_search(query, unique_tracks)

    if not unique_tracks:
        text = "Bu nom bo‘yicha natija topilmadi. Boshqa yozilishda qidirib ko‘ring."
        if search_status:
            await search_status.edit_text(text)
        else:
            await message.answer(text)
        return

    tracks = unique_tracks[:8]
    lines = ["🔎 Katalog natijalari:"]
    buttons = []
    for index, track in enumerate(tracks, start=1):
        lines.append(f"{index}. {track.title} — {track.artist} ({track.country})")
        if track.preview_url:
            title = track.title[:22]
            artist = track.artist[:18]
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"🎧 {index}. {title} — {artist}",
                        callback_data=f"track:{track.country}:{track.track_id}",
                    )
                ]
            )
    result_keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    if search_status:
        await search_status.edit_text("\n".join(lines), reply_markup=result_keyboard)
    else:
        await message.answer("\n".join(lines), reply_markup=result_keyboard)


@dispatcher.callback_query(F.data.startswith("track:"))
async def send_catalog_preview(callback: CallbackQuery) -> None:
    _, country, track_id_text = callback.data.split(":", 2)
    if country not in {"UZ", "US"} or not track_id_text.isdigit():
        await callback.answer("Trek ma'lumoti noto'g'ri.", show_alert=True)
        return

    track = catalog.get_track(int(track_id_text), country)
    if track is None or not track.preview_url:
        await callback.answer("Bu qo'shiq uchun preview mavjud emas.", show_alert=True)
        return

    await callback.answer("30 soniyalik preview yuborilmoqda...")
    try:
        preview = await asyncio.to_thread(download_preview, track.preview_url)
        if callback.message:
            upload_key = uuid.uuid4().hex[:12]
            source_path = inbox / f"{upload_key}.m4a"
            source_path.write_bytes(preview)
            sent_message = await callback.message.answer_audio(
                FSInputFile(source_path),
                title=track.title,
                performer=track.artist,
                caption="🎧 30 soniyalik preview. O'zgartirish uchun tugmani tanlang.",
                reply_markup=upload_keyboard(upload_key, include_45_second_cut=False),
            )
            if sent_message.audio:
                recent_uploads[callback.from_user.id] = (
                    source_path,
                    sent_message.audio.file_id,
                    track.title,
                )
    except Exception:
        logging.exception("Could not send catalog preview for track %s", track.track_id)
        if callback.message:
            await callback.message.answer("Previewni hozir yuborib bo'lmadi. Keyinroq urinib ko'ring.")


@dispatcher.message(F.video | (F.document & F.document.mime_type.startswith("video/")))
async def receive_video(message: Message) -> None:
    media = message.video or message.document
    if media is None:
        await message.answer("Video faylni yuboring.")
        return
    if settings.sponsor_channels and not await check_sponsors(message.from_user.id):
        await message.answer("Botdan foydalanish uchun homiy kanalga obuna bo'ling.")
        return

    title = getattr(media, "file_name", None) or "Instagram video"
    upload_key = uuid.uuid4().hex[:12]
    extension = Path(title).suffix or ".mp4"
    source_path = inbox / f"{upload_key}{extension}"
    try:
        await bot.download(media, destination=source_path)
    except Exception:
        logging.exception("Could not download uploaded video")
        await message.answer("Videoni qabul qilib bo'lmadi. Qisqaroq fayl yuborib ko'ring.")
        return

    recent_videos[upload_key] = (message.from_user.id, source_path, Path(title).stem)
    await message.reply(
        "🎵 Qo'shiqni yuklab olish:",
        reply_markup=video_audio_keyboard(upload_key),
    )


def get_video_upload(user_id: int, upload_key: str) -> tuple[Path, str] | None:
    upload = recent_videos.get(upload_key)
    if upload is None or upload[0] != user_id or not upload[1].exists():
        return None
    return upload[1], upload[2]


@dispatcher.callback_query(F.data.startswith("video:"))
async def send_video_file(callback: CallbackQuery) -> None:
    upload_key = callback.data.split(":", 1)[1]
    upload = get_video_upload(callback.from_user.id, upload_key)
    if upload is None:
        await callback.answer("Video topilmadi. Qayta yuboring.", show_alert=True)
        return
    source_path, title = upload
    await callback.answer("Video yuborilmoqda...")
    if callback.message:
        await callback.message.answer_document(FSInputFile(source_path), caption=title[:900])


@dispatcher.callback_query(F.data.startswith("videoaudio:"))
async def send_video_audio(callback: CallbackQuery) -> None:
    upload_key = callback.data.split(":", 1)[1]
    upload = get_video_upload(callback.from_user.id, upload_key)
    if upload is None:
        await callback.answer("Video topilmadi. Qayta yuboring.", show_alert=True)
        return
    source_path, title = upload
    await callback.answer("Qo'shiq ajratilmoqda...")
    audio_path = Path(tempfile.gettempdir()) / f"musicbot-audio-{uuid.uuid4().hex}.mp3"
    try:
        await asyncio.to_thread(extract_audio, source_path, audio_path)
        if callback.message:
            await callback.message.answer_audio(
                FSInputFile(audio_path),
                title=title,
                caption="🎵 Videodan ajratilgan audio",
            )
    except RuntimeError as error:
        if callback.message:
            await callback.message.answer(str(error))
    finally:
        audio_path.unlink(missing_ok=True)


@dispatcher.message(F.audio | F.voice | (F.document & F.document.mime_type.startswith("audio/")))
async def receive_audio(message: Message) -> None:
    media = message.audio or message.voice or message.document
    if media is None:
        await message.answer("Iltimos, audio fayl yuboring.")
        return
    if settings.sponsor_channels and not await check_sponsors(message.from_user.id):
        await message.answer("Botdan foydalanish uchun homiy kanalga obuna bo'ling.")
        return

    title = getattr(media, "title", None) or getattr(media, "file_name", None) or "Telegram audio"
    upload_key = uuid.uuid4().hex[:12]
    extension = Path(getattr(media, "file_name", "") or "audio.ogg").suffix or ".ogg"
    source_path = inbox / f"{upload_key}{extension}"
    await bot.download(media, destination=source_path)
    recent_uploads[message.from_user.id] = (source_path, media.file_id, title)
    await message.answer(
        f"{title}: amalni tanlang. Ringtone kesimi fayl boshidan olinadi.",
        reply_markup=upload_keyboard(upload_key),
    )


async def get_upload(user_id: int, upload_key: str) -> tuple[Path, str, str] | None:
    upload = recent_uploads.get(user_id)
    if upload is None or upload[0].stem != upload_key or not upload[0].exists():
        return None
    return upload


@dispatcher.callback_query(F.data.startswith("fav:"))
async def save_favorite(callback: CallbackQuery) -> None:
    upload_key = callback.data.split(":", 1)[1]
    upload = await get_upload(callback.from_user.id, upload_key)
    if upload is None:
        await callback.answer("Audio topilmadi. Qayta yuboring.", show_alert=True)
        return
    _, file_id, title = upload
    added = favorites.add(callback.from_user.id, file_id, title)
    await callback.answer("Sevimlilarga saqlandi." if added else "Bu audio allaqachon saqlangan.")


async def send_processed(callback: CallbackQuery, action: str, upload_key: str) -> None:
    upload = await get_upload(callback.from_user.id, upload_key)
    if upload is None:
        await callback.answer("Audio topilmadi. Qayta yuboring.", show_alert=True)
        return
    source_path, _, title = upload
    await callback.answer("Audio tayyorlanmoqda...")
    output_path = Path(tempfile.gettempdir()) / f"musicbot-{uuid.uuid4().hex}.mp3"
    try:
        if action in EFFECTS:
            label, audio_filter = EFFECTS[action]
            await asyncio.to_thread(process_audio, source_path, output_path, audio_filter)
        else:
            duration = int(action)
            label = f"Ringtone {duration} sec"
            await asyncio.to_thread(cut_audio, source_path, output_path, duration)
        await callback.message.answer_audio(FSInputFile(output_path), title=f"{title} - {label}")
    except (RuntimeError, ValueError) as error:
        await callback.message.answer(str(error))
    finally:
        output_path.unlink(missing_ok=True)


@dispatcher.callback_query(F.data.startswith("fx:"))
async def apply_effect(callback: CallbackQuery) -> None:
    _, effect, upload_key = callback.data.split(":", 2)
    if effect not in EFFECTS:
        await callback.answer("Noma'lum effekt", show_alert=True)
        return
    await send_processed(callback, effect, upload_key)


@dispatcher.callback_query(F.data.startswith("cut:"))
async def make_ringtone(callback: CallbackQuery) -> None:
    _, duration, upload_key = callback.data.split(":", 2)
    await send_processed(callback, duration, upload_key)


async def run_bot() -> None:
    await dispatcher.start_polling(bot)


def main() -> None:
    asyncio.run(run_bot())
