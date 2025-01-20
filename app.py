import streamlit as st
from transcription_service import transcribe_meeting
from nlp_processor import PVProcessor
from document_generator import DocumentGenerator
import tempfile
import os
from copy import deepcopy

class SessionState:
    """Classe pour gérer l'état de session de manière plus structurée"""
    DEFAULTS = {
        'transcript': None,
        'pv_data': None,
        'speaker_mapping': {},
        'export_format': "PDF",
        'file_processed': False,
        'discussions_modified': False
    }

    @classmethod
    def initialize(cls):
        """Initialise les variables de session avec des valeurs par défaut"""
        for key, default_value in cls.DEFAULTS.items():
            if key not in st.session_state:
                st.session_state[key] = default_value

    @classmethod
    def reset_file_state(cls):
        """Réinitialise l'état lié au fichier"""
        st.session_state.transcript = None
        st.session_state.pv_data = None
        st.session_state.speaker_mapping = {}
        st.session_state.file_processed = False

def handle_file_upload(uploaded_file):
    """Gère l'upload et la transcription du fichier audio"""
    if not uploaded_file:
        return False

    if st.session_state.file_processed:
        return True

    with st.spinner('Transcription en cours...'):
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            audio_path = tmp_file.name
        
        try:
            transcript = transcribe_meeting(audio_path)
            processor = PVProcessor()
            pv_data = processor.process_transcript(transcript)
            
            st.session_state.transcript = transcript
            st.session_state.pv_data = pv_data
            speakers = list(set(utterance.speaker for utterance in transcript.utterances))
            st.session_state.speaker_mapping = {speaker: "" for speaker in speakers}
            st.session_state.file_processed = True
            return True
            
        except Exception as e:
            st.error(f"Erreur lors de la transcription : {str(e)}")
            return False
        finally:
            # Nettoyer le fichier temporaire
            if os.path.exists(audio_path):
                os.unlink(audio_path)

def update_discussion(idx, field, value):
    """Met à jour une discussion de manière atomique"""
    if st.session_state.pv_data and "discussions" in st.session_state.pv_data:
        discussions = st.session_state.pv_data["discussions"]
        if 0 <= idx < len(discussions):
            discussions[idx][field] = value
            st.session_state.discussions_modified = True

def add_discussion(idx=None):
    """Ajoute une nouvelle discussion à l'index spécifié ou à la fin"""
    if not st.session_state.pv_data:
        return

    discussions = st.session_state.pv_data["discussions"]
    
    # Créer une nouvelle entrée vide
    new_entry = {
        "speaker": "",
        "text": "",
        "timestamp": 0
    }
    
    # Si idx est -1, ajouter au début
    if idx == -1:
        discussions.insert(0, new_entry)
    # Si idx est spécifié, ajouter après cet index
    elif idx is not None and 0 <= idx < len(discussions):
        discussions.insert(idx + 1, new_entry)
        # Nettoyer les clés de session pour les discussions suivantes
        for key in list(st.session_state.keys()):
            if key.startswith("discussion_"):
                try:
                    discussion_idx = int(key.split("_")[1])
                    if discussion_idx > idx:
                        del st.session_state[key]
                except (ValueError, IndexError):
                    continue
    # Sinon, ajouter à la fin
    else:
        discussions.append(new_entry)
    
    st.session_state.discussions_modified = True

def remove_discussion(idx):
    """Supprime une discussion à l'index spécifié"""
    if st.session_state.pv_data and "discussions" in st.session_state.pv_data:
        discussions = st.session_state.pv_data["discussions"]
        if 0 <= idx < len(discussions):
            # Supprimer la discussion
            discussions.pop(idx)
            # Nettoyer toutes les clés de session liées à cette discussion et aux suivantes
            for key in list(st.session_state.keys()):
                if key.startswith("discussion_"):
                    try:
                        discussion_idx = int(key.split("_")[1])
                        if discussion_idx >= idx:
                            del st.session_state[key]
                    except (ValueError, IndexError):
                        continue
            st.session_state.discussions_modified = True

def show_transcription_page():
    st.header("Transcription Audio")
    
    uploaded_file = st.file_uploader(
        "Choisir un fichier audio",
        type=['mp3', 'wav', 'm4a'],
        key="audio_uploader"
    )
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if uploaded_file is not None:
            handle_file_upload(uploaded_file)
    with col2:
        if st.session_state.file_processed and st.button("Nouveau fichier"):
            SessionState.reset_file_state()
            st.rerun()
    
    if st.session_state.transcript:
        show_participant_sidebar()

