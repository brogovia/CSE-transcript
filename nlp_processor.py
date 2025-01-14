from transformers import Pipeline

class PVProcessor:
    def __init__(self):
        self.sections = {
            "présences": [],
            "discussions": [],
            "décisions": [],
            "votes": []
        }
    
    def process_transcript(self, transcript):
        # Pour l'instant, tout va dans "discussions"
        for utterance in transcript.utterances:
            self.sections["discussions"].append({
                "speaker": utterance.speaker,
                "text": utterance.text,
                "timestamp": utterance.start
            })
        
        return self.sections 