# SimpleCut Add-on

A simple, vibe-coded way to trim the start and end of MP3 files directly on your Home Assistant media folder.

## How it works

1. You select a file from your `/media` library.
2. The server temporarily converts it to a WAV file (Proxy) for frame-perfect seeking.
3. You set your cut points (In/Out) on the WAV.
4. The server encodes the cut back to a high-quality MP3 and overwrites the original, preserving ID3 tags and album art.

## Features

* **Frame-Perfect Cuts**: Uses WAV proxying to avoid browser MP3 seeking drift.
* **Metadata Preservation**: Keeps your original ID3 tags and Album Art intact.
* **Auto-Cleanup**: Automatically deletes temporary WAV files when you switch tracks.

## Why the WAV conversion?

Browsers are surprisingly bad at streaming MP3s for editing. They often guess the total duration based on file size rather than reading the headers. This results in "drift"—you might click at 2:00, but the browser is actually processing audio from 1:55.

Converting to WAV first guarantees that the timestamp you select is exactly the frame that gets cut.
