from transformers import Pipeline

class PVProcessor:
    @staticmethod
    def process_transcript(transcript, speaker_mapping=None, additional_participants=None):
        # Ne plus utiliser self.sections pour éviter les problèmes d'état
        sections = {
            "présences": [],
            "discussions": [],
            "décisions": [],
            "votes": []
        }
        
        # Gérer la liste des présences
        presences = []
        if speaker_mapping:
            presences.extend(speaker_mapping.values())
        if additional_participants:
            presences.extend(additional_participants)
        sections["présences"] = list(set(presences))  # Enlever les doublons
        
        # Traiter les discussions avec le mapping des speakers
        sections["discussions"] = [
            {
                "speaker": speaker_mapping.get(utterance.speaker, utterance.speaker) if speaker_mapping else utterance.speaker,
                "text": utterance.text,
                "timestamp": utterance.start
            }
            for utterance in transcript.utterances
        ]
        
        return sections