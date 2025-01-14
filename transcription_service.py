import assemblyai as aai
from dotenv import load_dotenv
import os

# Charger les variables d'environnement depuis .env
load_dotenv()

def transcribe_meeting(audio_file_path):
    # Configurer la clé API
    aai.settings.api_key = os.getenv('ASSEMBLYAI_API_KEY')
    
    config = aai.TranscriptionConfig(
        speaker_labels=True,
        language_code="fr",
        punctuate=True,
        format_text=True
    )
    
    transcript = aai.Transcriber().transcribe(
        audio_file_path,
        config=config
    )
    
    if transcript.error:
        raise Exception(f"Transcription error: {transcript.error}")
        
    return transcript 