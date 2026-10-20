# Telegram Music Bot

A Python Telegram bot MVP for audio effects, ringtone clips, and personal favorites.

## Included

- Slowed + reverb, Nightcore, and bass-boost processing for uploaded audio.
- 15, 30, or 45 second clips cut from the beginning of an uploaded track.
- A personal favorites list stored in SQLite.
- Optional sponsor-channel membership checks when `SPONSOR_CHANNELS` is configured.
- Uzbek and international song metadata search, cached in SQLite as users search.
- A persistent three-row Telegram menu for search, favorites, audio effects, help, and contact.
- Instagram videos up to 480p and 25 MB are sent automatically with a separate MP3 extraction button for faster delivery.
- Public Instagram post/reel links are handled with `yt-dlp` and receive the same video/audio buttons.

## Requirements

- Python 3.11 or newer.
- `imageio-ffmpeg` provides a bundled FFmpeg binary for audio processing.

Install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e .
Copy-Item .env.example .env
```

Set `BOT_TOKEN` in `.env` to a newly generated token from BotFather, then run:

```powershell
python -m music_bot
```

Set `ADMIN_CONTACT` in `.env` to the admin's Telegram username (without `@`) to enable the contact menu item. The trend chart button currently reports that charts are not connected.

## Render deployment

This bot uses Telegram long polling, so deploy it as a Render **Background Worker**, not a web service. The root-level `render.yaml` configures the Docker worker and a 1 GB persistent disk mounted at `/app/data`; this keeps the SQLite database across restarts and deploys. Render background workers and persistent disks require a paid plan.

1. Push the project to a GitHub repository. Make sure `.env` and local `data/` files are not committed.
2. In the Render Dashboard, create a **Blueprint** from that repository and select `render.yaml`.
3. Enter `BOT_TOKEN` when prompted. Add optional `SPONSOR_CHANNELS` and `ADMIN_CONTACT` variables in the worker's Environment settings if needed.
4. Deploy, then check the worker's logs for startup errors.

Keep the Telegram token in Render's environment settings; do not add it to `render.yaml` or commit it. The first deployment creates a new SQLite database on the Render disk; existing local favorites and catalog data are not copied automatically.

## Always-on free VM deployment

For continuous Telegram polling, use an Always Free VM such as Oracle Cloud's free-tier compute. Free web hosts may sleep the bot or discard its local SQLite files. VM availability depends on region and capacity; the provider may require payment-card verification.

1. Create an Ubuntu VM in your cloud account and install Docker Engine with the Compose plugin.
2. Copy this project to the VM and create `.env` from `.env.example`. Set `BOT_TOKEN` on the VM; never commit `.env`.
3. From the project directory run:

```sh
docker compose up -d --build
docker compose logs -f music-bot
```

The Compose service restarts after VM or container restarts, and a Docker named volume persists the SQLite database and downloaded media. Back up the `bot-data` Docker volume if favorites and cached catalog data must survive VM loss. Stop the bot with `docker compose down` (the volume is retained).

## Bot usage

Send a song title to search the Uzbek and US Apple Music catalogs. Where available, tap the Uzbek preview button to receive the official 30-second audio preview directly in Telegram. Send an audio file or Telegram audio/voice message for effect, ringtone, and favorite actions. Send a video file or a public Instagram post/reel link; Instagram videos are returned immediately with a separate audio-extraction button. Private or login-required Instagram content is not supported; only download content you have permission to use. Use `/favorites` to list saved tracks and `/help` for commands.

## Integrations not enabled yet

Voice recognition (for example, ACRCloud), lyrics, and live charts need a chosen provider and API credentials. Telegram Stars, Click/Payme billing, VIP entitlements, and advertising placement also need merchant configuration and payment/webhook handling before they can be enabled. The catalog only sends licensed short previews where available; it does not provide full copyrighted tracks.