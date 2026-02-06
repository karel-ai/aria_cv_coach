import os
import sys
from docxtpl import DocxTemplate
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle 
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

# Dossier de destination absolu
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOSSIER_DEST = os.path.join(BASE_DIR, "cv_optimise_output")
os.makedirs(DOSSIER_DEST, exist_ok=True)

# --- HELPER DE FORMATAGE CONTACT ---
def format_contact_info(info):
    """
    Transforme un dictionnaire de contact ou une liste en chaîne propre.
    Ex: {'tel': '06..', 'ville': 'Paris'} -> "Paris | 06..."
    """
    if isinstance(info, dict):
        # On récupère toutes les valeurs non vides
        values = [str(v) for v in info.values() if v]
        return " | ".join(values)
    elif isinstance(info, list):
        return " | ".join([str(v) for v in info if v])
    return str(info)

# ==========================
# GESTION DOCX (Via Template)
# ==========================
def creer_docx_cv(data_cv, filename="cv_optimise.docx"):
    """
    Remplit le template 'template_2.docx' avec les données du CV.
    """
    template_path = os.path.join(BASE_DIR, "template_2.docx")
    
    if not os.path.exists(template_path):
        template_path = os.path.join(os.path.dirname(BASE_DIR), "template_2.docx")
        if not os.path.exists(template_path):
            print(f"ERREUR : Template introuvable à {template_path}")
            return None

    try:
        doc = DocxTemplate(template_path)
        context = {}
        
        # --- PRÉPARATION DES DONNÉES ---
        if isinstance(data_cv, dict):
            # 1. En-tête et Contact
            entete = data_cv.get('entete', {})
            context['entete'] = entete
            
            # CORRECTION ICI : Utilisation du formatteur
            raw_contact = entete.get('contact_info', '')
            context['contact'] = format_contact_info(raw_contact)

            # 2. Résumé
            context['resume'] = data_cv.get('resume', '')

            # 3. Compétences
            if 'competences_techniques' in data_cv:
                val = data_cv['competences_techniques']
                if isinstance(val, list): context['competences_techniques'] = ", ".join(val)
                else: context['competences_techniques'] = val
            
            # 4. Expériences
            exp_text = ""
            for exp in data_cv.get('experiences', []):
                exp_text += f"{exp.get('poste', '')} chez {exp.get('entreprise', '')} ({exp.get('dates', '')})\n"
                for t in exp.get('taches', []):
                    exp_text += f"- {t}\n"
                exp_text += "\n" 
            context['experiences_text'] = exp_text.strip()

            # 5. Formation
            form_text = ""
            for f in data_cv.get('formation', []):
                form_text += f"{f.get('diplome', '')}, {f.get('ecole', '')} ({f.get('dates', '')})\n"
                if f.get('details'):
                    form_text += f"• {f.get('details')}\n"
                form_text += "\n"
            context['formation_text'] = form_text.strip()

            # 6. Infos Supplémentaires
            infos_text = ""
            if data_cv.get('langues'): infos_text += f"Langues: {data_cv['langues']}\n"
            
            if data_cv.get('soft_skills'):
                val_soft = data_cv['soft_skills']
                if isinstance(val_soft, list): val_soft = ", ".join(val_soft)
                infos_text += f"Soft Skills: {val_soft}\n"

            if data_cv.get('certifications'): infos_text += f"Certifications: {data_cv['certifications']}\n"
            if data_cv.get('interets'): infos_text += f"Intérêts: {data_cv['interets']}\n"
            
            context['infos_supp_text'] = infos_text.strip()

        else:
            # Fallback
            context = {
                'entete': {'prenom_nom': 'CV GÉNÉRÉ'},
                'contact': '',
                'resume': str(data_cv),
                'experiences_text': '',
                'competences_techniques': '',
                'formation_text': '',
                'infos_supp_text': ''
            }

        doc.render(context)
        output_path = os.path.join(DOSSIER_DEST, filename)
        doc.save(output_path)
        return output_path

    except Exception as e:
        print(f"ERREUR DOCX : {e}")
        return None


