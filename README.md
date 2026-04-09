# 🚀 RK TechFlow AI Automator

An autonomous HD video production engine that creates and uploads YouTube Shorts daily.

## 🛠️ Tech Stack
- **AI:** Google Gemini 2.5 Flash
- **Visuals:** Pexels API
- **Audio:** gTTS
- **Processing:** MoviePy

## 📋 Features
- **Auto-News:** Fetches the latest IT industry updates.
- **Auto-Edit:** Loops and stitches 1080p HD video to exactly 60 seconds.
- **Auto-Upload:** Uses OAuth2 tokens for hands-free YouTube publishing.
- **High Quality:** Encoded at 6000k bitrate with clear 192k audio.

## ⚙️ Setup
1. Clone the repo.
2. Create a `.env` file with `GEMINI_API_KEY` and `PEXELS_API_KEY`.
3. Add your `client_secret.json` from Google Cloud Console.
4. Run `python app.py`.