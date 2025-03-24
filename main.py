import streamlit as st
import requests
import logging
import os
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# API endpoints
CLONE_URL = "https://api.play.ht/api/v2/cloned-voices/instant"
LIST_VOICES_URL = "https://api.play.ht/api/v2/cloned-voices"
GENERATE_AUDIO_URL = "https://api.play.ht/api/v2/tts/stream"

# Your credentials
USER_ID = "SAMBON1noiSP3YfgY7GHSqyEoMV2"
API_KEY = "ak-ffc1fe48dba2414a8661013e9066aca0"

# Create a folder for storing audio files
AUDIO_FOLDER = "generated_audio"
os.makedirs(AUDIO_FOLDER, exist_ok=True)

# Function to upload and clone a voice sample
def upload_voice_sample(file, voice_name):
    file_extension = file.name.split(".")[-1].lower()
    content_type = f"audio/{file_extension}" if file_extension in ["aac", "mpeg", "ogg", "wav", "webm", "flac", "midi", "mp4", "m4a", "wma", "amr", "aiff"] else "audio/wav"

    files = {
        "sample_file": (file.name, file, content_type),
        "voice_name": (None, voice_name)
    }

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {API_KEY}",
        "X-User-Id": USER_ID
    }

    response = requests.post(CLONE_URL, headers=headers, files=files)
    return response.json()

# Streamlit app
st.title("Voice Cloning and Text-to-Speech App")

# Step 1: Clone a voice
st.header("1. Clone a Voice")
voice_sample = st.file_uploader("Upload a voice sample (MP3, WAV, etc.)", type=["wav", "mp3", "m4a", "ogg"])

if voice_sample:
    voice_name = st.text_input("Enter a name for the cloned voice:")
    if st.button("Clone Voice"):
        with st.spinner("Cloning voice..."):
            clone_response = upload_voice_sample(voice_sample, voice_name)
            if "voice_id" in clone_response:
                st.success("Voice clone created successfully!")
                st.session_state.voice_id = clone_response["voice_id"]
                logger.info(f"Voice cloning response: {clone_response}")
            else:
                st.error(f"If cloning successful, the voice will be present in the next section.")
                logger.error(f"If cloning successful, the voice will be present in the next section.")

# Step 2: List cloned voices
st.header("2. Select a Cloned Voice")

headers = {
    "accept": "application/json",
    "X-User-ID": USER_ID,
    "Authorization": f"Bearer {API_KEY}"
}

try:
    response = requests.get(LIST_VOICES_URL, headers=headers)
    response.raise_for_status()
    voices = response.json()
    voice_options = [voice["id"] for voice in voices]
    selected_voice = st.selectbox("Choose a cloned voice", voice_options)
    logger.info(f"Retrieved {len(voice_options)} voices")
except requests.exceptions.RequestException as e:
    st.error(f"Error fetching voices: {str(e)}")
    logger.error(f"Error fetching voices: {str(e)}")
    selected_voice = None

# Step 3: Text-to-Speech
st.header("3. Text-to-Speech")

if selected_voice:
    text_input = st.text_area("Enter text to convert to speech (max 2000 characters)")

    if st.button("Generate Speech"):
        if len(text_input) > 2000:
            st.error("Text exceeds 2000 character limit. Please shorten your input.")
        else:
            payload = {
                "text": text_input,
                "voice": selected_voice,
                "output_format": "mp3",
                "voice_engine": "PlayHT2.0"
            }
            headers = {
                "accept": "audio/mpeg",
                "content-type": "application/json",
                "X-User-ID": USER_ID,
                "Authorization": f"Bearer {API_KEY}"
            }

            try:
                with st.spinner("Generating audio..."):
                    response = requests.post(GENERATE_AUDIO_URL, json=payload, headers=headers, stream=True)
                    response.raise_for_status()

                    # Generate a unique filename
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    mp3_filename = f"audio_{timestamp}.mp3"
                    mp3_filepath = os.path.join(AUDIO_FOLDER, mp3_filename)

                    # Save the MP3 audio file
                    with open(mp3_filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)

                    st.success(f"Audio generated and saved as {mp3_filename}")

            except requests.exceptions.RequestException as e:
                st.error(f"Error generating speech: {str(e)}")
                logger.error(f"Error generating speech: {str(e)}")
else:
    st.warning("Please select a cloned voice first.")

# Step 4: Play Generated Audio
st.header("4. Play Generated Audio")

# Get list of MP3 audio files
audio_files = [f for f in os.listdir(AUDIO_FOLDER) if f.endswith('.mp3')]

if audio_files:
    selected_audio = st.selectbox("Choose an audio file to play", audio_files)

    if st.button("Play Selected Audio"):
        audio_path = os.path.join(AUDIO_FOLDER, selected_audio)
        st.audio(audio_path, format="audio/mp3")
else:
    st.info("No audio files available. Generate some audio first!")

# Display debug information
if st.checkbox("Show Debug Info"):
    st.text(f"User ID: {USER_ID}")
    st.text(f"API Key: {API_KEY[:5]}...{API_KEY[-5:]})")  # Show partial API key for security
    st.text(f"Selected Voice: {selected_voice}")
    st.text(f"Text Input: {text_input}")
    st.text(f"Available Audio Files: {audio_files}")
