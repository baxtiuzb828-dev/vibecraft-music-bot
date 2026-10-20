import json
import sqlite3
from contextlib import closing
from pathlib import Path
from time import time

from .catalog import CatalogTrack


class FavoritesStore:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection, connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS favorites (
                    user_id INTEGER NOT NULL,
                    file_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    PRIMARY KEY (user_id, file_id)
                )"""
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)

    def add(self, user_id: int, file_id: str, title: str) -> bool:
        with closing(self._connect()) as connection, connection:
            cursor = connection.execute(
                "INSERT OR IGNORE INTO favorites (user_id, file_id, title) VALUES (?, ?, ?)",
                (user_id, file_id, title),
            )
            return cursor.rowcount > 0

    def list_for_user(self, user_id: int) -> list[tuple[str, str]]:
        with closing(self._connect()) as connection, connection:
            rows = connection.execute(
                "SELECT file_id, title FROM favorites WHERE user_id = ? ORDER BY rowid DESC",
                (user_id,),
            ).fetchall()
        return [(str(file_id), str(title)) for file_id, title in rows]


class CatalogStore:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.database_path)) as connection, connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS catalog_tracks (
                    track_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    artist TEXT NOT NULL,
                    country TEXT NOT NULL,
                    track_url TEXT NOT NULL,
                    preview_url TEXT,
                    PRIMARY KEY (track_id, country)
                )"""
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS catalog_searches (
                    query_key TEXT PRIMARY KEY,
                    track_ids TEXT NOT NULL,
                    updated_at REAL NOT NULL
                )"""
            )

    def cache_tracks(self, tracks: list[CatalogTrack]) -> None:
        with closing(sqlite3.connect(self.database_path)) as connection, connection:
            connection.executemany(
                """INSERT OR REPLACE INTO catalog_tracks
                    (track_id, title, artist, country, track_url, preview_url)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                [
                    (
                        track.track_id,
                        track.title,
                        track.artist,
                        track.country,
                        track.track_url,
                        track.preview_url,
                    )
                    for track in tracks
                ],
            )

    def search_cached(self, query: str, limit: int = 8) -> list[CatalogTrack]:
        pattern = f"%{query}%"
        with closing(sqlite3.connect(self.database_path)) as connection, connection:
            rows = connection.execute(
                """SELECT track_id, title, artist, country, track_url, preview_url
                    FROM catalog_tracks
                    WHERE title LIKE ? OR artist LIKE ?
                    ORDER BY title LIMIT ?""",
                (pattern, pattern, limit),
            ).fetchall()
        return [CatalogTrack(*row) for row in rows]

    def cache_search(self, query: str, tracks: list[CatalogTrack]) -> None:
        query_key = query.casefold().strip()
        track_ids = json.dumps(
            [(track.track_id, track.country) for track in tracks],
            separators=(",", ":"),
        )
        with closing(sqlite3.connect(self.database_path)) as connection, connection:
            connection.execute(
                """INSERT OR REPLACE INTO catalog_searches
                    (query_key, track_ids, updated_at) VALUES (?, ?, ?)""",
                (query_key, track_ids, time()),
            )

    def get_recent_search(
        self,
        query: str,
        max_age_seconds: int = 24 * 60 * 60,
    ) -> list[CatalogTrack] | None:
        query_key = query.casefold().strip()
        with closing(sqlite3.connect(self.database_path)) as connection, connection:
            cached = connection.execute(
                "SELECT track_ids, updated_at FROM catalog_searches WHERE query_key = ?",
                (query_key,),
            ).fetchone()
            if cached is None or time() - float(cached[1]) > max_age_seconds:
                return None

            tracks = []
            for track_id, country in json.loads(cached[0]):
                row = connection.execute(
                    """SELECT track_id, title, artist, country, track_url, preview_url
                        FROM catalog_tracks WHERE track_id = ? AND country = ?""",
                    (track_id, country),
                ).fetchone()
                if row:
                    tracks.append(CatalogTrack(*row))
        return tracks

    def get_track(self, track_id: int, country: str) -> CatalogTrack | None:
        with closing(sqlite3.connect(self.database_path)) as connection, connection:
            row = connection.execute(
                """SELECT track_id, title, artist, country, track_url, preview_url
                    FROM catalog_tracks WHERE track_id = ? AND country = ?""",
                (track_id, country),
            ).fetchone()
        return CatalogTrack(*row) if row else None