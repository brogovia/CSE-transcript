from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

class DocumentGenerator:
    def generate_pdf(self, pv_data):
        pdf_path = "pv_cse.pdf"
        c = canvas.Canvas(pdf_path, pagesize=A4)
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
            if items:  # Si la section n'est pas vide
                # Titre de section
                c.setFont("Helvetica-Bold", 14)
                y -= 20
                c.drawString(50, y, section.capitalize())
                y -= 20
                
                # Contenu de la section
                c.setFont("Helvetica", 12)
                for item in items:
                    # Nouvelle page si nécessaire
                    if y < 50:
                        c.showPage()
                        y = height - 50
                    
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

        c.save()
        
        with open(pdf_path, 'rb') as file:
            return file.read()