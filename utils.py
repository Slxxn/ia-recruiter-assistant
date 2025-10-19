# utils.py
import fitz  # PyMuPDF

def extract_text_from_pdf(file_path):
    """Lit un fichier PDF et renvoie le texte complet."""
    text = ""
    with fitz.open(file_path) as pdf:
        for page in pdf:
            text += page.get_text()
    return text
