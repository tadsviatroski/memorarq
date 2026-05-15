import os
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi import HTTPException
from services.ocr_service import extract_text
from pydantic import BaseModel # Necessário para receber o texto JSON
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from fastapi.responses import StreamingResponse
import io
from services.bert_correction import bert_corrector

class TextUpdate(BaseModel):
    text: str

app = FastAPI()

origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "storage/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/files", StaticFiles(directory=UPLOAD_DIR), name="files")

# 1. FUNÇÃO AUXILIAR PARA SALVAR TEXTO
def save_text_file(filename: str, text: str):
    txt_path = os.path.join(UPLOAD_DIR, f"{filename}.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)

# 2. ATUALIZAR ROTA DE UPLOAD (Para salvar automático na primeira vez)
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_location = f"{UPLOAD_DIR}/{file.filename}"
    
    # Salva o binário
    content = await file.read()
    with open(file_location, "wb") as f:
        f.write(content)
        
    # Extrai o texto (OCR)
    extracted_text = extract_text(file_location, file.content_type)
    
    # SALVA O TEXTO EM DISCO
    save_text_file(file.filename, extracted_text)

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "url": f"http://127.0.0.1:8000/files/{file.filename}",
        "text": extracted_text
    }

# 3. NOVA ROTA: ABRIR ARQUIVO EXISTENTE (Recupera o texto salvo)
@app.get("/documents/{filename}/details")
async def get_document_details(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    txt_path = os.path.join(UPLOAD_DIR, f"{filename}.txt")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    
    # Tenta ler o texto salvo, se não existir, retorna vazio
    saved_text = ""
    if os.path.exists(txt_path):
        with open(txt_path, "r", encoding="utf-8") as f:
            saved_text = f.read()
            
    # Determina o Content-Type básico
    content_type = "application/octet-stream"
    if filename.endswith(".pdf"): content_type = "application/pdf"
    elif filename.lower().endswith((".png", ".jpg", ".jpeg")): content_type = "image/jpeg"

    return {
        "filename": filename,
        "content_type": content_type,
        "url": f"http://127.0.0.1:8000/files/{filename}",
        "text": saved_text
    }

# 4. NOVA ROTA: SALVAR EDIÇÃO MANUAL
@app.post("/documents/{filename}/save")
async def save_document_text(filename: str, update: TextUpdate):
    # Verifica se o arquivo original existe apenas por segurança
    if not os.path.exists(os.path.join(UPLOAD_DIR, filename)):
        raise HTTPException(status_code=404, detail="Documento original não encontrado")
        
    save_text_file(filename, update.text)
    return {"status": "success", "message": "Texto salvo com sucesso."}

# 5. NOVA ROTA: REFAZER OCR (Força a re-extração)
@app.post("/documents/{filename}/ocr")
async def re_run_ocr(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    
    # Redescobre o tipo
    content_type = "application/octet-stream"
    if filename.endswith(".pdf"): content_type = "application/pdf"
    elif filename.lower().endswith((".png", ".jpg", ".jpeg")): content_type = "image/jpeg"

    # Roda o OCR novamente
    new_text = extract_text(file_path, content_type)
    
    # Salva o novo resultado (sobrescreve o anterior)
    save_text_file(filename, new_text)
    
    return {"text": new_text}

# 6. ROTA PARA LISTAR DOCUMENTOS (Ordenados por data de modificação)
@app.get("/documents")
async def list_documents():
    """Retorna a lista de arquivos na pasta de uploads."""
    files = []
    if os.path.exists(UPLOAD_DIR):
        # Lista arquivos e ordena por data de modificação (mais recentes primeiro)
        for filename in os.listdir(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, filename)
            if os.path.isfile(file_path):
                stats = os.stat(file_path)
                files.append({
                    "name": filename,
                    "size": stats.st_size,
                    "created": stats.st_ctime
                })
        
        # Ordena: Mais novos no topo
        files.sort(key=lambda x: x['created'], reverse=True)
        
    return files

# 6. ROTA PARA LISTAR DOCUMENTOS (ATUALIZADA)
@app.get("/documents")
async def list_documents():
    """Retorna lista de arquivos, ESCONDENDO os .txt de sistema."""
    files = []
    if os.path.exists(UPLOAD_DIR):
        for filename in os.listdir(UPLOAD_DIR):
            # LÓGICA DE FILTRO: Pula arquivos que terminam em .txt
            # (Assumimos que .txt são apenas arquivos de suporte do sistema)
            if filename.endswith(".txt"):
                continue

            file_path = os.path.join(UPLOAD_DIR, filename)
            if os.path.isfile(file_path):
                stats = os.stat(file_path)
                files.append({
                    "name": filename,
                    "size": stats.st_size,
                    "created": stats.st_ctime
                })
        
        files.sort(key=lambda x: x['created'], reverse=True)
    return files

# 7. ROTA PARA DELETAR DOCUMENTO (ATUALIZADA)
@app.delete("/documents/{filename}")
async def delete_document(filename: str):
    """Remove o arquivo original E seu arquivo de texto associado."""
    file_path = os.path.join(UPLOAD_DIR, filename)
    txt_path = os.path.join(UPLOAD_DIR, f"{filename}.txt") # Caminho do arquivo sombra
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        
    try:
        # 1. Remove o arquivo principal
        os.remove(file_path)
        
        # 2. Remove o arquivo .txt se existir (Limpeza automática)
        if os.path.exists(txt_path):
            os.remove(txt_path)
            
        return {"status": "success", "message": f"{filename} deletado."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao deletar: {str(e)}")

# 8. NOVA ROTA: DOWNLOAD EM PDF
@app.post("/download/pdf")
async def generate_pdf(update: TextUpdate):
    """Gera um PDF on-the-fly com o texto enviado."""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    text_content = update.text
    
    # Configuração básica de fonte
    p.setFont("Helvetica", 12)
    
    # Lógica simples de quebra de linha
    y_position = height - 50
    margin = 50
    max_width = width - (2 * margin)
    
    lines = text_content.split('\n')
    
    for paragraph in lines:
        # Quebra parágrafos longos visualmente
        wrapped_lines = simpleSplit(paragraph, "Helvetica", 12, max_width)
        
        for line in wrapped_lines:
            if y_position < 50: # Nova página se acabar o espaço
                p.showPage()
                p.setFont("Helvetica", 12)
                y_position = height - 50
                
            p.drawString(margin, y_position, line)
            y_position -= 15 # Espaçamento entre linhas
            
        y_position -= 10 # Espaçamento extra entre parágrafos

    p.save()
    buffer.seek(0)
    
    # Retorna o arquivo como stream (download direto)
    return StreamingResponse(
        buffer, 
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=documento_exportado.pdf"}
    )

# 9. NOVA ROTA: CORREÇÃO COM IA (BERT)
@app.post("/documents/{filename}/ai-fix")
async def run_ai_correction(filename: str):
    """Lê o texto salvo, passa pelo BERTimbau e salva a versão corrigida."""
    # 1. Ler texto atual
    txt_path = os.path.join(UPLOAD_DIR, f"{filename}.txt")
    if not os.path.exists(txt_path):
         raise HTTPException(status_code=404, detail="Texto não encontrado. Rode o OCR primeiro.")
    
    with open(txt_path, "r", encoding="utf-8") as f:
        current_text = f.read()
        
    # 2. Processar com BERT
    # (Isso pode levar alguns segundos dependendo do tamanho)
    try:
        fixed_text = bert_corrector.correct_text(current_text)
    except Exception as e:
        print(f"Erro no BERT: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na IA: {str(e)}")
    
    # 3. Salvar
    save_text_file(filename, fixed_text)
    
    return {"text": fixed_text}