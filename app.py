import os
import random
import time
import requests
import json
from dotenv import load_dotenv
from google import genai
from gtts import gTTS
from moviepy import AudioFileClip, VideoFileClip, concatenate_videoclips
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- 1. CONFIGURATION ---
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
PEXELS_KEY = os.getenv("PEXELS_API_KEY")

# --- 2. THE VISUAL ENGINE ---
def get_pexels_video(query):
    print(f"🔍 Searching Pexels for: {query}...")
    headers = {"Authorization": PEXELS_KEY}
    url = f"https://api.pexels.com/videos/search?query={query}&orientation=portrait&per_page=1"
    
    try:
        response = requests.get(url, headers=headers).json()
        if not response.get('videos'):
            return get_pexels_video("technology")
            
        video_data = response['videos'][0]['video_files']
        download_url = next(v['link'] for v in video_data if v['width'] >= 1080)
        
        v_res = requests.get(download_url)
        with open("background.mp4", 'wb') as f:
            f.write(v_res.content)
        return "background.mp4"
    except Exception as e:
        print(f"❌ Pexels Error: {e}")
        return None

# --- 3. HIGH-QUALITY 60s ASSEMBLY ---
def assemble_video(audio_path, video_path):
    print("🎬 Stitching HD video (60s)...")
    audio = AudioFileClip(audio_path).with_duration(60)
    video = VideoFileClip(video_path).without_audio()

    if video.duration < 60:
        loops_needed = int(60 / video.duration) + 1
        video = concatenate_videoclips([video] * loops_needed)
    
    video = video.subclipped(0, 60).resized(height=1920)
    final = video.with_audio(audio)
    
    final.write_videofile(
        "final_video.mp4", 
        fps=30, 
        codec="libx264", 
        audio_codec="aac",
        bitrate="6000k",
        audio_bitrate="192k"
    )
    return "final_video.mp4"

# --- 4. THE AUTONOMOUS UPLOADER ---
def upload_to_youtube(title, description):
    print(f"🚀 Initializing Upload: {title}")
    scopes = ["https://www.googleapis.com/auth/youtube.upload"]
    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", scopes)
            creds = flow.run_local_server(port=0)
        
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            print("💾 Session saved!")

    youtube = build("youtube", "v3", credentials=creds)

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": f"{title} #shorts #tamil",
                "description": description,
                "categoryId": "28"
            },
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
        },
        media_body=MediaFileUpload("final_video.mp4")
    )
    request.execute()
    print("✅ SUCCESS! Video is LIVE.")

# --- 5. THE TAMIL OPTIMIZED BRAIN ---
def run_automation():
    print("🤖 Generating Tamil content (Quota-Saving Mode)...")
    
    # Updated prompt for Tamil language and 60-second timing
    combined_prompt = (
        "1. Identify the top IT industry news from the last 24h. "
        "2. Write a professional and engaging news script in TAMIL language. "
        "3. The script must be roughly 100-110 Tamil words to fit a 60-second video. "
        "4. Provide ONE English search keyword for a tech background video. "
        "5. Provide a 5-word English catchy title for SEO. "
        "Format exactly as: \nSCRIPT: [Tamil text]\nKEYWORD: [English word]\nTITLE: [English title]"
    )
    
    try:
        res = client.models.generate_content(model="gemini-2.5-flash", contents=combined_prompt)
        raw_output = res.text
        
        # Parsing the combined data
        script = raw_output.split("SCRIPT:")[1].split("KEYWORD:")[0].strip()
        keyword = raw_output.split("KEYWORD:")[1].split("TITLE:")[0].strip().replace('"', '')
        final_title = raw_output.split("TITLE:")[1].strip().split('\n')[0]
        
        print(f"📌 Tamil Script Generated. English Title: {final_title}")
        
        # Audio - Updated language code to 'ta' for Tamil
        print("🎙️ Generating Tamil Voiceover...")
        gTTS(text=script, lang='ta', slow=False).save("voiceover.mp3")
        
        # Visuals
        v_file = get_pexels_video(keyword)
        if v_file:
            assemble_video("voiceover.mp3", v_file)
            
            # Tamil Description
            desc = (
                f"நித்ய தொழில்நுட்ப செய்திகள் (Daily Tech Update): {final_title}\n\n"
                "🚀 For Automation Solutions: rktechflowsolutions@gmail.com\n"
                "Follow @rktechflowsolutions on Instagram.\n"
                "#itnews #tamil #technology #automation #shorts"
            )
            upload_to_youtube(final_title, desc)
            
    except Exception as e:
        if "429" in str(e):
            print("🚨 QUOTA ALERT: Free Tier exhausted. Wait for reset.")
        else:
            print(f"🚨 Pipeline Error: {e}")

if __name__ == "__main__":
    run_automation()