def show_participant_sidebar():
    """Affiche et gère la sidebar des participants"""
    with st.sidebar:
        st.header("Gestion des participants")
        
        st.subheader("Speakers identifiés")
        
        mapping_changed = False
        for speaker in st.session_state.speaker_mapping.keys():
            input_key = f"speaker_input_{speaker}"
            if input_key not in st.session_state:
                st.session_state[input_key] = st.session_state.speaker_mapping.get(speaker, "")
            
            new_name = st.text_input(
                f"Nom pour {speaker}",
                key=input_key
            )
            
            if new_name != st.session_state.speaker_mapping.get(speaker, ""):
                st.session_state.speaker_mapping[speaker] = new_name
                mapping_changed = True
        
        if mapping_changed:
            update_pv_with_mapping()
            st.rerun()

def update_pv_with_mapping():
    """Met à jour le PV avec le nouveau mapping des participants"""
    if not st.session_state.transcript:
        return
        
    valid_mapping = {k: v for k, v in st.session_state.speaker_mapping.items() if v}
    processor = PVProcessor()
    
    new_pv_data = processor.process_transcript(
        st.session_state.transcript,
        speaker_mapping=valid_mapping
    )
    
    if "discussions" in new_pv_data:
        for idx, discussion in enumerate(new_pv_data["discussions"]):
            speaker_state_key = f"discussion_{idx}_speaker"
            original_speaker = st.session_state.pv_data["discussions"][idx]["speaker"]
            
            if original_speaker in valid_mapping:
                st.session_state[speaker_state_key] = valid_mapping[original_speaker]
    
    st.session_state.pv_data = new_pv_data

def show_edition_page():
    st.header("Édition de la transcription")
    
    if st.session_state.pv_data is None:
        st.warning("Veuillez d'abord effectuer une transcription")
        return

    discussions = st.session_state.pv_data.get("discussions", [])
    available_speakers = get_available_speakers()

    if st.button("Ajouter une intervention au début"):
        add_discussion(idx=-1)
        st.rerun()

    for idx, item in enumerate(discussions):
        with st.expander(f"Intervention #{idx+1}", expanded=True):
            col1, col2, col3 = st.columns([2, 5, 1])
            
            with col1:
                state_key = f"discussion_{idx}_speaker"
                if state_key not in st.session_state:
                    st.session_state[state_key] = item["speaker"]
                
                speaker = st.selectbox(
                    "Intervenant",
                    options=available_speakers,
                    index=available_speakers.index(st.session_state[state_key]) if st.session_state[state_key] in available_speakers else 0,
                    key=f"speaker_select_{idx}",
                    on_change=lambda i=idx: update_discussion(i, "speaker", st.session_state[f"speaker_select_{i}"])
                )
            
            with col2:
                text_state_key = f"discussion_{idx}_text"
                if text_state_key not in st.session_state:
                    st.session_state[text_state_key] = item["text"]
                
                new_text = st.text_area(
                    "Texte",
                    value=st.session_state[text_state_key],
                    height=100,
                    key=f"text_{idx}",
                    on_change=lambda i=idx: update_discussion(i, "text", st.session_state[f"text_{i}"])
                )
            
            with col3:
                if st.button("Supprimer", key=f"del_{idx}"):
                    remove_discussion(idx)
                    st.rerun()
                
                if st.button("Insérer après", key=f"insert_{idx}"):
                    add_discussion(idx)
                    st.rerun()

    if discussions and st.button("Ajouter une intervention à la fin"):
        add_discussion()
        st.rerun()

def get_available_speakers():
    """Retourne la liste des speakers disponibles"""
    speakers = set(
        list(st.session_state.speaker_mapping.values()) +
        [item["speaker"] for item in st.session_state.pv_data.get("discussions", [])]
    )
    return sorted([s for s in speakers if s])

def show_export_page():
    st.header("Export du Document")
    
    if st.session_state.pv_data is None:
        st.warning("Aucun PV à exporter")
        return
    
    export_format = st.radio(
        "Format d'export",
        ["PDF", "Word"],
        index=0 if st.session_state.export_format == "PDF" else 1
    )
    
    if export_format != st.session_state.export_format:
        st.session_state.export_format = export_format
    
    if st.button("Générer le document"):
        generator = DocumentGenerator()
        with st.spinner("Génération en cours..."):
            try:
                if export_format == "PDF":
                    file_content = generator.generate_pdf(st.session_state.pv_data)
                    file_name = "pv_cse.pdf"
                    mime = "application/pdf"
                else:
                    file_content = generator.generate_docx(st.session_state.pv_data)
                    file_name = "pv_cse.docx"
                    mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                
                st.download_button(
                    label=f"Télécharger le {export_format}",
                    data=file_content,
                    file_name=file_name,
                    mime=mime
                )
            except Exception as e:
                st.error(f"Erreur lors de la génération : {str(e)}")

def main():
    st.title("Gestionnaire de PV de CSE")
    SessionState.initialize()
    
    # Créer les onglets
    tab1, tab2, tab3 = st.tabs(["Transcription", "Édition", "Export"])
    
    with tab1:
        show_transcription_page()
    
    with tab2:
        show_edition_page()
    
    with tab3:
        show_export_page()

if __name__ == "__main__":
    main()