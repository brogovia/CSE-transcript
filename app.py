import streamlit as st
from transcription_service import transcribe_meeting
from nlp_processor import PVProcessor
from document_generator import DocumentGenerator
import tempfile
import os
from copy import deepcopy

def handle_file_upload(uploaded_file):
    """Gère l'upload et la transcription du fichier audio"""
    with st.spinner('Transcription en cours...'):
        # Créer un fichier temporaire avec un contexte
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            audio_path = tmp_file.name
        
        try:
            transcript = transcribe_meeting(audio_path)
            processor = PVProcessor()
            pv_data = processor.process_transcript(transcript)
            
            # Mettre à jour l'état de session
            st.session_state.transcript = transcript
            st.session_state.pv_data = pv_data
            # Initialiser le mapping des speakers
            speakers = list(set(utterance.speaker for utterance in transcript.utterances))
            st.session_state.speaker_mapping = {speaker: "" for speaker in speakers}
            
            return True
            
        except Exception as e:
            st.error(f"Erreur lors de la transcription : {str(e)}")
            return False

def initialize_session_state():
    """Initialise les variables de session si elles n'existent pas"""
    if 'processing_key' not in st.session_state:
        st.session_state.processing_key = 0
        
    defaults = {
        'transcript': None,
        'pv_data': None,
        'speaker_mapping': {},
        'additional_participants': [],
        'export_format': "PDF",
        'last_update': 0  # Pour suivre la dernière mise à jour
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

def update_speaker_mapping(speaker, new_name):
    """Met à jour le mapping des speakers de manière sûre"""
    if new_name != st.session_state.speaker_mapping.get(speaker, ""):
        mapping_copy = dict(st.session_state.speaker_mapping)
        mapping_copy[speaker] = new_name
        st.session_state.speaker_mapping = mapping_copy
        return True
    return False

def update_pv_with_mapping():
    """Met à jour le PV avec le nouveau mapping"""
    if not st.session_state.transcript:
        return
        
    # Incrémenter la clé de traitement pour forcer une mise à jour
    st.session_state.processing_key += 1
    
    valid_mapping = {k: v for k, v in st.session_state.speaker_mapping.items() if v}
    processor = PVProcessor()
    updated_pv_data = processor.process_transcript(
        st.session_state.transcript,
        speaker_mapping=valid_mapping,
        additional_participants=st.session_state.additional_participants
    )
    
    st.session_state.pv_data = updated_pv_data
    st.session_state.last_update = st.session_state.processing_key

def show_transcription_page():
    st.header("Transcription Audio")
    
    # Utiliser la clé de traitement dans la key du file_uploader
    uploaded_file = st.file_uploader(
        "Choisir un fichier audio",
        type=['mp3', 'wav', 'm4a'],
        key=f"uploader_{st.session_state.processing_key}"
    )
    
    if uploaded_file is not None:
        handle_file_upload(uploaded_file)
    
    if st.session_state.transcript:
        with st.sidebar:
            st.header("Gestion des participants")
            
            # Gestion des speakers identifiés
            st.subheader("Speakers identifiés")
            mapping_changed = False
            
            # Utiliser la clé de traitement dans les keys des widgets
            for speaker in st.session_state.speaker_mapping.keys():
                new_name = st.text_input(
                    f"Nom pour {speaker}",
                    value=st.session_state.speaker_mapping[speaker],
                    key=f"speaker_{speaker}_{st.session_state.processing_key}"
                )
                if new_name != st.session_state.speaker_mapping[speaker]:
                    st.session_state.speaker_mapping[speaker] = new_name
                    mapping_changed = True
            
            # Gestion des participants supplémentaires
            new_participant = st.text_input(
                "Ajouter un participant",
                key=f"new_participant_{st.session_state.processing_key}"
            )
            
            if st.button(
                "Ajouter",
                key=f"add_button_{st.session_state.processing_key}"
            ) and new_participant:
                if new_participant not in st.session_state.additional_participants:
                    st.session_state.additional_participants.append(new_participant)
                    mapping_changed = True
            
            # Afficher les participants avec des clés uniques
            for idx, participant in enumerate(st.session_state.additional_participants):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(participant)
                with col2:
                    if st.button(
                        "Supprimer",
                        key=f"del_{idx}_{st.session_state.processing_key}"
                    ):
                        st.session_state.additional_participants.pop(idx)
                        mapping_changed = True
            
            if mapping_changed:
                update_pv_with_mapping()

def show_edition_page():
    st.header("Édition du PV")
    
    if st.session_state.pv_data is None:
        st.warning("Veuillez d'abord effectuer une transcription")
        return
    
    # Utiliser la clé de dernière mise à jour pour les widgets
    for section, content in st.session_state.pv_data.items():
        if not content:
            continue
            
        st.subheader(section.capitalize())
        if isinstance(content, list):
            for idx, item in enumerate(content):
                if isinstance(item, dict):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        new_text = st.text_area(
                            f"Intervention de {item.get('speaker', 'Inconnu')}",
                            value=item.get('text', ''),
                            key=f"{section}_{idx}_{st.session_state.last_update}"
                        )
                        if new_text != item.get('text', ''):
                            st.session_state.pv_data[section][idx]['text'] = new_text
                            
                            
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
    st.session_state.export_format = export_format
    
    if st.button("Générer le document"):
        generator = DocumentGenerator()
        with st.spinner("Génération en cours..."):
            if export_format == "PDF":
                file_content = generator.generate_pdf(st.session_state.pv_data)
                st.download_button(
                    label="Télécharger le PDF",
                    data=file_content,
                    file_name="pv_cse.pdf",
                    mime="application/pdf"
                )
            else:
                file_content = generator.generate_docx(st.session_state.pv_data)
                st.download_button(
                    label="Télécharger le document Word",
                    data=file_content,
                    file_name="pv_cse.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

def main():
    st.title("Gestionnaire de PV de CSE")
    initialize_session_state()
    
    tab1, tab2, tab3 = st.tabs(["Transcription", "Édition", "Export"])
    
    with tab1:
        show_transcription_page()
    with tab2:
        show_edition_page()
    with tab3:
        show_export_page()

if __name__ == "__main__":
    main()