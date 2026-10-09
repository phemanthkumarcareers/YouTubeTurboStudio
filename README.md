# 🎬 YouTube Turbo Studio

**An Autonomous Multi-Channel Agentic AI Video Studio & YouTube Publishing Engine.**

Combines the viral topic intelligence, hook tournaments, cinematic Ken Burns rendering, and automated YouTube OAuth workflows of **YouTube AI Agent Studio** with the versatile multi-LLM, multi-engine stock/animation capabilities of **MoneyPrinterTurbo**, powered by a **Sky Blue & YouTube Red Mix Theme** and the **Section 3/4 Originality & Content Guard Gate**.

![YouTube Turbo Studio Dashboard](docs/images/studio_dashboard_preview.jpg)

---

## 🌟 Key Highlights & Capabilities

### ⚡ 1. Three Content Modes & Content Family Model
- **`Long Video` (16:9 Standard)**: Generates complete long-form explainer documentaries. Upon rendering, automatically registers into the channel's `content_history` as an eligible parent for derived Shorts.
- **`Shorts` (9:16 Standalone)**: Generates standalone vertical videos. Guarantees zero parent video requirement and never receives parent URLs or CTAs.
- **`Shorts - Link Long Video`**: Generates purpose-built Shorts derived from the strongest subtopics, moments, or lessons of an eligible Long video:
  - **Dynamic Lock State**: Automatically disabled with a protective badge (`🔒 Generate, import, or publish an eligible Long video first`) until an eligible Long video exists on the active channel.
  - **Channel Isolation**: Parent dropdown strictly filters to active-channel Long videos. Cross-channel linking (e.g. Kids Short linking to Science Long video) is rejected server-side.
  - **Lineage Tracking**: Stores `parent_content_id` and `content_family_id`.
  - **Dynamic Real URL Injection**: Injects the verified YouTube URL (`Watch the full video: https://youtube.com/watch?v=...`) into the Short description once the parent is published. **Never fabricates placeholder URLs** if the parent is not yet published.

---

### 🛡️ 2. Originality Engine & Hard Publishing Gate
Successful rendering does not automatically qualify a video for upload. Every generated video is evaluated against historical channel content to eliminate template repetition, spam, and content duplication.

![Review & Publish Studio with Internal Readiness Panel](docs/images/review_studio_preview.jpg)

- **Discrete Originality Score (0–100, Default Threshold: 85)**:
  - **Script Similarity**: N-gram shingle overlap against channel history.
  - **Concept Similarity**: Topic and keyword repetition detection.
  - **Hook Repetition**: Opening phrase and psychological angle diversity.
  - **Story Structure**: Plot beat pattern detection.
  - **Visual & Scene Reuse**: Detects excessive sequence duplication.
  - **Animation Action Reuse**: Checks for repeated character action chains.
  - **Metadata & Value-Add**: Validates informational and educational substance.
  - **Recurring Character Exception**: Allows recurring characters (e.g., *Toby the Tiger* or *Dr. Silas*) while penalizing identical story templates.
- **Separate Production Quality Score (Default Threshold: 90)**:
  - Distinct from originality, auditing audio quality, pacing, text legibility, and technical resolution.
- **Internal Readiness & Content Guard Panel**:
  - Live audit table in the Review Studio checking Production Quality, Originality, Technical QC, Content Compliance, Channel Validation, and Kids Safety.
  - Displays internal status: `READY FOR REVIEW` or `BLOCKED` *(includes explicit monetization disclaimer)*.
- **Targeted Stage Regeneration**:
  - Automatically isolates and re-runs only the failing component (hook, script rewrite, story structure, visual beats, audio narration, or subtitles) without rebuilding the entire pipeline from scratch.

---

### 🏛️ 3. Dual Engine Architecture & Multi-Channel Management
- **Media Video Engine** (*The AI Brief It*): Stock footage hierarchy (Pexels HD Video first, Pexels Photos with Ken Burns pan/zoom fallback), word-synchronized animated subtitles, and audio ducking.
- **Shared Animation Engine** (*Kids Wonder Lab* & *Golden Stories & Wisdom*): Programmatic scene composition, character sprite animations, and stage choreography.
  - **Kids Safeguards Gate**: Mandatory age verification, safe visual/language scanning, educational accuracy checks, and Made-for-Kids declarations.
  - **Elders Channel**: Adult character pack, unhurried narration pacing, and nostalgic environments without inheriting child-specific constraints.
- **Zero Cross-Channel Contamination**: Distinct OAuth credentials, API keys, video engines, and settings isolated in `channels/<channel_id>/`.

---

### ⚙️ 4. Automation & Background Heavy Worker
- **Single Heavy Render Worker**: Runs background encoding with `max_workers = 1` concurrency to prevent CPU/GPU encoding thrashing.
- **Human-in-the-Loop Review Queue**: Renders that pass all gates enter a pending queue requiring review before live publishing.
- **Channel-Partitioned Analytics & Learning Loop**: Tracks view retention, likes, and watch time strictly per channel to discover winning topic pillars and formats.

---

## 💻 Installation & Setup

