import streamlit as st
from transcription_service import transcribe_meeting
from nlp_processor import PVProcessor
from document_generator import DocumentGenerator
import tempfile
import os

def main():
    st.title("Gestionnaire de PV de CSE")
    
    # Créer les onglets de navigation
    tab1, tab2, tab3 = st.tabs(["Transcription", "Édition", "Export"])
    
    # Contenu de l'onglet Transcription
    with tab1:
        show_transcription_page()
    
    # Contenu de l'onglet Édition
    with tab2:
        show_edition_page()
    
    # Contenu de l'onglet Export
    with tab3:
        show_export_page()

def show_transcription_page():
    st.header("Transcription Audio")
    
    uploaded_file = st.file_uploader("Choisir un fichier audio", type=['mp3', 'wav', 'm4a'])
    
    if uploaded_file is not None:
        with st.spinner('Transcription en cours...'):
            # Sauvegarde temporaire du fichier
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                audio_path = tmp_file.name
            
            # Lancement de la transcription
            transcript = transcribe_meeting(audio_path)
            
            # Stockage du transcript dans la session
            st.session_state['transcript'] = transcript
            
            # Traitement initial sans mapping
            processor = PVProcessor()
            pv_data = processor.process_transcript(transcript)
            
            # Stockage dans la session
            st.session_state['pv_data'] = pv_data
            
            st.success('Transcription terminée!')
            st.json(pv_data)
    
    # Sidebar pour la gestion des participants
    if 'transcript' in st.session_state:
        with st.sidebar:
            st.header("Gestion des participants")
            
            # Initialisation du mapping des speakers dans la session si nécessaire
            if 'speaker_mapping' not in st.session_state:
                speakers = list(set(utterance.speaker for utterance in st.session_state['transcript'].utterances))
                st.session_state['speaker_mapping'] = {speaker: "" for speaker in speakers}
            
            # Mapping des speakers identifiés
            st.subheader("Speakers identifiés")
            mapping_changed = False
            for speaker in st.session_state['speaker_mapping'].keys():
                new_name = st.text_input(
                    f"Nom pour {speaker}",
                    value=st.session_state['speaker_mapping'][speaker],
                    key=f"speaker_{speaker}"
                )
                if new_name != st.session_state['speaker_mapping'][speaker]:
                    st.session_state['speaker_mapping'][speaker] = new_name
                    mapping_changed = True
                print(st.session_state['speaker_mapping'])
            
            # Ajout de participants supplémentaires
            st.subheader("Autres participants présents")
            if 'additional_participants' not in st.session_state:
                st.session_state['additional_participants'] = []
            
            new_participant = st.text_input("Ajouter un participant")
            if st.button("Ajouter") and new_participant:
                if new_participant not in st.session_state['additional_participants']:
                    st.session_state['additional_participants'].append(new_participant)
                    mapping_changed = True
            
            # Affichage des participants supplémentaires
            for idx, participant in enumerate(st.session_state['additional_participants']):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(participant)
                with col2:
                    if st.button("Supprimer", key=f"del_{idx}"):
                        st.session_state['additional_participants'].pop(idx)
                        mapping_changed = True
            
            # Mise à jour automatique du PV si des changements sont détectés
            if mapping_changed:
                # Filtrer les mappings vides
                valid_mapping = {k: v for k, v in st.session_state['speaker_mapping'].items() if v}
                
                # Retraiter le transcript avec le mapping (sans retranscrire)
                processor = PVProcessor()
                updated_pv_data = processor.process_transcript(
                    st.session_state['transcript'],
                    speaker_mapping=valid_mapping,
                    additional_participants=st.session_state['additional_participants']
                )
                
                # Mise à jour du PV
                st.session_state['pv_data'] = updated_pv_data

def show_edition_page():
    st.header("Édition du PV")
    
    if 'pv_data' not in st.session_state:
        st.warning("Veuillez d'abord effectuer une transcription")
        return
    
    # Stocker une copie locale de pv_data
    pv_data = dict(st.session_state['pv_data'])
    
    try:
        # Édition par section
        for section, content in pv_data.items():
            if not content:  # Skip empty sections
                continue
                
            st.subheader(section.capitalize())
            # Vérifier que content est une liste de dictionnaires
            if isinstance(content, list):
                for idx, item in enumerate(content):
                    if isinstance(item, dict):  # Vérifier que item est un dictionnaire
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            new_text = st.text_area(
                                f"Intervention de {item.get('speaker', 'Inconnu')}",
                                value=item.get('text', ''),
                                key=f"{section}_{idx}"
                            )
                            pv_data[section][idx]['text'] = new_text
                        with col2:
                            st.text(f"Timestamp: {item.get('timestamp', 'N/A')}")
        
        if st.button("Sauvegarder les modifications"):
            st.session_state['pv_data'] = pv_data
            st.success("Modifications sauvegardées!")
            
    except Exception as e:
        st.error(f"Une erreur s'est produite : {str(e)}")
        print(f"Debug - Error: {str(e)}")
        print(f"Debug - PV Data: {pv_data}")

def show_export_page():
    st.header("Export du Document")
    
    if 'pv_data' not in st.session_state:
        st.warning("Aucun PV à exporter")
        return
    
    format_export = st.radio("Format d'export", ["PDF", "Word"])
    
    if st.button("Générer le document"):
        generator = DocumentGenerator()
        with st.spinner("Génération en cours..."):
            if format_export == "PDF":
                file_content = generator.generate_pdf(st.session_state['pv_data'])
                st.download_button(
                    label="Télécharger le PDF",
                    data=file_content,
                    file_name="pv_cse.pdf",
                    mime="application/pdf"
                )
            else:
                file_content = generator.generate_docx(st.session_state['pv_data'])
                st.download_button(
                    label="Télécharger le document Word",
                    data=file_content,
                    file_name="pv_cse.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

if __name__ == "__main__":
    main()