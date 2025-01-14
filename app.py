import streamlit as st
from transcription_service import transcribe_meeting
from nlp_processor import PVProcessor
from document_generator import DocumentGenerator
import tempfile
import os

def main():
    st.title("Gestionnaire de PV de CSE")
    
    # Sidebar pour la navigation
    page = st.sidebar.selectbox(
        "Navigation",
        ["Transcription", "Édition", "Export"]
    )
    
    if page == "Transcription":
        show_transcription_page()
    elif page == "Édition":
        show_edition_page()
    elif page == "Export":
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
            
            # Traitement NLP
            processor = PVProcessor()
            pv_data = processor.process_transcript(transcript)
            
            # Stockage dans la session
            st.session_state['pv_data'] = pv_data
            
            st.success('Transcription terminée!')
            st.json(pv_data)  # Affichage du résultat

def show_edition_page():
    st.header("Édition du PV")
    
    if 'pv_data' not in st.session_state:
        st.warning("Veuillez d'abord effectuer une transcription")
        return
    
    pv_data = st.session_state['pv_data']
    
    # Édition par section
    for section, content in pv_data.items():
        st.subheader(section.capitalize())
        for idx, item in enumerate(content):
            col1, col2 = st.columns([4, 1])
            with col1:
                new_text = st.text_area(
                    f"Intervention de {item['speaker']}",
                    value=item['text'],
                    key=f"{section}_{idx}"
                )
                pv_data[section][idx]['text'] = new_text
            with col2:
                st.text(f"Timestamp: {item['timestamp']}")
    
    if st.button("Sauvegarder les modifications"):
        st.session_state['pv_data'] = pv_data
        st.success("Modifications sauvegardées!")

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