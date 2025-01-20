from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import cm
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, BinaryIO
import logging

class DocumentGenerator:
    """Générateur de documents pour les PV"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Configure les styles personnalisés pour le document"""
        # Vérifier si le style existe déjà avant de l'ajouter
        if 'Normal' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Normal',
                fontName='Helvetica',
                fontSize=11,
                leading=14,
                spaceAfter=6
            ))
        
        # Faire de même pour les autres styles
        if 'Speaker' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Speaker',
                parent=self.styles['Normal'],
                fontName='Helvetica-Bold'
            ))
        
        if 'Title' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Title',
                parent=self.styles['Normal'],
                fontName='Helvetica-Bold',
                fontSize=14,
                spaceAfter=12,
                alignment=1  # Center alignment
            ))
        
        self.styles.add(ParagraphStyle(
            name='Titre',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=30
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=20,
            spaceBefore=20
        ))

    def generate_pdf(self, pv_data: Dict[str, Any]) -> bytes:
        """
        Génère un PDF à partir des données du PV
        
        Args:
            pv_data: Dictionnaire contenant les données du PV
            
        Returns:
            Le contenu du PDF en bytes
        """
        try:
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                doc = SimpleDocTemplate(
                    tmp_file.name,
                    pagesize=A4,
                    rightMargin=2*cm,
                    leftMargin=2*cm,
                    topMargin=2*cm,
                    bottomMargin=2*cm
                )
                
                story = self._create_document_content(pv_data)
                doc.build(story)
                
                # Lire le contenu du PDF
                with open(tmp_file.name, 'rb') as file:
                    pdf_content = file.read()
                
                return pdf_content
                
        except Exception as e:
            logging.error(f"Erreur lors de la génération du PDF: {str(e)}")
            raise
        finally:
            if 'tmp_file' in locals():
                os.unlink(tmp_file.name)

    def _create_document_content(self, pv_data: Dict[str, Any]) -> list:
        """Crée le contenu du document"""
        story = []
        
        # Titre
        story.append(Paragraph("Procès Verbal de CSE", self.styles['Titre']))
        story.append(Spacer(1, 12))
        
        # Sections
        for section, items in pv_data.items():
            if not items:
                continue
                
            story.append(Paragraph(
                section.capitalize(),
                self.styles['SectionTitle']
            ))
            
            if section == "présences":
                story.extend(self._format_presences(items))
            else:
                story.extend(self._format_discussions(items))
            
            story.append(Spacer(1, 12))
        
        return story

    def _format_presences(self, presences: list) -> list:
        """Formate la section des présences"""
        return [
            Paragraph(
                f"Personnes présentes : {', '.join(presences)}",
                self.styles['Normal']
            )
        ]

    def _format_discussions(self, discussions: list) -> list:
        """Formate la section des discussions"""
        formatted = []
        for item in discussions:
            if isinstance(item, dict) and 'speaker' in item and 'text' in item:
                text = f"<b>{item['speaker']}</b>: {item['text']}"
                formatted.append(Paragraph(text, self.styles['Normal']))
            else:
                formatted.append(Paragraph(str(item), self.styles['Normal']))
        return formatted

    def generate_docx(self, pv_data: Dict[str, Any]) -> bytes:
        """
        Génère un document Word à partir des données du PV
        
        À implémenter selon les besoins
        """
        raise NotImplementedError(
            "La génération de documents Word n'est pas encore implémentée"
        )