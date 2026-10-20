import unittest
from pathlib import Path

from music_bot.audio import EFFECTS, build_extract_audio_command, build_ffmpeg_command, cut_audio


class AudioTests(unittest.TestCase):
    def test_effects_have_expected_filters(self) -> None:
        self.assertEqual(set(EFFECTS), {"slowed", "nightcore", "bass"})
        self.assertIn("aecho", EFFECTS["slowed"][1])

    def test_ffmpeg_command_includes_filter_and_output(self) -> None:
        command = build_ffmpeg_command(Path("input.ogg"), Path("output.mp3"), "bass=g=8")
        self.assertEqual(command[command.index("-af") + 1], "bass=g=8")
        self.assertEqual(command[-1], "output.mp3")

    def test_extract_audio_command_uses_video_audio_stream(self) -> None:
        command = build_extract_audio_command(Path("video.mp4"), Path("song.mp3"))
        self.assertEqual(command[command.index("-map") + 1], "0:a:0")
        self.assertIn("-vn", command)
        self.assertEqual(command[-1], "song.mp3")

    def test_cut_rejects_unsupported_duration_before_ffmpeg(self) -> None:
        with self.assertRaises(ValueError):
            cut_audio(Path("missing.mp3"), Path("clip.mp3"), 20)


if __name__ == "__main__":
    unittest.main()