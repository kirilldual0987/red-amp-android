# 🔴 Red-Amp Player for Android

![Version](https://img.shields.io/badge/version-1.3-red)
![Android](https://img.shields.io/badge/Android-5.0+-green)
![License](https://img.shields.io/badge/license-MIT-blue)

Minimalist music player for Android with dark theme and no emojis.

## ✨ Features

- 🎵 **Audio Formats:** MP3, WAV, OGG, M4A, FLAC, AAC
- 📁 **Folder Scanning:** Browse and scan music folders
- 💾 **Playlist:** Auto-save and restore playlists
- 📊 **Visualizer:** Real-time audio visualization
- 🔀 **Shuffle & Repeat:** Multiple playback modes
- 🎨 **Dark Theme:** Strict design without emojis
- ⚡ **Lightweight:** ~35-40 MB APK

## 📱 Requirements

- **Minimum Android:** 5.0 (Lollipop / API 21)
- **Tested on:** Android 5-13
- **Permissions:** Storage access

## 📥 Installation

### Method 1: Download Release
1. Go to [Releases](../../releases)
2. Download `Red-Amp-v1.3.apk`
3. Install on your Android device
4. Enable "Install from Unknown Sources" if asked

### Method 2: Build from Source
See [Building](#-building) section below.

## 🚀 Usage

1. **First Launch:** Grant storage permissions
2. **Add Music:** Tap `[SCAN]` → Select folder
3. **Play:** Double-tap track to play
4. **Controls:**
   - `[>]` / `[||]` - Play/Pause
   - `[<<]` - Previous track
   - `[>>]` - Next track
   - `[SHF]` - Toggle shuffle
   - `[RPT]` - Cycle repeat (Off → All → One)
   - `[VOL]` - Adjust volume

## 🛠️ Building

### Prerequisites
```bash
# Install dependencies
pip install buildozer cython==0.29.36
