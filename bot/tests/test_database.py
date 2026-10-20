import tempfile
import unittest
from pathlib import Path

from music_bot.catalog import CatalogTrack
from music_bot.database import CatalogStore, FavoritesStore


class FavoritesStoreTests(unittest.TestCase):
    def test_favorites_are_user_scoped_and_duplicates_are_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = FavoritesStore(Path(directory) / "favorites.sqlite3")

            self.assertTrue(store.add(10, "file-a", "Track A"))
            self.assertFalse(store.add(10, "file-a", "Track A"))
            self.assertTrue(store.add(11, "file-b", "Track B"))

            self.assertEqual(store.list_for_user(10), [("file-a", "Track A")])
            self.assertEqual(store.list_for_user(11), [("file-b", "Track B")])


class CatalogStoreTests(unittest.TestCase):
    def test_recent_search_returns_cached_tracks_case_insensitively(self) -> None:
        track = CatalogTrack(
            track_id=24,
            title="Example track",
            artist="Example artist",
            country="UZ",
            track_url="https://music.example/track/24",
            preview_url="https://audio-ssl.itunes.apple.com/preview.m4a",
        )
        with tempfile.TemporaryDirectory() as directory:
            store = CatalogStore(Path(directory) / "catalog.sqlite3")
            store.cache_tracks([track])
            store.cache_search("Example Track", [track])

            self.assertEqual(store.get_recent_search("  example track "), [track])
            self.assertIsNone(store.get_recent_search("different query"))


if __name__ == "__main__":
    unittest.main()