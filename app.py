import os
import time
import requests
from dotenv import load_dotenv
from groq import Groq  # The new engine
from gtts import gTTS
from moviepy import AudioFileClip, VideoFileClip, concatenate_videoclips
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- 1. INITIALIZATION ---
load_dotenv()
# We are only using Groq now for high reliability and zero quota stress
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
PEXELS_KEY = os.getenv("PEXELS_API_KEY")

# --- 2. PEXELS VISUALS ---
def get_pexels_video(query):
    print(f"🔍 Searching Pexels for: {query}...")
    headers = {"Authorization": PEXELS_KEY}
    url = f"https://api.pexels.com/videos/search?query={query}&orientation=portrait&per_page=1"
    
    try:
        response = requests.get(url, headers=headers).json()
        if not response.get('videos'):
            return get_pexels_video("technology") # Fallback
            
        video_data = response['videos'][0]['video_files']
        download_url = next(v['link'] for v in video_data if v['width'] >= 1080)
        
        v_res = requests.get(download_url)
        with open("background.mp4", 'wb') as f:
            f.write(v_res.content)
        return "background.mp4"
    except Exception as e:
        print(f"❌ Pexels Error: {e}")
        return None

# --- 3. VIDEO ASSEMBLY (Shorts Optimized: 58s) ---
def assemble_video(audio_path, video_path):
    TARGET_DURATION = 58.0 
    print(f"🎬 Creating Shorts-ready HD video ({TARGET_DURATION}s)...")
    
    audio = AudioFileClip(audio_path).with_duration(TARGET_DURATION)
    video = VideoFileClip(video_path).without_audio()

    if video.duration < TARGET_DURATION:
        loops_needed = int(TARGET_DURATION / video.duration) + 1
        video = concatenate_videoclips([video] * loops_needed)
    
    video = video.subclipped(0, TARGET_DURATION).resized(height=1920)
    final = video.with_audio(audio)
    
    final.write_videofile(
        "final_video.mp4", 
        fps=30, 
        codec="libx264", 
        audio_codec="aac",
        bitrate="6000k"
    )
    return "final_video.mp4"

# --- 4. YOUTUBE UPLOADER ---
def upload_to_youtube(title, description):
    print(f"🚀 Uploading to YouTube: {title}")
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
    print("✅ SUCCESS! RK TechFlow video is LIVE.")

# --- 5. THE CONTENT ENGINE (Groq-Llama 3.3) ---
def run_automation():
    print("🤖 Generating Tamil News with Groq (14.4k RPD Mode)...")
    
    prompt = (
        "Role: Professional Tech Journalist. Language: TAMIL. "
        "Task: Identify the top 3 IT/AI news stories from the last 24 hours. "
        "Create a script of 90 Tamil words. "
        "Output Format MUST BE EXACTLY: "
        "SCRIPT: [Tamil News Script] "
        "KEYWORD: [Single English word for tech video] "
        "TITLE: [Catchy 5-word English SEO title]"
    )

    try:
        # Llama-3.3-70b is extremely high quality for Tamil scripts
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6
        )
        res_text = completion.choices[0].message.content
        
        # Data Parsing
        script = res_text.split("SCRIPT:")[1].split("KEYWORD:")[0].strip()
        keyword = res_text.split("KEYWORD:")[1].split("TITLE:")[0].strip().replace('"', '')
        final_title = res_text.split("TITLE:")[1].strip().split('\n')[0]
        
        print(f"📌 News Generated: {final_title}")
        
        # Audio & Video Generation
        gTTS(text=script, lang='ta', slow=False).save("voiceover.mp3")
        v_file = get_pexels_video(keyword)
        
        if v_file:
            assemble_video("voiceover.mp3", v_file)
            
            desc = (
                f"நித்ய தொழில்நுட்ப செய்திகள் (Daily Tech Update): {final_title}\n\n"
                "🚀 Automation Solutions: rktechflowsolutions@gmail.com\n"
                "#itnews #tamil #technology #automation #shorts"
            )
            upload_to_youtube(final_title, desc)
            
    except Exception as e:
        print(f"🚨 Groq Automation Error: {e}")

if __name__ == "__main__":
    run_automation()