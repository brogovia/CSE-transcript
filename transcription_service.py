from dataclasses import dataclass
import json
import os
import assemblyai as aai
import logging
import streamlit as st
from pathlib import Path

# Configuration du logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@dataclass
class Utterance:
    """Représente une intervention dans la transcription"""
    speaker: str
    text: str
    start: int
    end: int

@dataclass
class Transcript:
    """Représente une transcription complète"""
    utterances: list[Utterance]
    error: str | None = None

    def to_dict(self) -> dict:
        """Convertit la transcription en dictionnaire pour la sérialisation"""
        return {
            'utterances': [
                {
                    'speaker': u.speaker,
                    'text': u.text,
                    'start': u.start,
                    'end': u.end
                } for u in self.utterances
            ]
        }

class TranscriptionService:
    """Service de transcription avec gestion des mocks et de la configuration"""
    
    MOCK_FILE = 'mock_transcript.json'
    
    def __init__(self):
        logger.debug("Initialisation du TranscriptionService")
        
        # Récupérer les variables depuis secrets.toml
        use_mock = st.secrets.get('USE_MOCK', False)  # Valeur par défaut à False
        logger.debug(f"Valeur brute de USE_MOCK: {use_mock}")
        
        # Modification de la logique de parsing de USE_MOCK
        self.use_mock = use_mock.lower() in ['true', '1', 'yes', 'y'] if isinstance(use_mock, str) else bool(use_mock)
        
        logger.debug(f"use_mock après traitement: {self.use_mock}")
        
        if not self.use_mock:
            logger.debug("Mode réel activé, vérification de la clé API")
            api_key = st.secrets["ASSEMBLYAI_API_KEY"]
            if not api_key:
                raise ValueError("ASSEMBLYAI_API_KEY non définie dans les secrets")
            logger.debug("Clé API AssemblyAI trouvée")
            aai.settings.api_key = api_key

    def transcribe(self, audio_file_path: str | Path) -> Transcript:
        """Transcrit un fichier audio en utilisant le mode réel ou mock selon la configuration"""
        logger.info(f"Début de la transcription en mode {'mock' if self.use_mock else 'réel'}")
        try:
            if self.use_mock:
                logger.debug("Utilisation du mock")
                return self._transcribe_mock()
            logger.debug("Utilisation de la transcription réelle")
            return self._transcribe_real(audio_file_path)
        except Exception as e:
            logger.error(f"Erreur lors de la transcription: {str(e)}", exc_info=True)
            raise
        finally:
            if isinstance(audio_file_path, (str, Path)) and os.path.exists(audio_file_path):
                logger.debug(f"Nettoyage du fichier temporaire: {audio_file_path}")
                os.unlink(audio_file_path)

    def _transcribe_mock(self) -> Transcript:
        """Charge une transcription mockée depuis un fichier JSON"""
        logger.debug(f"Tentative de lecture du fichier mock: {self.MOCK_FILE}")
        try:
            with open(self.MOCK_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.debug("Fichier mock chargé avec succès")
            utterances = [
                Utterance(
                    speaker=u['speaker'],
                    text=u['text'],
                    start=u['start'],
                    end=u['end']
                ) for u in data['utterances']
            ]
            
            return Transcript(utterances=utterances)
            
        except FileNotFoundError as e:
            logger.error(f"Fichier mock non trouvé: {e}")
            raise Exception(
                "Fichier de mock non trouvé. Veuillez d'abord exécuter "
                "le service en mode réel pour générer les données de mock."
            )

    def _transcribe_real(self, audio_file_path: str | Path) -> Transcript:
        """Effectue une vraie transcription via AssemblyAI"""
        logger.debug("Configuration de la transcription AssemblyAI")
        config = aai.TranscriptionConfig(
            speaker_labels=True,
            language_code="fr",
            punctuate=True,
            format_text=True
        )
        
        logger.debug(f"Début de la transcription du fichier: {audio_file_path}")
        aai_transcript = aai.Transcriber().transcribe(
            str(audio_file_path),
            config=config
        )
        
        if aai_transcript.error:
            logger.error(f"Erreur de transcription AssemblyAI: {aai_transcript.error}")
            raise Exception(f"Erreur de transcription: {aai_transcript.error}")
        
        logger.debug("Conversion du transcript AssemblyAI")
        utterances = [
            Utterance(
                speaker=u.speaker,
                text=u.text,
                start=u.start,
                end=u.end
            ) for u in aai_transcript.utterances
        ]
        
        transcript = Transcript(utterances=utterances)
        
        logger.debug(f"Sauvegarde du mock dans {self.MOCK_FILE}")
        with open(self.MOCK_FILE, 'w', encoding='utf-8') as f:
            json.dump(transcript.to_dict(), f, ensure_ascii=False, indent=2)
            
        return transcript

def transcribe_meeting(audio_file_path: str | Path) -> Transcript:
    """Point d'entrée principal pour la transcription"""
    logger.info("Démarrage d'une nouvelle transcription")
    service = TranscriptionService()
    return service.transcribe(audio_file_path)