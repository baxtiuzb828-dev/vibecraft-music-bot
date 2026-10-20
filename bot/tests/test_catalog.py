import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from music_bot.catalog import download_preview, parse_catalog_response, search_tracks
from music_bot.instagram import MAX_VIDEO_BYTES, download_public_video, validate_instagram_url


class CatalogTests(unittest.TestCase):
    def test_parse_catalog_response_keeps_supported_track_metadata(self) -> None:
        tracks = parse_catalog_response(
            {
                "results": [
                    {
                        "trackId": 42,
                        "trackName": "Example song",
                        "artistName": "Example artist",
                        "trackViewUrl": "https://music.example/track/42",
                        "previewUrl": "https://music.example/preview/42",
                    },
                    {"trackName": "Incomplete result"},
                ]
            },
            "UZ",
        )

        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0].title, "Example song")
        self.assertEqual(tracks[0].country, "UZ")
        self.assertEqual(tracks[0].preview_url, "https://music.example/preview/42")

    def test_search_rejects_unsupported_country_without_network_access(self) -> None:
        with self.assertRaises(ValueError):
            search_tracks("example", "XX")

    def test_preview_rejects_external_hosts_without_network_access(self) -> None:
        with self.assertRaises(ValueError):
            download_preview("https://example.com/preview.m4a")

    def test_instagram_url_accepts_reel_and_rejects_other_hosts(self) -> None:
        reel_url = "https://www.instagram.com/reel/ABC123/"
        self.assertEqual(validate_instagram_url(reel_url), reel_url)
        with self.assertRaises(ValueError):
            validate_instagram_url("https://example.com/reel/ABC123/")

    def test_instagram_downloader_rejects_file_over_size_limit(self) -> None:
        with TemporaryDirectory() as directory:
            video_path = Path(directory) / "instagram-123.mp4"
            with video_path.open("wb") as video_file:
                video_file.truncate(MAX_VIDEO_BYTES + 1)

            downloader = MagicMock()
            downloader.__enter__.return_value.extract_info.return_value = {
                "id": "123",
                "title": "Test reel",
            }
            downloader.__enter__.return_value.prepare_filename.return_value = str(video_path)

            with patch("music_bot.instagram.yt_dlp.YoutubeDL", return_value=downloader):
                with self.assertRaises(ValueError):
                    download_public_video("https://www.instagram.com/reel/ABC123/", Path(directory))

            self.assertFalse(video_path.exists())


if __name__ == "__main__":
    unittest.main()