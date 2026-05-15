import pytesseract
import pdfplumber
from pdf2image import convert_from_path
from PIL import Image
import os
from .preprocessing import preprocess_image # <--- IMPORT NOVO

# --- CONFIGURAÇÃO WINDOWS ---
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
POPPLER_PATH = r'C:\Program Files\poppler-25.12.0\Library\bin' 

def extract_text(file_path: str, content_type: str) -> str:
    try:
        if content_type == 'application/pdf':
            return _process_pdf(file_path)
        elif content_type.startswith('image/'):
            return _process_image(file_path)
        else:
            return "Formato não suportado."
    except Exception as e:
        print(f"Erro Crítico: {e}")
        return f"Erro: {str(e)}"

def _process_pdf(file_path):
    full_text = []
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            native_text = page.extract_text(layout=True)
            header = f"\n--- PÁGINA {i+1} ---\n"
            
            # Se tiver pouco texto, assumimos que é imagem e rodamos o OCR pesado
            if not native_text or len(native_text.strip()) < 50:
                print(f"Página {i+1} escaneada. Aplicando Visão Computacional...")
                ocr_text = _ocr_pdf_page(file_path, i)
                full_text.append(header + ocr_text)
            else:
                full_text.append(header + native_text)
    return "\n".join(full_text)

def _process_image(file_path):
    """OCR para arquivos de imagem pura."""
    raw_image = Image.open(file_path)
    # APLICA O FILTRO ANTES DE LER
    processed_image = preprocess_image(raw_image) 
    return _run_tesseract(processed_image)

def _ocr_pdf_page(file_path, page_number):
    """Converte PDF -> Imagem -> Filtro -> Texto"""
    images = convert_from_path(
        file_path, 
        first_page=page_number+1, 
        last_page=page_number+1, 
        dpi=400, # <--- AUMENTADO PARA 400 DPI (Mais definição)
        poppler_path=POPPLER_PATH
    )
    if images:
        # APLICA O FILTRO NA PÁGINA RENDERIZADA
        processed_image = preprocess_image(images[0])
        return _run_tesseract(processed_image)
    return "[Erro ao renderizar]"

def _run_tesseract(image):
    # Configuração mantida, mas agora recebe uma imagem limpa
    custom_config = r'--psm 3 -c preserve_interword_spaces=1'
    return pytesseract.image_to_string(image, lang='por', config=custom_config)