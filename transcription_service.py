# transcription_service.py
from dataclasses import dataclass
import json
import os
import assemblyai as aai
from dotenv import load_dotenv
import tempfile
import shutil

@dataclass
class MockUtterance:
    speaker: str
    text: str
    start: int
    end: int

@dataclass
class MockTranscript:
    utterances: list
    error: str = None

def transcribe_meeting(audio_file_path):
    try:
        if os.getenv('USE_MOCK') == 'true':
            return transcribe_meeting_mock(audio_file_path)
        else:
            return transcribe_meeting_real(audio_file_path)
    finally:
        # Nettoyer le fichier temporaire si nécessaire
        if os.path.exists(audio_file_path):
            os.unlink(audio_file_path)

def transcribe_meeting_mock(audio_file_path):
    # Charger les données mockées
    try:
        with open('mock_transcript.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Créer les objets MockUtterance
        utterances = [
            MockUtterance(
                speaker=u['speaker'],
                text=u['text'],
                start=u['start'],
                end=u['end']
            ) for u in data['utterances']
        ]
        
        return MockTranscript(utterances=utterances)
        
    except FileNotFoundError:
        raise Exception("Mock data file not found. Please run the real service first to generate mock data.") 

def transcribe_meeting_real(audio_file_path):
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
    
    # Sauvegarder la réponse pour le mock
    with open('mock_transcript.json', 'w', encoding='utf-8') as f:
        json.dump({
            'utterances': [{
                'speaker': u.speaker,
                'text': u.text,
                'start': u.start,
                'end': u.end
            } for u in transcript.utterances]
        }, f, ensure_ascii=False, indent=2)
        
    return transcript 