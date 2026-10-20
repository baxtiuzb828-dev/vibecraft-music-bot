import shutil
import subprocess
from pathlib import Path


EFFECTS = {
    "slowed": ("Slowed + reverb", "atempo=0.85,aecho=0.8:0.9:1000:0.25"),
    "nightcore": ("Nightcore", "asetrate=44100*1.2,aresample=44100"),
    "bass": ("Bass boost", "bass=g=8"),
}


def find_ffmpeg() -> str:
    executable = shutil.which("ffmpeg")
    if executable:
        return executable
    try:
        import imageio_ffmpeg
    except ImportError as error:
        raise RuntimeError("Install ffmpeg or the imageio-ffmpeg Python package.") from error
    return imageio_ffmpeg.get_ffmpeg_exe()


def build_ffmpeg_command(source: Path, destination: Path, audio_filter: str) -> list[str]:
    return [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source),
        "-vn",
        "-af",
        audio_filter,
        "-codec:a",
        "libmp3lame",
        "-q:a",
        "2",
        str(destination),
    ]


def build_extract_audio_command(source: Path, destination: Path) -> list[str]:
    return [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source),
        "-map",
        "0:a:0",
        "-vn",
        "-codec:a",
        "libmp3lame",
        "-q:a",
        "2",
        str(destination),
    ]


def extract_audio(source: Path, destination: Path) -> None:
    command = build_extract_audio_command(source, destination)
    command[0] = find_ffmpeg()
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "Video ichidan audio ajratib bo'lmadi.")


def process_audio(source: Path, destination: Path, audio_filter: str) -> None:
    command = build_ffmpeg_command(source, destination, audio_filter)
    command[0] = find_ffmpeg()
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "ffmpeg could not process this audio.")


def cut_audio(source: Path, destination: Path, duration: int, start: int = 0) -> None:
    if duration not in {15, 30, 45}:
        raise ValueError("Clip duration must be 15, 30, or 45 seconds.")
    if start < 0:
        raise ValueError("Clip start cannot be negative.")
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-ss",
        str(start),
        "-i",
        str(source),
        "-t",
        str(duration),
        "-vn",
        "-codec:a",
        "libmp3lame",
        "-q:a",
        "2",
        str(destination),
    ]
    command[0] = find_ffmpeg()
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "ffmpeg could not create this clip.")