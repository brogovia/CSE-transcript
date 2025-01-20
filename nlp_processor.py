from dataclasses import dataclass
from typing import List, Dict, Optional
import logging
from transcription_service import Transcript

@dataclass
class Discussion:
    """Représente une discussion dans le PV"""
    speaker: str
    text: str
    timestamp: int

@dataclass
class PVData:
    """Représente l'ensemble des données du PV"""
    presences: List[str]
    discussions: List[Discussion]
    decisions: List[str]
    votes: List[Dict]

    def to_dict(self) -> dict:
        """Convertit les données en dictionnaire pour la sérialisation"""
        return {
            "présences": self.presences,
            "discussions": [
                {
                    "speaker": d.speaker,
                    "text": d.text,
                    "timestamp": d.timestamp
                } for d in self.discussions
            ],
            "décisions": self.decisions,
            "votes": self.votes
        }

class PVProcessor:
    """Processeur pour générer les données du PV à partir d'une transcription"""
    
    def process_transcript(
        self,
        transcript: Transcript,
        speaker_mapping: Optional[Dict[str, str]] = None,
        additional_participants: Optional[List[str]] = None
    ) -> dict:
        """
        Traite une transcription pour générer les données du PV
        
        Args:
            transcript: La transcription à traiter
            speaker_mapping: Mapping optionnel des speakers vers leurs noms réels
            additional_participants: Liste optionnelle de participants additionnels
            
        Returns:
            Un dictionnaire contenant les données du PV structurées
        """
        try:
            # Initialiser les présences
            presences = self._get_presences(
                transcript, 
                speaker_mapping or {},
                additional_participants or []
            )
            
            # Traiter les discussions
            discussions = self._process_discussions(
                transcript,
                speaker_mapping or {}
            )
            
            # Créer l'objet PVData
            pv_data = PVData(
                presences=presences,
                discussions=discussions,
                decisions=[],  # À implémenter selon les besoins
                votes=[]       # À implémenter selon les besoins
            )
            
            return pv_data.to_dict()
            
        except Exception as e:
            logging.error(f"Erreur lors du traitement de la transcription: {str(e)}")
            raise

    def _get_presences(
        self,
        transcript: Transcript,
        speaker_mapping: Dict[str, str],
        additional_participants: List[str]
    ) -> List[str]:
        """Génère la liste des présences"""
        presences = set()
        
        # Ajouter les speakers mappés
        presences.update(
            name for name in speaker_mapping.values()
            if name.strip()
        )
        
        # Ajouter les participants additionnels
        presences.update(
            name for name in additional_participants
            if name.strip()
        )
        
        return sorted(presences)

    def _process_discussions(
        self,
        transcript: Transcript,
        speaker_mapping: Dict[str, str]
    ) -> List[Discussion]:
        """Traite les discussions de la transcription"""
        return [
            Discussion(
                speaker=speaker_mapping.get(utterance.speaker, utterance.speaker),
                text=utterance.text,
                timestamp=utterance.start
            )
            for utterance in transcript.utterances
        ]