### Prerequisites
1. **Python 3.10 to 3.12** installed on your system.
2. **FFmpeg** installed and accessible in your system `PATH` (required for MoviePy rendering):
   - **Windows**: `winget install Gyan.FFmpeg` or download from [ffmpeg.org](https://ffmpeg.org).
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt install ffmpeg`
3. **Git** installed.

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/hemanthkumar/YouTubeTurboStudio.git
cd YouTubeTurboStudio
```

---

### Step 2: Create and Activate a Virtual Environment
```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Windows (Command Prompt)
python -m venv .venv
.\.venv\Scripts\activate.bat

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

---

### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

### Step 4: Configure API Keys & Environment
Create a `.env` file in the root directory (or configure keys directly through the **API Keys & AI** tab in the web UI):

```ini
# Primary LLM Provider: 'gemini' | 'groq' | 'openai'
LLM_PROVIDER=gemini

# Google Gemini API Key (Get free at https://aistudio.google.com)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash

# Groq API Key (Optional free high-speed LLaMA at https://console.groq.com)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# Free Stock Media API Keys
PEXELS_API_KEY=your_pexels_api_key_here
PIXABAY_API_KEY=your_pixabay_api_key_here
```

---

### Step 5: Start YouTube Turbo Studio

```bash
# Direct Python Launch:
python app.py

# Or via Windows Launcher:
.\run.ps1
# or
run.bat
```

The studio will start and automatically open in your default browser at:  
👉 **`http://localhost:7860`**

---

## 🔑 YouTube OAuth Setup (Per Channel)

You can connect one or more YouTube channels directly through the UI:

1. Open the **YouTube OAuth & Config** tab in the studio.
2. In **Client Secret Setup**:
   - Upload your `client_secret.json` obtained from [Google Cloud Console](https://console.cloud.google.com/apis/credentials), **OR**
   - Paste your **Client ID** and **Client Secret** and click **Save Credentials**.
3. Click **Connect YouTube Channel** to trigger Google Sign-In in your browser.
4. Accept permissions. The badge will immediately switch to **Connected & Authorized** displaying your channel name and subscriber count!
5. Repeat for any other channel by selecting the channel from the top header dropdown. Credentials remain strictly isolated in `channels/<channel_id>/.env`.

---

## 🧪 Testing the Pipeline

Run the comprehensive test suite to verify all engine features, channels, gates, and relationship lineages:

```bash
# Run all 72 automated test cases
python -m unittest discover -s tests

# Or run the Content Guard & Addendum V1 tests specifically
python -m unittest tests/test_content_guard.py
```

*Note: Automated tests run with simulated mock YouTube fixtures. Zero live videos are published or uploaded during testing.*

---

## 📂 Project Architecture

```
YouTubeTurboStudio/
├── app.py                      # Flask REST API server & web routes
├── config.py                   # Central configuration & .env sync
├── requirements.txt            # Python dependencies
├── run.ps1 / run.bat           # 1-click launch scripts
│
├── core/
│   ├── channel_registry.py     # Multi-channel registry (Science, Kids, Elders)
│   ├── channel_context.py      # Isolated per-channel execution context
│   ├── credential_manager.py   # Secure per-channel credential encryption/storage
│   ├── content_family.py       # Content Family lineage & parent URL resolver
│   ├── originality_engine.py   # 9-dimension originality & anti-spam engine
│   ├── compliance_gate.py      # Hard publishing gate & internal readiness audit
│   ├── targeted_regeneration.py# Stage-level targeted regeneration engine
│   ├── pipeline_router.py      # Routes generation to Stock or Animation engine
│   └── pipeline.py             # Phase 2 Media Video Engine pipeline
│
├── animation/
│   ├── renderer.py             # Shared MoviePy animation compositor
│   ├── storyboarder.py         # Script-to-scene-graph generator
│   └── qc.py                   # Animation quality control checks
│
├── kids/                       # Kids Wonder Lab channel package
│   ├── characters.py           # Kids characters (Toby the Tiger, Pip the Panda)
│   └── safeguards.py           # Mandatory child safety & educational validator
│
├── elders/                     # Golden Stories & Wisdom channel package
│   ├── characters.py           # Adult character pack (Dr. Silas, Arthur, Martha)
│   └── qc.py                   # Pacing & clarity validation
│
├── automation/
│   ├── db.py                   # SQLite persistence (jobs, review queue, content history)
│   ├── job_queue.py            # Channel-immutable job queue
│   ├── worker.py               # Single Heavy Render Worker (max_workers=1)
│   ├── review_queue.py         # Human-in-the-loop review queue
│   └── analytics.py            # Channel-partitioned metrics store
│
├── youtube/
│   ├── auth.py                 # OAuth2 PKCE login & refresh manager
│   ├── channel_verifier.py     # Channel identity security verifier
│   └── uploader.py             # Resumable video uploader with parent URL injection
│
├── static/
│   ├── css/studio.css          # Sky Blue & YouTube Red Mix Design System
│   └── js/studio.js            # Studio frontend, parent selector, readiness UI
│
├── templates/
│   └── index.html              # Studio web interface
│
└── docs/
    ├── MASTER_ARCHITECTURE.md  # V2 Master Architecture specification
    ├── ARCHITECTURE_ADDENDUM_CONTENT_GUARD.md # Addendum V1 specification
    └── images/                 # Studio UI screenshots
```

---

## 🎨 Design System

YouTube Turbo Studio features a custom **Sky Blue & YouTube Red Mix Theme**:
- **Primary Interactive**: Vibrant Sky Blue (`#0ea5e9` / `#38bdf8`) for controls, focus states, and research flows.
- **YouTube Accent**: Iconic YouTube Red (`#ff0033` / `#cc0029`) for video upload buttons, running indicators, and active navigation bars.
- **Canvas**: Midnight Slate (`#060913` and `#0c1322`) for high-contrast readability.

---

## 📄 License

This project is licensed under the MIT License — see the LICENSE file for details.
