from pathlib import Path
from urllib.parse import urlparse

import yt_dlp


ALLOWED_HOSTS = {"instagram.com", "www.instagram.com", "m.instagram.com", "instagr.am"}
ALLOWED_PATHS = {"p", "reel", "reels", "tv"}
MAX_VIDEO_BYTES = 25 * 1024 * 1024


def validate_instagram_url(url: str) -> str:
    parsed = urlparse(url.strip())
    host = (parsed.hostname or "").lower()
    path_parts = [part for part in parsed.path.split("/") if part]
    if (
        parsed.scheme != "https"
        or host not in ALLOWED_HOSTS
        or len(path_parts) < 2
        or path_parts[0] not in ALLOWED_PATHS
    ):
        raise ValueError("Ochiq Instagram post, reel yoki video havolasini yuboring.")
    return url.strip()


def download_public_video(url: str, output_dir: Path) -> tuple[Path, str]:
    validated_url = validate_instagram_url(url)
    output_dir.mkdir(parents=True, exist_ok=True)
    options = {
        "format": "best[height<=480][ext=mp4]/best[height<=480]",
        "outtmpl": str(output_dir / "instagram-%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 15,
        "retries": 1,
        "extractor_retries": 1,
        "concurrent_fragment_downloads": 8,
        "max_filesize": MAX_VIDEO_BYTES,
    }
    with yt_dlp.YoutubeDL(options) as downloader:
        info = downloader.extract_info(validated_url, download=True)
        video_path = Path(downloader.prepare_filename(info))
    if not video_path.is_file():
        raise RuntimeError("Yuklangan video fayli topilmadi.")
    if video_path.stat().st_size > MAX_VIDEO_BYTES:
        video_path.unlink()
        raise ValueError("Video 25 MB limitdan katta.")
    return video_path, str(info.get("title") or "Instagram video")