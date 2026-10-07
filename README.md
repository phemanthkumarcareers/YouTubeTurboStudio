# 🎬 YouTube Turbo Studio

**An all-in-one agentic AI faceless video generation platform and YouTube publishing studio.**

Combines the viral intelligence, agentic topic research, cinematic Ken Burns rendering, and YouTube OAuth automation of **YouTube AI Agent Studio** with the versatile multi-LLM, multi-stock provider, and rich voiceover catalog of **MoneyPrinterTurbo**.

---

## ✨ Highlights & Capabilities

### 🧠 1. Agentic AI Research & Scriptwriting
- **AI Trend Discovery**: Brainstorms high-retention viral concepts tailored to your channel niche and focus angles (Fermi Paradox, Quantum Mechanics, Frightening AI Horizons, Space Colonization, Paradoxes, etc.).
- **Multi-LLM Provider Engine**: Seamlessly switch between **Google Gemini** (Gemini 2.5 Flash, 2.0 Flash, 1.5 Flash, 2.5 Pro with automatic fallback chain) and **OpenAI / OpenAI-Compatible endpoints** (DeepSeek, Groq, Ollama, OpenRouter, Claude gateways).
- **Cinematic Script Generation**: Generates hook questions, segmented narration, visual stock footage search queries, and tags in structured JSON.
- **Negative Filters**: Built-in banned topic management to avoid topic duplication.

### 🖼️ 2. Multi-Source Footage & Visual Engine
- **Orientation & Format Awareness**: Switch between **Standard 16:9 Landscape (1920×1080)** for long-form YouTube explainers and **Vertical 9:16 Shorts (1080×1920)**.
- **Stock Media Sources**: Supports **Pexels HD Photos & Videos**, **Pixabay HD Photos & Videos**, or synthetic atmospheric gradient backgrounds.
- **Cinematic Ken Burns Effect**: Dynamic smooth pan and zoom animations into stock images with adjustable intensity.
- **Synced Subtitles**: Burned-in word-level synchronized subtitles with heavy contrast outlines and custom TTF typography (`BeVietnamPro-Bold.ttf`, etc.).

### 🎙️ 3. Audio & Voiceover Engine
- **100% Free Edge-TTS**: Deep catalog of natural neural voices across English (US, UK, India, Australia), Spanish, French, German, and Hindi.
- **Word-Boundary Subtitle Sync**: Generates word-level timestamped `.srt` files matching the exact voice cadence.
- **Live Voice Preview**: Test and listen to voice samples in the UI with a single click.
- **Background Music & Ducking**: Automatically mixes, loops, and ducks background music from `resources/songs/` with configurable volume.

### 📺 4. Full YouTube Integration via UI
- **Live OAuth Status**: Displays your YouTube channel connection state, channel title, channel ID, subscriber count, and upload authorization.
- **One-Click Browser Authorization**: Launch the Google OAuth login flow directly from the UI without touching the command line.
- **Client Secret Management**: Upload `client_secret.json` directly from your browser, or paste your `Client ID` and `Client Secret` in the settings UI.
- **Direct YouTube Upload**: Upload videos directly to YouTube with automated or custom title, description, tags, category, and privacy settings (Public, Unlisted, Private).
- **Scheduled Publishing**: Pick a publication date/time in the UI to schedule video releases.
- **Thumbnail Generator**: Auto-generates high-CTR 1280×720 YouTube thumbnails with bold typography, dark gradients, and channel branding.

---

## 🚀 Quick Start

### 1. Launch the Studio
Simply run the launcher script:
```powershell
# In PowerShell:
cd C:\Users\PC\Turbo\Youtube\YouTubeTurboStudio
.\run.ps1

# Or in Windows Command Prompt:
run.bat
```
The studio will automatically start and open in your default browser at:
**`http://localhost:7860`**

---

## 🔑 Updating API Keys & YouTube Settings in the UI

You never need to edit configuration files manually. Everything is controllable through the web interface:

### 1. Update API Keys
1. Open the **API Keys & AI** tab.
2. Enter your **Google Gemini API Key** and/or **OpenAI API Key**.
3. Enter your **Pexels API Key** and **Pixabay API Key**.
4. Click **Test Key** to verify connectivity with instant visual feedback.
5. Click **Save All API Keys & Settings** (automatically updates `.env` and `config_data.json`).

### 2. Configure YouTube Authentication & Channel
1. Open the **YouTube OAuth & Config** tab.
2. In **Client Secret Setup**, either:
   - Upload your `client_secret.json` using the file picker, OR
   - Enter your `Client ID` and `Client Secret` and click **Save Manual Credentials**.
3. Click **Connect YouTube Channel** to trigger Google Sign-In in your browser.
4. Once authorized, the status badge will display **Connected & Authorized** along with your channel details!
5. Configure your default video privacy, default category, and channel niche description.

---

## 📁 Project Structure

```
YouTubeTurboStudio/
├── app.py                      # Flask web server & REST API
├── config.py                   # Centralized configuration & .env sync
├── run.bat                     # 1-click Windows batch launcher
├── run.ps1                     # PowerShell launcher
├── requirements.txt            # Python dependencies
├── config_data.json            # Persistent studio configuration
├── client_secret.json          # Google OAuth credentials
├── youtube_token.pickle        # YouTube OAuth token
├── banned_topics.txt           # Banned topics list
│
├── core/
│   ├── pipeline.py             # Pipeline orchestrator
│   ├── state.py                # Global state tracker
│   └── logger.py               # Real-time logger & SSE streamer
│
├── agents/
│   ├── llm_client.py           # Multi-provider LLM (Gemini + OpenAI/DeepSeek)
│   ├── researcher.py           # Topic research agent
│   └── scriptwriter.py         # Scriptwriting agent
│
├── media/
│   ├── pexels_client.py        # Pexels stock downloader & validator
│   ├── pixabay_client.py       # Pixabay stock downloader & validator
│   └── media_manager.py        # Section asset coordinator & fallback generator
│
├── audio/
│   ├── edge_tts_engine.py      # Edge-TTS synthesizer & SRT generator
│   └── music_manager.py        # BGM manager & audio mixer
│
├── video/
│   ├── renderer.py             # MoviePy 1.0.3 + Pillow video composer
│   └── thumbnail_generator.py  # 1280x720 YouTube thumbnail maker
│
├── youtube/
│   ├── auth.py                 # OAuth manager & channel diagnostic
│   └── uploader.py             # Resumable video & thumbnail uploader
│
├── resources/
│   ├── fonts/                  # TrueType fonts
│   └── songs/                  # Background music tracks
│
├── static/
│   ├── css/studio.css          # Modern dark-mode styling
│   └── js/studio.js            # Client-side SPA controller
│
├── templates/
│   └── index.html              # Studio single-page application
│
└── output/                     # Generated videos, scripts, audio, thumbnails
```
# YouTubeTurboStudio
