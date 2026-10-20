import json
from dataclasses import dataclass
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class CatalogTrack:
    track_id: int
    title: str
    artist: str
    country: str
    track_url: str
    preview_url: str | None


def parse_catalog_response(payload: dict, country: str) -> list[CatalogTrack]:
    tracks = []
    for item in payload.get("results", []):
        if not isinstance(item, dict):
            continue
        track_id = item.get("trackId")
        title = item.get("trackName")
        artist = item.get("artistName")
        track_url = item.get("trackViewUrl")
        if not isinstance(track_id, int) or not all(
            isinstance(value, str) and value for value in (title, artist, track_url)
        ):
            continue
        preview_url = item.get("previewUrl")
        tracks.append(
            CatalogTrack(
                track_id=track_id,
                title=title,
                artist=artist,
                country=country,
                track_url=track_url,
                preview_url=preview_url if isinstance(preview_url, str) else None,
            )
        )
    return tracks


def search_tracks(query: str, country: str, limit: int = 5) -> list[CatalogTrack]:
    if country not in {"UZ", "US"}:
        raise ValueError("Catalog country must be UZ or US.")
    params = urlencode({"term": query, "country": country, "entity": "song", "limit": limit})
    request = Request(
        f"https://itunes.apple.com/search?{params}",
        headers={"User-Agent": "VibeCraftMusic/0.1"},
    )
    with urlopen(request, timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        return []
    return parse_catalog_response(payload, country)


def download_preview(preview_url: str, max_bytes: int = 15 * 1024 * 1024) -> bytes:
    parsed_url = urlparse(preview_url)
    hostname = parsed_url.hostname or ""
    if (
        parsed_url.scheme != "https"
        or not (hostname == "apple.com" or hostname.endswith(".apple.com"))
    ):
        raise ValueError("Preview manzili ishonchli katalogdan emas.")

    request = Request(preview_url, headers={"User-Agent": "VibeCraftMusic/0.1"})
    with urlopen(request, timeout=15) as response:
        content = response.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise ValueError("Preview fayli ruxsat etilgan hajmdan katta.")
    if not content:
        raise ValueError("Preview fayli bo'sh.")
    return content