# ==========================
# GESTION PDF (Mise en page structurée)
# ==========================
def creer_pdf_cv(data_cv, filename="cv_optimise.pdf"):
    pdf_path = os.path.join(DOSSIER_DEST, filename)
    
    try:
        doc = SimpleDocTemplate(
            pdf_path, 
            pagesize=A4,
            topMargin=0.5*inch, bottomMargin=0.5*inch, 
            leftMargin=0.5*inch, rightMargin=0.5*inch
        )
        
        # Styles
        styles = getSampleStyleSheet()
        style_nom = ParagraphStyle('Nom', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, alignment=TA_CENTER, textColor=colors.black, spaceAfter=2)
        style_contact = ParagraphStyle('Contact', parent=styles['Normal'], fontName='Helvetica', fontSize=9, alignment=TA_CENTER, textColor=colors.black, spaceAfter=15)
        style_section = ParagraphStyle('Section', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, textColor=colors.darkblue, spaceBefore=10, spaceAfter=5)
        
        # MODIFICATION ICI : Taille réduite à 10
        style_normal = ParagraphStyle('Corps', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=12, alignment=TA_JUSTIFY)
        style_bullet = ParagraphStyle('Bullet', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=12, leftIndent=15, bulletIndent=0)

        story = []

        if isinstance(data_cv, dict):
            # Header
            ent = data_cv.get('entete', {})
            nom = str(ent.get('prenom_nom', 'Prénom Nom')).upper()
            
            # Utilisation du formatteur
            raw_infos = ent.get('contact_info', 'Contact')
            infos = format_contact_info(raw_infos)
            
            story.append(Paragraph(nom, style_nom))
            story.append(Paragraph(infos, style_contact))
            story.append(Spacer(1, 0.2*cm))
            story.append(Paragraph("_" * 90, style_contact))
            story.append(Spacer(1, 0.3*cm))

            # Resume
            if data_cv.get('resume'):
                story.append(Paragraph("PROFIL", style_section))
                story.append(Paragraph(str(data_cv['resume']), style_normal))
                story.append(Spacer(1, 0.3*cm))

            # Compétences
            if 'competences_techniques' in data_cv:
                story.append(Paragraph("COMPÉTENCES", style_section))
                comps = data_cv['competences_techniques']
                if isinstance(comps, list): comps = ", ".join(comps)
                story.append(Paragraph(str(comps), style_normal))
                story.append(Spacer(1, 0.3*cm))

            # Expériences
            if data_cv.get('experiences'):
                story.append(Paragraph("EXPÉRIENCES PROFESSIONNELLES", style_section))
                for exp in data_cv['experiences']:
                    header_exp = f"<b>{exp.get('poste', 'Poste')}</b> - {exp.get('entreprise', 'Entreprise')}"
                    date_exp = f"<i>{exp.get('dates', '')}</i>"
                    story.append(Paragraph(f"{header_exp} <br/> {date_exp}", style_normal))
                    
                    for tache in exp.get('taches', []):
                        story.append(Paragraph(f"• {tache}", style_bullet))
                    story.append(Spacer(1, 0.2*cm))

            # Formation
            if data_cv.get('formation'):
                story.append(Paragraph("FORMATION", style_section))
                for form in data_cv['formation']:
                    ligne = f"<b>{form.get('dates', '')}</b> : {form.get('diplome', '')}, {form.get('ecole', '')}"
                    story.append(Paragraph(ligne, style_normal))
                    if form.get('details'):
                         story.append(Paragraph(f"<i>{form['details']}</i>", style_bullet))
                    story.append(Spacer(1, 0.1*cm))

            # Infos Complémentaires
            story.append(Paragraph("INFORMATIONS COMPLÉMENTAIRES", style_section))
            content_supp = []
            
            if data_cv.get('langues'): 
                content_supp.append(f"<b>Langues:</b> {data_cv['langues']}")
            
            if data_cv.get('soft_skills'):
                val_soft = data_cv['soft_skills']
                if isinstance(val_soft, list): val_soft = ", ".join(val_soft)
                content_supp.append(f"<b>Soft Skills:</b> {val_soft}")

            if data_cv.get('interets'): 
                content_supp.append(f"<b>Intérêts:</b> {data_cv['interets']}")
            
            for item in content_supp:
                story.append(Paragraph(item, style_normal))

        else:
            story.append(Paragraph("CV Optimisé", style_nom))
            story.append(Paragraph(str(data_cv), style_normal))

        doc.build(story)
        return pdf_path

    except Exception as e:
        print(f"ERREUR PDF: {e}")
        return None