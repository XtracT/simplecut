# SimpleCut

This project is vibe coded.

I needed a simple way to trim the start and end of MP3 files directly on my NAS without downloading them to my computer, editing them, and uploading them back. Most web editors are full blown streamed desktop apps, and I wanted something simpler. 

## How it works

1. You select a file from your library.
2. The server temporarily converts it to a WAV file (Proxy).
3. You set your cut points on the WAV.
4. The server encodes the cut back to a high-quality MP3 and overwrites the original.

## Installation

Just use docker compose: 

**docker-compose.yml**
```yaml
services:
  simplecut:
    container_name: simplecut
    image: ghcr.io/xtract/simplecut:latest
    ports:
      - "5000:5000"
    volumes:
      - /path/to/your/music:/music
    restart: unless-stopped
```
Change port and path to your music to something that works for you. 

Run it:
```bash
docker-compose up -d
```

Go to `http://whatever-ip:5000`.

## Features
* Cuts are frame-perfect.
* Preserves your original ID3 tags and Album Art.
* Auto-cleans up temporary WAV files when you switch tracks or restart the container. Just don't store your media in WAV!

## Why the WAV conversion?
Browsers are surprisingly bad at streaming MP3s for editing. They often guess the total duration based on file size rather than reading the headers. This results in "drift"—you might click at 2:00, but the browser is actually processing audio from 1:55.

Additionally, if your MP3 has a non-standard sample rate (like 48kHz from a video rip!), browsers often play it at the wrong speed inside the web player.

Converting to WAV first guarantees that the timestamp you select is exactly the frame that gets cut. It is one way to get subnanosecond perfect accuracy in a web browser.
