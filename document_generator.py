from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import tempfile
import os

class DocumentGenerator:
    def generate_pdf(self, pv_data):
        # Utiliser un fichier temporaire
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            c = canvas.Canvas(tmp_file.name, pagesize=A4)
            width, height = A4
            
            # Position initiale
            y = height - 50
            
            # Titre
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, y, "Procès Verbal de CSE")
            y -= 30
            
            # Contenu par section
            c.setFont("Helvetica", 12)
            for section, items in pv_data.items():
                if not items:  # Si la section est vide
                    continue
                    
                # Titre de section
                c.setFont("Helvetica-Bold", 14)
                y -= 20
                c.drawString(50, y, section.capitalize())
                y -= 20
                
                # Contenu de la section
                c.setFont("Helvetica", 12)
                
                # Traitement différent selon la section
                if section == "présences":
                    # Pour la section présences, c'est une liste de noms
                    text = "Personnes présentes : " + ", ".join(items)
                    words = text.split()
                    line = []
                    for word in words:
                        line.append(word)
                        if len(' '.join(line)) > 80:
                            c.drawString(50, y, ' '.join(line[:-1]))
                            y -= 15
                            line = [line[-1]]
                    if line:
                        c.drawString(50, y, ' '.join(line))
                        y -= 25
                else:
                    # Pour les autres sections (discussions, décisions, votes)
                    for item in items:
                        # Nouvelle page si nécessaire
                        if y < 50:
                            c.showPage()
                            y = height - 50
                        
                        if isinstance(item, dict):
                            if 'speaker' in item and 'text' in item:
                                speaker_text = f"{item['speaker']}: {item['text']}"
                                
                                # Découpage du texte en lignes de 80 caractères
                                words = speaker_text.split()
                                line = []
                                for word in words:
                                    line.append(word)
                                    if len(' '.join(line)) > 80:
                                        c.drawString(50, y, ' '.join(line[:-1]))
                                        y -= 15
                                        line = [line[-1]]
                                
                                if line:
                                    c.drawString(50, y, ' '.join(line))
                                    y -= 25
                            else:
                                # Pour les éléments qui n'ont pas speaker/text
                                text = str(item)
                                c.drawString(50, y, text)
                                y -= 25
                        else:
                            # Pour les éléments qui ne sont pas des dictionnaires
                            text = str(item)
                            c.drawString(50, y, text)
                            y -= 25

            c.save()
            
            # Lire le contenu du PDF
            with open(tmp_file.name, 'rb') as file:
                pdf_content = file.read()
            
            # Nettoyer le fichier temporaire
            os.unlink(tmp_file.name)
            
            return pdf_content