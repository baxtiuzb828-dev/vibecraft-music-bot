from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 QIDIRUV"), KeyboardButton(text="🔥 TREND XITLAR")],
            [KeyboardButton(text="⭐ SEVIMLILAR"), KeyboardButton(text="🎛 AUDIO EFFEKTLAR")],
            [KeyboardButton(text="💡 YORDAM"), KeyboardButton(text="📞 ALOQA")],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Qoʻshiq nomini yozing...",
    )


def video_audio_keyboard(upload_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎵 Qo'shiqni yuklab olish",
                    callback_data=f"videoaudio:{upload_key}",
                )
            ],
        ]
    )