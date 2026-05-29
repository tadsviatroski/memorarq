import os
import json
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit

from services.ocr_service import extract_text
from services.bert_correction import bert_corrector

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 1. NOVA ESTRUTURA DE DIRETÓRIOS (FASE 1)
# ==========================================
UPLOAD_DIR = "storage/uploads"
ORIGINALS_DIR = os.path.join(UPLOAD_DIR, "originals")
EXTRACTED_DIR = os.path.join(UPLOAD_DIR, "extracted")
LOGS_DIR = os.path.join(UPLOAD_DIR, "logs")

# Cria as pastas isoladas se não existirem
os.makedirs(ORIGINALS_DIR, exist_ok=True)
os.makedirs(EXTRACTED_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Monta apenas a pasta de originais para preview no frontend
app.mount("/files", StaticFiles(directory=ORIGINALS_DIR), name="files")

class TextUpdate(BaseModel):
    text: str

# Função Auxiliar: Salva sempre na pasta de extraídos
def save_text_file(filename: str, text: str):
    txt_path = os.path.join(EXTRACTED_DIR, f"{filename}.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)

# ==========================================
# ROTAS DA API ATUALIZADAS (FASE 2)
# ==========================================

# 2. ROTA DE UPLOAD (Isolando originais e extraídos)
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    original_location = os.path.join(ORIGINALS_DIR, file.filename)
    
    content = await file.read()
    with open(original_location, "wb") as f:
        f.write(content)
        
    extracted_text = extract_text(original_location, file.content_type)
    save_text_file(file.filename, extracted_text)

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "url": f"http://127.0.0.1:8000/files/{file.filename}",
        "text": extracted_text
    }

# 3. ABRIR DOCUMENTO EXISTENTE (Lê as duas pastas separadamente)
@app.get("/documents/{filename}/details")
async def get_document_details(filename: str):
    original_path = os.path.join(ORIGINALS_DIR, filename)
    txt_path = os.path.join(EXTRACTED_DIR, f"{filename}.txt")
    
    if not os.path.exists(original_path):
        raise HTTPException(status_code=404, detail="Arquivo original não encontrado")
    
    saved_text = ""
    if os.path.exists(txt_path):
        with open(txt_path, "r", encoding="utf-8") as f:
            saved_text = f.read()
            
    content_type = "application/octet-stream"
    if filename.endswith(".pdf"): content_type = "application/pdf"
    elif filename.lower().endswith((".png", ".jpg", ".jpeg")): content_type = "image/jpeg"

    return {
        "filename": filename,
        "content_type": content_type,
        "url": f"http://127.0.0.1:8000/files/{filename}",
        "text": saved_text
    }

# 4. SALVAR EDIÇÃO MANUAL
@app.post("/documents/{filename}/save")
async def save_document_text(filename: str, update: TextUpdate):
    if not os.path.exists(os.path.join(ORIGINALS_DIR, filename)):
        raise HTTPException(status_code=404, detail="Documento original não encontrado")
        
    save_text_file(filename, update.text)
    return {"status": "success", "message": "Texto salvo com sucesso."}

# 5. REFAZER OCR
@app.post("/documents/{filename}/ocr")
async def re_run_ocr(filename: str):
    original_path = os.path.join(ORIGINALS_DIR, filename)
    
    if not os.path.exists(original_path):
        raise HTTPException(status_code=404, detail="Arquivo original não encontrado")
    
    content_type = "application/octet-stream"
    if filename.endswith(".pdf"): content_type = "application/pdf"
    elif filename.lower().endswith((".png", ".jpg", ".jpeg")): content_type = "image/jpeg"

    new_text = extract_text(original_path, content_type)
    save_text_file(filename, new_text)
    
    return {"text": new_text}

# 6. LISTAGEM DO GERENCIADOR (Totalmente blindada contra arquivos de sistema)
@app.get("/documents")
async def list_documents():
    """Retorna lista focada apenas na pasta de ORIGINAIS."""
    files = []
    if os.path.exists(ORIGINALS_DIR):
        for filename in os.listdir(ORIGINALS_DIR):
            file_path = os.path.join(ORIGINALS_DIR, filename)
            
            if os.path.isfile(file_path):
                stats = os.stat(file_path)
                
                # Verifica dinamicamente nos outros diretórios isolados
                has_txt = os.path.exists(os.path.join(EXTRACTED_DIR, f"{filename}.txt"))
                has_logs = os.path.exists(os.path.join(LOGS_DIR, f"{filename}_logs.json"))
                
                files.append({
                    "name": filename,
                    "size": stats.st_size,
                    "created": stats.st_ctime,
                    "has_txt": has_txt,
                    "has_logs": has_logs 
                })
        
        files.sort(key=lambda x: x['created'], reverse=True)
    return files

# 7. EXCLUSÃO EM CASCATA
@app.delete("/documents/{filename}")
async def delete_document(filename: str):
    original_path = os.path.join(ORIGINALS_DIR, filename)
    txt_path = os.path.join(EXTRACTED_DIR, f"{filename}.txt")
    logs_path = os.path.join(LOGS_DIR, f"{filename}_logs.json") 
    
    if not os.path.exists(original_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        
    try:
        os.remove(original_path)
        if os.path.exists(txt_path): os.remove(txt_path)
        if os.path.exists(logs_path): os.remove(logs_path) 
            
        return {"status": "success", "message": f"{filename} e seus dados derivados foram deletados."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao deletar: {str(e)}")

# 8. CORREÇÃO COM IA (Lê do extracted, salva no extracted, loga no logs)
@app.post("/documents/{filename}/ai-fix")
async def run_ai_correction(filename: str):
    txt_path = os.path.join(EXTRACTED_DIR, f"{filename}.txt")
    if not os.path.exists(txt_path):
         raise HTTPException(status_code=404, detail="Texto não encontrado. Rode o OCR primeiro.")
    
    with open(txt_path, "r", encoding="utf-8") as f:
        current_text = f.read()
        
    try:
        fixed_text, logs = bert_corrector.correct_text(current_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na IA: {str(e)}")
    
    save_text_file(filename, fixed_text)
    
    logs_path = os.path.join(LOGS_DIR, f"{filename}_logs.json")
    with open(logs_path, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=4)
    
    return {"text": fixed_text, "logs": logs}

# 9. BUSCAR LOGS
@app.get("/documents/{filename}/logs")
async def get_document_logs(filename: str):
    logs_path = os.path.join(LOGS_DIR, f"{filename}_logs.json")
    if not os.path.exists(logs_path):
        return []
    
    with open(logs_path, "r", encoding="utf-8") as f:
        return json.load(f)

# =================================================================
# A ROTA RAIZ (/) DEVE SER OBRIGATORIAMENTE A ÚLTIMA DO ARQUIVO
# =================================================================
app.mount("/", StaticFiles(directory="static", html=True), name="static")