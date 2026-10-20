import unittest

from music_bot.keyboards import main_menu_keyboard, video_audio_keyboard


class MainMenuKeyboardTests(unittest.TestCase):
    def test_menu_has_the_requested_three_rows(self) -> None:
        keyboard = main_menu_keyboard()
        labels = [[button.text for button in row] for row in keyboard.keyboard]

        self.assertEqual(
            labels,
            [
                ["🔍 QIDIRUV", "🔥 TREND XITLAR"],
                ["⭐ SEVIMLILAR", "🎛 AUDIO EFFEKTLAR"],
                ["💡 YORDAM", "📞 ALOQA"],
            ],
        )

    def test_video_keyboard_only_offers_song_download(self) -> None:
        keyboard = video_audio_keyboard("abc123")
        labels = [row[0].text for row in keyboard.inline_keyboard]

        self.assertEqual(labels, ["🎵 Qo'shiqni yuklab olish"])


if __name__ == "__main__":
    unittest.main()